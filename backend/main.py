"""
FinMind AI — Personal Finance Agentic Backend
FastAPI + Groq API (llama-3.3-70b-versatile)
"""

from fastapi import FastAPI, HTTPException, Request  # type: ignore[import]
from fastapi.middleware.cors import CORSMiddleware    # type: ignore[import]
from fastapi.staticfiles import StaticFiles          # type: ignore[import]
from fastapi.responses import HTMLResponse           # type: ignore[import]
from pydantic import BaseModel                       # type: ignore[import]
from typing import Optional, List
from groq import Groq                                # type: ignore[import]
import json, os, re, time
from datetime import datetime
from dotenv import load_dotenv                       # type: ignore[import]

from logger import log, get_logger, log_requests     # ← our logger

load_dotenv()

# ── Child loggers per domain ──────────────────────────────────────────────────
log_groq    = get_logger("groq")
log_routes  = get_logger("routes")
log_db      = get_logger("db")

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="FinMind AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
app.middleware("http")(log_requests)   # ← request/response logger

log.info("FinMind AI backend starting up", extra={"version": "1.0.0"})

# ── Groq client ───────────────────────────────────────────────────────────────
def get_groq():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        log_groq.error("GROQ_API_KEY is not set in .env")
        raise HTTPException(500, "GROQ_API_KEY not set in .env")
    return Groq(api_key=key)

GROQ_MODEL = "llama-3.3-70b-versatile"

def groq_chat(messages: list, system: str = "", max_tokens: int = 800) -> str:
    client = get_groq()
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages)

    last_user_msg = messages[-1]["content"][:80] if messages else ""
    log_groq.debug(
        f"Calling Groq",
        extra={
            "model":      GROQ_MODEL,
            "max_tokens": max_tokens,
            "turns":      len(messages),
            "preview":    last_user_msg,
        }
    )

    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=msgs,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        duration = round((time.perf_counter() - t0) * 1000, 1)
        reply = resp.choices[0].message.content
        log_groq.info(
            f"Groq response received",
            extra={
                "duration_ms":    duration,
                "output_chars":   len(reply),
                "finish_reason":  resp.choices[0].finish_reason,
            }
        )
        return reply
    except Exception as exc:
        duration = round((time.perf_counter() - t0) * 1000, 1)
        log_groq.error(
            f"Groq call failed: {exc}",
            exc_info=True,
            extra={"duration_ms": duration, "model": GROQ_MODEL}
        )
        raise

# ── In-memory DB ──────────────────────────────────────────────────────────────
expenses_db: List[dict] = [
    {"id": 1,  "desc": "Swiggy - Dinner",       "category": "Food",          "amount": 450,   "date": "2025-05-10"},
    {"id": 2,  "desc": "Ola Cab - Office",       "category": "Transport",     "amount": 180,   "date": "2025-05-10"},
    {"id": 3,  "desc": "Netflix Subscription",   "category": "Entertainment", "amount": 649,   "date": "2025-05-09"},
    {"id": 4,  "desc": "Big Basket - Groceries", "category": "Food",          "amount": 2300,  "date": "2025-05-08"},
    {"id": 5,  "desc": "Electricity Bill",       "category": "Bills",         "amount": 1850,  "date": "2025-05-07"},
    {"id": 6,  "desc": "Zerodha SIP",            "category": "Investment",    "amount": 10000, "date": "2025-05-06"},
    {"id": 7,  "desc": "Amazon Shopping",        "category": "Shopping",      "amount": 3200,  "date": "2025-05-05"},
    {"id": 8,  "desc": "Zomato - Lunch",         "category": "Food",          "amount": 380,   "date": "2025-05-05"},
    {"id": 9,  "desc": "Gym Membership",         "category": "Healthcare",    "amount": 2500,  "date": "2025-05-04"},
    {"id": 10, "desc": "IRCTC Train Ticket",     "category": "Transport",     "amount": 1200,  "date": "2025-05-03"},
    {"id": 11, "desc": "Myntra Clothes",         "category": "Shopping",      "amount": 4500,  "date": "2025-05-02"},
]

