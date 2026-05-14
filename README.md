# 🚀 Agentic AI Finance Projects — Groq Edition
### Uses FREE Groq API (LLaMA 3.3 70B) — No paid key needed!

---

## 📦 Two Projects Included

| Project | Level | Port (Backend) | Port (Frontend) |
|---------|-------|----------------|-----------------|
| FinMind AI — Personal Finance Agent | Beginner | 8001 | 3001 |
| StockSage AI — Stock Research Agent | Intermediate | 8002 | 3002 |

---

## 🔑 Get Your FREE Groq API Key (2 minutes)

1. Go to → **https://console.groq.com**
2. Sign up (free, no credit card)
3. Click **"API Keys"** → **"Create API Key"**
4. Copy the key (starts with `gsk_...`)
5. Paste it into **both** `.env` files

---

## ⚡ Why Groq?

| Feature | Groq (Free) | OpenAI / Anthropic |
|---------|-------------|--------------------|
| Cost | **FREE** | Paid ($) |
| Speed | **Ultra-fast** (500+ tokens/sec) | Slower |
| Model | LLaMA 3.3 70B (Meta, open-source) | GPT-4 / Claude |
| Rate limits | 14,400 requests/day (free tier) | Pay per token |

---

## 🗂 Project Structure

```
Project1_FinMind_AI/
├── backend/
│   ├── main.py              ← FastAPI + Groq (all AI logic)
│   ├── requirements.txt
│   └── .env                 ← 👈 Add GROQ_API_KEY here
├── frontend/
│   ├── server.py            ← Static file server
│   ├── templates/index.html ← UI
│   └── static/
│       ├── css/style.css
│       └── js/app.js        ← Calls your FastAPI backend
└── README.md

Project2_StockSage_AI/
├── backend/
│   ├── main.py              ← FastAPI + Groq (8-step pipeline)
│   ├── requirements.txt
│   └── .env                 ← 👈 Add GROQ_API_KEY here
├── frontend/
│   ├── server.py
│   ├── templates/index.html
│   └── static/
│       ├── css/style.css
│       └── js/app.js
└── README.md
```

---

## 🚀 Run Project 1 — FinMind AI

```bash
# Step 1: Add API key
echo "GROQ_API_KEY=gsk_your_key_here" > Project1_FinMind_AI/backend/.env

# Step 2: Install
cd Project1_FinMind_AI/backend
pip install -r requirements.txt

# Step 3: Start backend (Terminal 1)
python main.py
# ✅ Running at http://localhost:8001
# 📄 API docs at http://localhost:8001/docs

# Step 4: Start frontend (Terminal 2)
cd Project1_FinMind_AI/frontend
python server.py
# ✅ Running at http://localhost:3001
```

Open **http://localhost:3001** 🎉

---

## 🚀 Run Project 2 — StockSage AI

```bash
# Step 1: Add API key
echo "GROQ_API_KEY=gsk_your_key_here" > Project2_StockSage_AI/backend/.env

# Step 2: Install
cd Project2_StockSage_AI/backend
pip install -r requirements.txt

# Step 3: Start backend (Terminal 1)
python main.py
# ✅ Running at http://localhost:8002

# Step 4: Start frontend (Terminal 2)
cd Project2_StockSage_AI/frontend
python server.py
# ✅ Running at http://localhost:3002
```

Open **http://localhost:3002** 🎉

---

## 🌐 API Endpoints

### FinMind AI (port 8001)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/expenses` | All expenses |
| POST | `/api/expenses` | Add expense (AI auto-categorizes) |
| DELETE | `/api/expenses/{id}` | Delete expense |
| GET | `/api/summary` | Financial summary + anomalies |
| GET | `/api/goals` | Savings goals with progress |
| POST | `/api/goals` | Add new goal |
| GET | `/api/insights` | AI-generated insights (Groq) |
| POST | `/api/chat` | AI finance chat (Groq) |
| POST | `/api/analyze` | Full financial analysis (Groq) |

### StockSage AI (port 8002)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stocks` | List all supported stocks |
| POST | `/api/research` | **Full 8-step AI pipeline** |
| POST | `/api/chat` | Context-aware follow-up (Groq) |
| GET | `/api/market-overview` | NSE/BSE index data |

**Interactive API docs (Swagger):**
- http://localhost:8001/docs
- http://localhost:8002/docs

---

## 🤖 AI Model Used

**Groq — LLaMA 3.3 70B Versatile**
- Model string: `llama-3.3-70b-versatile`
- Developed by Meta, hosted on Groq's custom LPU hardware
- ~500 tokens/second generation speed
- Excellent at reasoning, analysis, and structured JSON output
- Free tier: 14,400 requests/day, 6,000 tokens/minute

---

## 💼 Resume Description

**Project 1 — FinMind AI:**
> Built a full-stack Agentic AI personal finance system (FastAPI + Groq LLaMA 3.3 70B + Vanilla JS). The agent auto-categorizes expenses, detects spending anomalies, generates proactive financial insights, and provides a real-time conversational AI financial advisor with complete user financial context.

**Project 2 — StockSage AI:**
> Architected a production-grade Agentic AI stock research platform (FastAPI + Groq LLaMA + Chart.js). The system executes an autonomous 8-step research pipeline per stock: data collection → fundamental scoring → technical analysis → risk modeling → peer comparison → AI synthesis. Features live agent execution log, BUY/HOLD/SELL signals, and context-aware follow-up chat.

**Tech Stack:** Python, FastAPI, Groq API, LLaMA 3.3 70B, HTML5, CSS3, JavaScript, Chart.js, REST APIs

---

## ❓ Troubleshooting

**"GROQ_API_KEY not set"** → Check your `.env` file is in the `backend/` folder with `GROQ_API_KEY=gsk_...`

**"Connection refused"** → Make sure backend is running before opening the browser

**Groq rate limit hit** → Free tier allows 30 req/min. Wait 60s and retry.

**Port already in use** → Change port in `main.py`: `uvicorn.run("main:app", port=8003, ...)`
