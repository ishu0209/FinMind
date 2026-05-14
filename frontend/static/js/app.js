// FinMind AI — Frontend JavaScript
// Communicates with FastAPI backend on port 8001

const API = 'https://ubiquitous-fishstick-xg6q6jjwwq7c695-8001.app.github.dev/api';
let chatHistory = [];

const CAT_COLORS = {
  Food:'#ff6b6b', Transport:'#ffd93d', Shopping:'#ff9f43',
  Entertainment:'#6c63ff', Healthcare:'#54a0ff', Bills:'#ffd93d',
  Investment:'#00e5a0', Other:'#a0a0c0', Income:'#00e5a0'
};
const CAT_ICONS = {
  Food:'🍕', Transport:'🚗', Shopping:'🛍️', Entertainment:'🎬',
  Healthcare:'🏥', Bills:'⚡', Investment:'📈', Other:'📦', Income:'💰'
};

// ── Navigation ────────────────────────────────────────────────────────────────
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    item.classList.add('active');
    const page = item.dataset.page;
    document.getElementById('page-' + page).classList.add('active');
    if (page === 'dashboard') loadDashboard();
    if (page === 'expenses') loadExpenses();
    if (page === 'goals') loadGoals();
    if (page === 'agent' && document.getElementById('messages').children.length === 0) initChat();
  });
});

// ── Dashboard ─────────────────────────────────────────────────────────────────
async function loadDashboard() {
  try {
    const [summaryRes, expRes, insRes] = await Promise.all([
      fetch(`${API}/summary`), fetch(`${API}/expenses`), fetch(`${API}/insights`)
    ]);
    const summary = await summaryRes.json();
    const { expenses } = await expRes.json();
    const { insights } = await insRes.json();

    renderStats(summary);
    renderCatBars(summary.by_category);
    renderInsights(insights);
    renderRecentTxns(expenses.slice(0, 8));
    document.getElementById('dash-updated').textContent =
      `${summary.transaction_count} transactions · Last updated ${new Date().toLocaleTimeString('en-IN')}`;
  } catch (e) {
    console.error('Dashboard load error:', e);
  }
}

function renderStats(s) {
  const grid = document.getElementById('stats-grid');
  grid.innerHTML = `
    <div class="stat-card">
      <div class="stat-label">Monthly Income</div>
      <div class="stat-value">₹${s.income.toLocaleString()}</div>
      <div class="stat-delta up">Fixed monthly salary</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Total Spent</div>
      <div class="stat-value" style="color:var(--danger)">₹${s.total_spent.toLocaleString()}</div>
      <div class="stat-delta down">${s.transaction_count} transactions</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Net Savings</div>
      <div class="stat-value" style="color:var(--accent)">₹${s.savings.toLocaleString()}</div>
      <div class="stat-delta up">${s.savings_rate}% savings rate</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">AI Alerts</div>
      <div class="stat-value" style="color:var(--warn)">${s.anomalies.length}</div>
      <div class="stat-delta neutral">${s.anomalies.length ? s.anomalies[0].category + ' is high' : 'All normal'}</div>
    </div>
  `;
}

function renderCatBars(byCategory) {
  const container = document.getElementById('cat-bars');
  const max = Math.max(...Object.values(byCategory));
  container.innerHTML = Object.entries(byCategory)
    .sort((a, b) => b[1] - a[1])
    .map(([cat, val]) => `
      <div class="bar-row">
        <div class="bar-label">${cat}</div>
        <div class="bar-track">
          <div class="bar-fill" style="background:${CAT_COLORS[cat]||'#888'}" data-w="${(val/max*100).toFixed(1)}"></div>
        </div>
        <div class="bar-val">₹${val.toLocaleString()}</div>
      </div>
    `).join('');
  setTimeout(() => {
    document.querySelectorAll('.bar-fill[data-w]').forEach(b => b.style.width = b.dataset.w + '%');
  }, 80);
}

function renderInsights(insights) {
  const container = document.getElementById('insights-list');
  if (!insights || !insights.length) {
    container.innerHTML = '<div class="loading-block">No insights available</div>';
    return;
  }
  container.innerHTML = insights.map(i => `
    <div class="insight">
      <div class="ins-icon">${i.icon}</div>
      <div>
        <div class="ins-title">${i.title}</div>
        <div class="ins-desc">${i.desc}</div>
      </div>
    </div>
  `).join('');
}

function renderRecentTxns(expenses) {
  const container = document.getElementById('recent-txns');
  container.innerHTML = expenses.map(e => `
    <div class="txn" id="txn-${e.id}">
      <div class="txn-icon" style="background:${(CAT_COLORS[e.category]||'#888')}22">
        ${CAT_ICONS[e.category] || '📦'}
      </div>
      <div class="txn-info">
        <div class="txn-name">${e.desc}</div>
        <div class="txn-cat">${e.category} · ${e.date}</div>
      </div>
      <div class="txn-amount down">-₹${e.amount.toLocaleString()}</div>
      <button class="txn-del" onclick="deleteExpense(${e.id})" title="Delete">✕</button>
    </div>
  `).join('');
}