goals_db: List[dict] = [
    {"id": 1, "name": "Emergency Fund",   "target": 200000, "saved": 85000,  "monthly": 10000, "icon": "🛡️"},
    {"id": 2, "name": "Europe Trip 2026", "target": 150000, "saved": 42000,  "monthly": 8000,  "icon": "✈️"},
    {"id": 3, "name": "New Laptop",       "target": 80000,  "saved": 65000,  "monthly": 5000,  "icon": "💻"},
    {"id": 4, "name": "Retirement SIP",   "target": 5000000,"saved": 320000, "monthly": 10000, "icon": "🌴"},
]

MONTHLY_INCOME = 85000
_next_id = 12

log_db.info(
    "In-memory DB initialized",
    extra={"expenses": len(expenses_db), "goals": len(goals_db), "income": MONTHLY_INCOME}
)

# ── Category auto-detect ──────────────────────────────────────────────────────
KEYWORDS = {
    "Food":          ["swiggy","zomato","restaurant","food","pizza","cafe","lunch","dinner","grocery","bigbasket","zepto","blinkit"],
    "Transport":     ["ola","uber","cab","train","bus","irctc","fuel","petrol","rapido","metro"],
    "Shopping":      ["amazon","flipkart","myntra","shopping","clothes","shoes","meesho","nykaa"],
    "Entertainment": ["netflix","prime","hotstar","movie","game","spotify","theatre","concert"],
    "Healthcare":    ["doctor","hospital","medicine","gym","pharmacy","health","apollo","medplus"],
    "Bills":         ["electricity","bill","recharge","internet","gas","water","maintenance","rent"],
    "Investment":    ["sip","zerodha","groww","mutual","stock","investment","fd","ppf","nps","elss"],
}

def auto_categorize(desc: str) -> str:
    d = desc.lower()
    for cat, kw in KEYWORDS.items():
        if any(k in d for k in kw):
            return cat
    log_db.debug(f"No keyword match for '{desc}' → defaulting to Other")
    return "Other"

# ── Pydantic models ───────────────────────────────────────────────────────────
class ExpenseIn(BaseModel):
    desc: str
    amount: float
    date: str
    category: Optional[str] = "auto"

class GoalIn(BaseModel):
    name: str
    target: float
    saved: float = 0
    monthly: float
    icon: str = "🎯"

class ChatIn(BaseModel):
    message: str
    history: Optional[List[dict]] = []

# ── Financial context builder ─────────────────────────────────────────────────
def financial_context() -> str:
    spent = sum(e["amount"] for e in expenses_db)
    by_cat: dict = {}
    for e in expenses_db:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + e["amount"]
    savings = MONTHLY_INCOME - spent
    rate = round(savings / MONTHLY_INCOME * 100, 1)
    cats = "\n".join(f"  {k}: ₹{v:,}" for k, v in sorted(by_cat.items(), key=lambda x: -x[1]))
    gls  = "\n".join(
        f"  {g['icon']} {g['name']}: ₹{g['saved']:,}/₹{g['target']:,} ({round(g['saved']/g['target']*100)}%)"
        for g in goals_db
    )
    return f"""USER FINANCIAL DATA (live):
Income : ₹{MONTHLY_INCOME:,}/month
Spent  : ₹{spent:,}  |  Saved: ₹{savings:,}  |  Rate: {rate}%
Transactions: {len(expenses_db)}

Spending breakdown:
{cats}

Goals:
{gls}"""

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    log_routes.debug("Health check hit")
    return {"status": "FinMind AI running", "model": GROQ_MODEL}


# ── Expenses ──────────────────────────────────────────────────────────────────
@app.get("/api/expenses")
def get_expenses():
    log_routes.debug("Fetching all expenses", extra={"count": len(expenses_db)})
    return {"expenses": expenses_db, "total": len(expenses_db)}


