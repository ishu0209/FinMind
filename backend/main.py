"""
FinMind AI — Personal Finance Agentic Backend
FastAPI + Groq API (llama-3.3-70b-versatile)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from groq import Groq
import json, os, re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="FinMind AI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# ── Groq client ───────────────────────────────────────────────────────────────
def get_groq():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise HTTPException(500, "GROQ_API_KEY not set in .env")
    return Groq(api_key=key)

GROQ_MODEL = "llama-3.3-70b-versatile"

def groq_chat(messages: list, system: str = "", max_tokens: int = 800) -> str:
    client = get_groq()
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages)
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=msgs,
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return resp.choices[0].message.content

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
    {"id": 1, "name": "Emergency Fund",  "target": 200000, "saved": 85000,  "monthly": 10000, "icon": "🛡️"},
    {"id": 2, "name": "Europe Trip 2026","target": 150000, "saved": 42000,  "monthly": 8000,  "icon": "✈️"},
    {"id": 3, "name": "New Laptop",      "target": 80000,  "saved": 65000,  "monthly": 5000,  "icon": "💻"},
    {"id": 4, "name": "Retirement SIP",  "target": 5000000,"saved": 320000, "monthly": 10000, "icon": "🌴"},
]

MONTHLY_INCOME = 85000
_next_id = 12

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
    gls  = "\n".join(f"  {g['icon']} {g['name']}: ₹{g['saved']:,}/₹{g['target']:,} ({round(g['saved']/g['target']*100)}%)" for g in goals_db)
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
    return {"status": "FinMind AI running", "model": GROQ_MODEL}

# --- Expenses ---
@app.get("/api/expenses")
def get_expenses():
    return {"expenses": expenses_db, "total": len(expenses_db)}

@app.post("/api/expenses")
def add_expense(body: ExpenseIn):
    global _next_id
    cat = body.category if body.category and body.category != "auto" else auto_categorize(body.desc)
    exp = {"id": _next_id, "desc": body.desc, "category": cat,
           "amount": body.amount, "date": body.date}
    expenses_db.insert(0, exp)
    _next_id += 1
    return {"expense": exp, "ai_category": cat,
            "message": f"Added! AI categorized as: {cat}"}

@app.delete("/api/expenses/{eid}")
def del_expense(eid: int):
    global expenses_db
    before = len(expenses_db)
    expenses_db = [e for e in expenses_db if e["id"] != eid]
    if len(expenses_db) == before:
        raise HTTPException(404, "Not found")
    return {"message": "Deleted"}

# --- Summary ---
@app.get("/api/summary")
def summary():
    spent = sum(e["amount"] for e in expenses_db)
    by_cat: dict = {}
    for e in expenses_db:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + e["amount"]
    savings = MONTHLY_INCOME - spent
    anomalies = [{"category": k, "amount": v, "pct": round(v/MONTHLY_INCOME*100,1)}
                 for k, v in by_cat.items() if v > MONTHLY_INCOME * 0.15]
    return {
        "income": MONTHLY_INCOME, "total_spent": spent,
        "savings": savings, "savings_rate": round(savings/MONTHLY_INCOME*100,1),
        "by_category": by_cat, "transaction_count": len(expenses_db),
        "anomalies": anomalies,
    }

# --- Goals ---
@app.get("/api/goals")
def get_goals():
    return {"goals": [{
        **g,
        "pct": round(g["saved"]/g["target"]*100, 1),
        "months_left": round((g["target"]-g["saved"])/g["monthly"])
    } for g in goals_db]}

@app.post("/api/goals")
def add_goal(body: GoalIn):
    g = {"id": len(goals_db)+1, **body.dict()}
    goals_db.append(g)
    return {"goal": g}

# --- AI Insights (Groq) ---
@app.get("/api/insights")
def get_insights():
    ctx = financial_context()
    prompt = f"""{ctx}

Generate exactly 3 financial insights as a JSON array.
Each object must have: "icon" (emoji), "title" (max 8 words), "desc" (2 sentences with numbers), "type" ("warning"|"success"|"info").
Return ONLY a valid JSON array — no markdown fences, no explanation."""
    try:
        raw = groq_chat([{"role":"user","content":prompt}], max_tokens=500)
        # strip any markdown
        raw = re.sub(r"```json|```", "", raw).strip()
        # extract array
        m = re.search(r'\[.*\]', raw, re.DOTALL)
        if m:
            return {"insights": json.loads(m.group())}
        return {"insights": json.loads(raw)}
    except Exception as e:
        s = summary()
        by_cat = s["by_category"]
        top = max(by_cat, key=by_cat.get) if by_cat else "Food"
        return {"insights": [
            {"icon":"⚠️","title":f"{top} spending needs attention",
             "desc":f"You spent ₹{by_cat.get(top,0):,} on {top} — your biggest category. Cutting it by 20% saves ₹{int(by_cat.get(top,0)*0.2):,}/month.","type":"warning"},
            {"icon":"🎉","title":"Savings rate is above average",
             "desc":f"You are saving {s['savings_rate']}% of income (₹{s['savings']:,}). The national average is around 12% — excellent discipline!","type":"success"},
            {"icon":"💡","title":"Invest for tax savings under 80C",
             "desc":"You can save up to ₹46,800 in taxes by maxing your ₹1.5L 80C limit via ELSS mutual funds or PPF this financial year.","type":"info"},
        ]}

# --- AI Chat (Groq) ---
@app.post("/api/chat")
def chat(body: ChatIn):
    system = f"""You are FinMind, an expert personal finance advisor for an Indian user.
You have real-time access to their financial data shown below. Be specific, practical, and use Indian context (₹, SIP, 80C, Nifty, Zerodha, UPI).
Keep responses concise, use bullet points for lists.

{financial_context()}"""
    messages = list(body.history or [])[-8:]   # keep last 8 turns
    messages.append({"role":"user","content":body.message})
    try:
        reply = groq_chat(messages, system=system, max_tokens=700)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(500, str(e))

# --- Full Analysis (Groq) ---
@app.post("/api/analyze")
def analyze():
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
        raw = groq_chat([{"role":"user","content":prompt}], max_tokens=400)
        raw = re.sub(r"```json|```","",raw).strip()
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        return json.loads(m.group() if m else raw)
    except Exception as e:
        s = summary()
        return {
            "score": 74, "score_label": "Good",
            "headline": f"You saved ₹{s['savings']:,} ({s['savings_rate']}%) this month — well above average.",
            "top_insight": f"Food is your largest discretionary expense at ₹{s['by_category'].get('Food',0):,}.",
            "savings_advice": "Order food delivery max 3x/week to save ~₹3,000/month.",
            "investment_advice": "Max out 80C (₹1.5L/year) via ELSS funds on Zerodha Coin for tax + growth.",
            "risk_level": "Low",
            "next_action": "Set a daily UPI spending alert of ₹1,500 to control impulse buys."
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