// ── Expenses ─────────────────────────────────────────────────────────────────
async function loadExpenses() {
  try {
    const [expRes, summRes] = await Promise.all([
      fetch(`${API}/expenses`), fetch(`${API}/summary`)
    ]);
    const { expenses } = await expRes.json();
    const summary = await summRes.json();

    document.getElementById('exp-count-badge').textContent = `${expenses.length} entries`;
    document.getElementById('exp-date').valueAsDate = new Date();

    const container = document.getElementById('all-expenses');
    container.innerHTML = expenses.map(e => `
      <div class="txn" id="txn-${e.id}">
        <div class="txn-icon" style="background:${(CAT_COLORS[e.category]||'#888')}22">
          ${CAT_ICONS[e.category] || '📦'}
        </div>
        <div class="txn-info">
          <div class="txn-name">${e.desc}</div>
          <div class="txn-cat">${e.category} · ${e.date}</div>
        </div>
        <div class="txn-amount down">-₹${e.amount.toLocaleString()}</div>
        <button class="txn-del" onclick="deleteExpense(${e.id})" title="Delete">✕</button>
      </div>
    `).join('');

    const top = Object.entries(summary.by_category).sort((a,b) => b[1]-a[1])[0] || ['N/A', 0];
    document.getElementById('exp-summary').innerHTML = `
      <div class="summary-stat"><span class="key">Total transactions</span><span class="val">${summary.transaction_count}</span></div>
      <div class="summary-stat"><span class="key">Total spent</span><span class="val" style="color:var(--danger)">₹${summary.total_spent.toLocaleString()}</span></div>
      <div class="summary-stat"><span class="key">Monthly income</span><span class="val">₹${summary.income.toLocaleString()}</span></div>
      <div class="summary-stat"><span class="key">Net savings</span><span class="val" style="color:var(--accent)">₹${summary.savings.toLocaleString()}</span></div>
      <div class="summary-stat"><span class="key">Savings rate</span><span class="val" style="color:var(--accent)">${summary.savings_rate}%</span></div>
      <div class="summary-stat"><span class="key">Top category</span><span class="val">${top[0]} — ₹${top[1].toLocaleString()}</span></div>
      <div class="summary-stat"><span class="key">AI anomalies</span><span class="val" style="color:var(--warn)">${summary.anomalies.length} detected</span></div>
    `;
  } catch(e) {
    console.error('Expenses load error:', e);
  }
}

async function addExpense() {
  const desc = document.getElementById('exp-desc').value.trim();
  const amount = parseFloat(document.getElementById('exp-amount').value);
  const date = document.getElementById('exp-date').value;
  const category = document.getElementById('exp-cat').value;
  const resultEl = document.getElementById('add-result');

  if (!desc || !amount || !date) {
    resultEl.className = 'add-result error';
    resultEl.textContent = 'Please fill in description, amount, and date.';
    return;
  }

  const btn = document.getElementById('add-btn');
  btn.disabled = true; btn.textContent = 'Adding...';

  try {
    const res = await fetch(`${API}/expenses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ desc, amount, date, category })
    });
    const data = await res.json();
    resultEl.className = 'add-result success';
    resultEl.textContent = `✅ ${data.message}`;
    document.getElementById('exp-desc').value = '';
    document.getElementById('exp-amount').value = '';
    loadExpenses();
  } catch(e) {
    resultEl.className = 'add-result error';
    resultEl.textContent = '❌ Failed to add expense. Is the backend running?';
  }
  btn.disabled = false; btn.textContent = '+ Add Expense';
}

async function deleteExpense(id) {
  try {
    await fetch(`${API}/expenses/${id}`, { method: 'DELETE' });
    document.getElementById(`txn-${id}`)?.remove();
    loadExpenses();
  } catch(e) {
    console.error('Delete error:', e);
  }
}

// ── Goals ─────────────────────────────────────────────────────────────────────
async function loadGoals() {
  try {
    const res = await fetch(`${API}/goals`);
    const { goals } = await res.json();
    const container = document.getElementById('goals-list');
    container.innerHTML = goals.map(g => `
      <div class="goal-item">
        <div class="goal-header">
          <div class="goal-name">${g.icon} ${g.name}</div>
          <div class="goal-pct">${g.pct}%</div>
        </div>
        <div class="goal-track">
          <div class="goal-fill" data-w="${g.pct}"></div>
        </div>
        <div class="goal-sub">₹${g.saved.toLocaleString()} of ₹${g.target.toLocaleString()} · ~${g.months_left} months left</div>
      </div>
    `).join('');
    setTimeout(() => {
      document.querySelectorAll('.goal-fill[data-w]').forEach(f => f.style.width = f.dataset.w + '%');
    }, 80);
  } catch(e) {
    console.error('Goals load error:', e);
  }
}

async function addGoal() {
  const name = document.getElementById('goal-name').value.trim();
  const target = parseFloat(document.getElementById('goal-target').value);
  const saved = parseFloat(document.getElementById('goal-saved').value) || 0;
  const monthly = parseFloat(document.getElementById('goal-monthly').value);
  const icon = document.getElementById('goal-icon').value || '🎯';
  const resultEl = document.getElementById('goal-result');

  if (!name || !target || !monthly) {
    resultEl.className = 'add-result error';
    resultEl.textContent = 'Please fill name, target, and monthly contribution.';
    return;
  }
  try {
    const res = await fetch(`${API}/goals`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, target, saved, monthly, icon })
    });
    const data = await res.json();
    resultEl.className = 'add-result success';
    resultEl.textContent = `✅ Goal "${data.goal.name}" added!`;
    loadGoals();
  } catch(e) {
    resultEl.className = 'add-result error';
    resultEl.textContent = '❌ Failed. Is the backend running?';
  }
}

// ── AI Chat ───────────────────────────────────────────────────────────────────
function initChat() {
  addMsg('ai', `👋 Hello! I'm your **FinMind AI Agent**.\n\nI have full access to your financial data — your income, every expense, spending patterns, and savings goals.\n\nAsk me anything about your finances and I'll give you specific, personalized advice!`);
}

function addMsg(role, text) {
  const msgs = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'msg ' + (role === 'user' ? 'user' : '');
  const html = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
  div.innerHTML = `
    <div class="msg-av ${role === 'ai' ? 'ai' : ''}">${role === 'ai' ? '🤖' : '👤'}</div>
    <div class="bubble ${role}">${html}</div>
  `;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function showTyping() {
  const msgs = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'msg'; div.id = 'typing';
  div.innerHTML = `<div class="msg-av ai">🤖</div><div class="bubble ai"><div class="typing-dots"><span></span><span></span><span></span></div></div>`;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  document.getElementById('send-btn').disabled = true;

  addMsg('user', text);
  chatHistory.push({ role: 'user', content: text });
  showTyping();

  try {
    const res = await fetch(`${API}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, history: chatHistory.slice(-8) })
    });
    const data = await res.json();
    document.getElementById('typing')?.remove();
    addMsg('ai', data.reply);
    chatHistory.push({ role: 'assistant', content: data.reply });
  } catch(e) {
    document.getElementById('typing')?.remove();
    addMsg('ai', '⚠️ Could not reach the backend. Make sure the FastAPI server is running on port 8001.');
  }
  document.getElementById('send-btn').disabled = false;
  input.focus();
}