@app.post("/api/expenses")
def add_expense(body: ExpenseIn):
    global _next_id
    cat = (
        body.category
        if body.category and body.category != "auto"
        else auto_categorize(body.desc)
    )
    exp = {
        "id":       _next_id,
        "desc":     body.desc,
        "category": cat,
        "amount":   body.amount,
        "date":     body.date,
    }
    expenses_db.insert(0, exp)
    _next_id += 1
    log_db.info(
        f"Expense added: '{body.desc}'",
        extra={"id": exp["id"], "amount": body.amount, "category": cat, "date": body.date}
    )
    return {"expense": exp, "ai_category": cat, "message": f"Added! AI categorized as: {cat}"}


@app.delete("/api/expenses/{eid}")
def del_expense(eid: int):
    global expenses_db
    before = len(expenses_db)
    expenses_db = [e for e in expenses_db if e["id"] != eid]
    if len(expenses_db) == before:
        log_routes.warning(f"Delete requested for non-existent expense", extra={"eid": eid})
        raise HTTPException(404, "Not found")
    log_db.info(f"Expense deleted", extra={"eid": eid})
    return {"message": "Deleted"}


# ── Summary ───────────────────────────────────────────────────────────────────
@app.get("/api/summary")
def summary():
    spent = sum(e["amount"] for e in expenses_db)
    by_cat: dict = {}
    for e in expenses_db:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + e["amount"]
    savings = MONTHLY_INCOME - spent
    anomalies = [
        {"category": k, "amount": v, "pct": round(v / MONTHLY_INCOME * 100, 1)}
        for k, v in by_cat.items()
        if v > MONTHLY_INCOME * 0.15
    ]
    if anomalies:
        log_routes.warning(
            f"{len(anomalies)} spending anomaly/anomalies detected",
            extra={"anomalies": [a["category"] for a in anomalies]}
        )
    else:
        log_routes.debug("Summary computed, no anomalies")
    return {
        "income":            MONTHLY_INCOME,
        "total_spent":       spent,
        "savings":           savings,
        "savings_rate":      round(savings / MONTHLY_INCOME * 100, 1),
        "by_category":       by_cat,
        "transaction_count": len(expenses_db),
        "anomalies":         anomalies,
    }


# ── Goals ─────────────────────────────────────────────────────────────────────
@app.get("/api/goals")
def get_goals():
    log_routes.debug("Fetching goals", extra={"count": len(goals_db)})
    return {"goals": [{
        **g,
        "pct":        round(g["saved"] / g["target"] * 100, 1),
        "months_left": round((g["target"] - g["saved"]) / g["monthly"]),
    } for g in goals_db]}


@app.post("/api/goals")
def add_goal(body: GoalIn):
    g = {"id": len(goals_db) + 1, **body.dict()}
    goals_db.append(g)
    log_db.info(
        f"Goal added: '{body.name}'",
        extra={"id": g["id"], "target": body.target, "monthly": body.monthly}
    )
    return {"goal": g}


# ── AI Insights ───────────────────────────────────────────────────────────────
@app.get("/api/insights")
def get_insights():
    log_routes.info("Generating AI insights via Groq")
    ctx = financial_context()
    prompt = f"""{ctx}

Generate exactly 3 financial insights as a JSON array.
Each object must have: "icon" (emoji), "title" (max 8 words), "desc" (2 sentences with numbers), "type" ("warning"|"success"|"info").
Return ONLY a valid JSON array — no markdown fences, no explanation."""
    try:
        raw = groq_chat([{"role": "user", "content": prompt}], max_tokens=500)
        raw = re.sub(r"```json|```", "", raw).strip()
        m = re.search(r'\[.*\]', raw, re.DOTALL)
        insights = json.loads(m.group() if m else raw)
        log_routes.info(f"Insights generated successfully", extra={"count": len(insights)})
        return {"insights": insights}
    except Exception as e:
        log_routes.error(f"Insights generation failed, using fallback", exc_info=True)
        s = summary()
        by_cat = s["by_category"]
        top = max(by_cat, key=by_cat.get) if by_cat else "Food"
        return {"insights": [
            {"icon": "⚠️", "title": f"{top} spending needs attention",
             "desc": f"You spent ₹{by_cat.get(top, 0):,} on {top} — your biggest category. Cutting it by 20% saves ₹{int(by_cat.get(top, 0) * 0.2):,}/month.", "type": "warning"},
            {"icon": "🎉", "title": "Savings rate is above average",
             "desc": f"You are saving {s['savings_rate']}% of income (₹{s['savings']:,}). The national average is around 12% — excellent discipline!", "type": "success"},
            {"icon": "💡", "title": "Invest for tax savings under 80C",
             "desc": "You can save up to ₹46,800 in taxes by maxing your ₹1.5L 80C limit via ELSS mutual funds or PPF this financial year.", "type": "info"},
        ]}