function sendChip(el) {
  document.getElementById('chat-input').value = el.textContent;
  sendMessage();
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

function clearChat() {
  chatHistory = [];
  document.getElementById('messages').innerHTML = '';
  initChat();
}

// ── Full Analysis ─────────────────────────────────────────────────────────────
async function runAnalysis() {
  const btn = document.getElementById('analyze-btn');
  btn.disabled = true; btn.textContent = '⏳ AI is analyzing your finances...';

  try {
    const res = await fetch(`${API}/analyze`, { method: 'POST' });
    const data = await res.json();

    const scoreColor = data.score >= 75 ? 'var(--accent)' : data.score >= 50 ? 'var(--warn)' : 'var(--danger)';
    const riskColor = data.risk_level === 'Low' ? 'var(--accent)' : data.risk_level === 'Medium' ? 'var(--warn)' : 'var(--danger)';

    document.getElementById('analysis-hero').innerHTML = `
      <div class="score-circle">
        <div class="score-num" style="color:${scoreColor}">${data.score}</div>
        <div class="score-label">/100</div>
      </div>
      <div>
        <div class="analysis-headline">${data.headline}</div>
        <div class="analysis-sub">Financial health: <strong style="color:${scoreColor}">${data.score_label}</strong></div>
        <div class="analysis-row">
          <span class="analysis-tag badge green">✅ ${data.score_label}</span>
          <span class="analysis-tag badge ${data.risk_level==='Low'?'green':data.risk_level==='Medium'?'':'red'}">
            Risk: ${data.risk_level}
          </span>
        </div>
      </div>
    `;
    document.getElementById('analysis-left').innerHTML = `
      <div class="card-title">📊 AI Findings</div>
      <div class="info-row"><span class="info-key">Top Insight</span><span class="info-val">${data.top_insight}</span></div>
      <div class="info-row"><span class="info-key">Savings Advice</span><span class="info-val" style="color:var(--accent)">${data.savings_advice}</span></div>
      <div class="info-row"><span class="info-key">Investment Advice</span><span class="info-val">${data.investment_advice}</span></div>
    `;
    document.getElementById('analysis-right').innerHTML = `
      <div class="card-title">🎯 Action Plan</div>
      <div class="info-row"><span class="info-key">Risk Level</span><span class="info-val" style="color:${riskColor}">${data.risk_level}</span></div>
      <div class="info-row"><span class="info-key">Next Best Action</span><span class="info-val" style="color:var(--accent)">${data.next_action}</span></div>
      <div class="info-row"><span class="info-key">Analyzed at</span><span class="info-val">${new Date().toLocaleTimeString('en-IN')}</span></div>
    `;
    document.getElementById('analysis-result').style.display = 'block';
  } catch(e) {
    alert('Analysis failed. Make sure the backend is running.');
  }
  btn.disabled = false; btn.textContent = '🔄 Run Again';
}

// ── Init ──────────────────────────────────────────────────────────────────────
loadDashboard();