# ── AI Chat ───────────────────────────────────────────────────────────────────
@app.post("/api/chat")
def chat(body: ChatIn):
    history_len = len(body.history or [])
    log_routes.info(
        "Chat message received",
        extra={"message_preview": body.message[:60], "history_turns": history_len}
    )
    system = f"""You are FinMind, an expert personal finance advisor for an Indian user.
You have real-time access to their financial data shown below. Be specific, practical, and use Indian context (₹, SIP, 80C, Nifty, Zerodha, UPI).
Keep responses concise, use bullet points for lists.

{financial_context()}"""
    messages = list(body.history or [])[-8:]
    messages.append({"role": "user", "content": body.message})
    try:
        reply = groq_chat(messages, system=system, max_tokens=700)
        log_routes.info("Chat reply sent", extra={"reply_chars": len(reply)})
        return {"reply": reply}
    except Exception as e:
        log_routes.error(f"Chat failed: {e}", exc_info=True)
        raise HTTPException(500, str(e))


# ── Full Analysis ─────────────────────────────────────────────────────────────
@app.post("/api/analyze")
def analyze():
    log_routes.info("Full financial analysis requested")
    ctx = financial_context()
    prompt = f"""{ctx}

Return a JSON object (no markdown) with EXACTLY these keys:
{{
  "score": <integer 0-100>,
  "score_label": "<Poor|Fair|Good|Excellent>",
  "headline": "<one sentence summary>",
  "top_insight": "<most important finding with a number>",
  "savings_advice": "<actionable savings tip with rupee amount>",
  "investment_advice": "<specific Indian investment recommendation>",
  "risk_level": "<Low|Medium|High>",
  "next_action": "<single most important action to take today>"
}}
Return ONLY the JSON object."""
    try:
        raw = groq_chat([{"role": "user", "content": prompt}], max_tokens=400)
        raw = re.sub(r"```json|```", "", raw).strip()
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        result = json.loads(m.group() if m else raw)
        log_routes.info(
            "Analysis completed",
            extra={"score": result.get("score"), "risk": result.get("risk_level")}
        )
        return result
    except Exception as e:
        log_routes.error("Analysis failed, using fallback", exc_info=True)
        s = summary()
        return {
            "score": 74, "score_label": "Good",
            "headline": f"You saved ₹{s['savings']:,} ({s['savings_rate']}%) this month — well above average.",
            "top_insight": f"Food is your largest discretionary expense at ₹{s['by_category'].get('Food', 0):,}.",
            "savings_advice": "Order food delivery max 3x/week to save ~₹3,000/month.",
            "investment_advice": "Max out 80C (₹1.5L/year) via ELSS funds on Zerodha Coin for tax + growth.",
            "risk_level": "Low",
            "next_action": "Set a daily UPI spending alert of ₹1,500 to control impulse buys.",
        }


# ── Startup / Shutdown events ─────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    log.info("FinMind API is ready", extra={"host": "0.0.0.0", "port": 8001})

@app.on_event("shutdown")
async def on_shutdown():
    log.info("FinMind API shutting down")


if __name__ == "__main__":
    import uvicorn  # type: ignore[import]
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)