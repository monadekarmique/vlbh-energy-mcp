/* Sprint Dashboard — VLBH Energy MCP */

const API_BASE = '';

const DEFAULT_SPRINT = {
  name: 'Sprint 1 — Foundation',
  goal: 'Ship the VLBH Energy MCP backend with full push/pull sync for all 5 modules (SLM, SLA, Session, Lead, Tore) and establish CI/CD pipeline.',
  startDate: '2026-04-08',
  endDate: '2026-04-22',
  team: [
    { name: 'Patrick', role: 'Lead / Shaman', availableDays: 8, totalDays: 10, allocation: 16, notes: 'Architecture + reviews' },
    { name: 'Claude', role: 'AI Engineer', availableDays: 10, totalDays: 10, allocation: 40, notes: 'Implementation' },
  ],
  backlog: [
    { id: 1, priority: 'P0', title: 'Backend API — all 5 modules push/pull operational', estimate: 8, owner: 'Claude', status: 'done', deps: 'None' },
    { id: 2, priority: 'P0', title: 'Make.com datastore integration (svlbh-v2)', estimate: 5, owner: 'Claude', status: 'done', deps: 'None' },
    { id: 3, priority: 'P0', title: 'GitHub Actions CI — Swift + Python', estimate: 5, owner: 'Claude', status: 'done', deps: 'None' },
    { id: 4, priority: 'P0', title: 'VLBHEnergyKit Swift Package + tests', estimate: 8, owner: 'Claude', status: 'done', deps: 'None' },
    { id: 5, priority: 'P0', title: 'Render.com auto-deploy from main', estimate: 3, owner: 'Claude', status: 'done', deps: 'None' },
    { id: 6, priority: 'P1', title: 'Xcode Cloud CI scripts', estimate: 3, owner: 'Claude', status: 'done', deps: '#4' },
    { id: 7, priority: 'P1', title: 'iOS integration patch for SVLBH Panel', estimate: 5, owner: 'Claude', status: 'done', deps: '#4' },
    { id: 8, priority: 'P1', title: 'Sprint dashboard for project tracking', estimate: 5, owner: 'Claude', status: 'wip', deps: 'None' },
    { id: 9, priority: 'P1', title: 'Architecture documentation (Mermaid)', estimate: 2, owner: 'Claude', status: 'done', deps: 'None' },
    { id: 10, priority: 'P2', title: 'Render deploy CLI tool', estimate: 3, owner: 'Claude', status: 'done', deps: '#5' },
    { id: 11, priority: 'P2', title: 'Auth token validation hardening', estimate: 2, owner: 'Claude', status: 'todo', deps: 'None' },
    { id: 12, priority: 'P2', title: 'Rate limiting on API endpoints', estimate: 3, owner: 'Patrick', status: 'todo', deps: 'None' },
  ],
  risks: [
    { level: 'medium', title: 'Make.com webhook latency', impact: 'Slow push/pull response times for iOS app', mitigation: 'Added 15s timeout + error handling in MakeService' },
    { level: 'low', title: 'Swift toolchain unavailable on Render', impact: 'Cannot run Swift tests in backend CI', mitigation: 'Separate swift-ci.yml runs on macOS runners' },
    { level: 'medium', title: 'No local database fallback', impact: 'Full dependency on Make.com for data persistence', mitigation: 'Evaluate SQLite cache layer for Sprint 2' },
  ],
  dod: [
    { text: 'Code reviewed and merged', checked: true },
    { text: 'CI passing (Swift + Python)', checked: true },
    { text: 'Deployed to Render', checked: true },
    { text: 'Architecture docs updated', checked: true },
    { text: 'iOS integration patch tested', checked: false },
    { text: 'Product sign-off from Patrick', checked: false },
  ],
  dates: [
    { date: '2026-04-08', label: 'Sprint start', today: true },
    { date: '2026-04-15', label: 'Mid-sprint check-in', today: false },
    { date: '2026-04-21', label: 'Code freeze', today: false },
    { date: '2026-04-22', label: 'Sprint end / Demo', today: false },
    { date: '2026-04-23', label: 'Retro', today: false },
  ],
};

let sprint = {};

function loadSprint() {
  const saved = localStorage.getItem('vlbh-sprint');
  if (saved) {
    try { sprint = JSON.parse(saved); return; } catch (e) { /* fall through */ }
  }
  sprint = JSON.parse(JSON.stringify(DEFAULT_SPRINT));
}

function saveSprint() {
  localStorage.setItem('vlbh-sprint', JSON.stringify(sprint));
}

/* Computed helpers */
function getStats() {
  const total = sprint.backlog.length;
  const done = sprint.backlog.filter(t => t.status === 'done').length;
  const wip = sprint.backlog.filter(t => t.status === 'wip').length;
  const blocked = sprint.backlog.filter(t => t.status === 'blocked').length;
  const totalPts = sprint.backlog.reduce((s, t) => s + t.estimate, 0);
  const donePts = sprint.backlog.filter(t => t.status === 'done').reduce((s, t) => s + t.estimate, 0);
  const totalCap = sprint.team.reduce((s, m) => s + m.allocation, 0);
  const pct = totalPts > 0 ? Math.round((donePts / totalPts) * 100) : 0;
  const load = totalCap > 0 ? Math.round((totalPts / totalCap) * 100) : 0;
  return { total, done, wip, blocked, totalPts, donePts, totalCap, pct, load };
}

/* Render */
function render() {
  const s = getStats();
  const today = new Date().toISOString().slice(0, 10);

  // Sprint header
  document.getElementById('sprint-name').textContent = sprint.name;
  document.getElementById('sprint-dates').textContent = `${sprint.startDate} — ${sprint.endDate}`;
  document.getElementById('sprint-team-count').textContent = `${sprint.team.length} members`;
  document.getElementById('sprint-goal-text').textContent = sprint.goal;

  // Stats
  document.getElementById('stat-progress').textContent = `${s.pct}%`;
  document.getElementById('stat-progress-sub').textContent = `${s.donePts} / ${s.totalPts} pts`;
  document.getElementById('progress-fill').style.width = `${s.pct}%`;

  document.getElementById('stat-tasks').textContent = `${s.done}/${s.total}`;
  document.getElementById('stat-tasks-sub').textContent = `${s.wip} in progress`;

  document.getElementById('stat-capacity').textContent = `${s.totalCap} pts`;
  document.getElementById('stat-capacity-sub').textContent = `Load: ${s.load}%`;

  const capEl = document.getElementById('stat-capacity-value');
  capEl.className = 'stat-value ' + (s.load > 90 ? 'red' : s.load > 75 ? 'yellow' : 'green');

  document.getElementById('stat-blocked').textContent = s.blocked;

  // Backlog
  const tbody = document.getElementById('backlog-body');
  tbody.innerHTML = sprint.backlog.map((item, idx) => `
    <tr>
      <td><span class="priority-badge ${item.priority.toLowerCase()}">${item.priority}</span></td>
      <td class="editable" onclick="editTask(${idx})">${item.title}</td>
      <td>${item.estimate} pts</td>
      <td>${item.owner}</td>
      <td>
        <span class="status-dot ${item.status}" onclick="cycleStatus(${idx})">
          ${item.status.toUpperCase()}
        </span>
      </td>
      <td>${item.deps}</td>
      <td><button class="modal-close" onclick="removeTask(${idx})" title="Remove">&times;</button></td>
    </tr>
  `).join('');

  // Capacity
  const capBody = document.getElementById('capacity-body');
  capBody.innerHTML = sprint.team.map((m, idx) => `
    <tr>
      <td><strong>${m.name}</strong><br><small style="color:var(--text-muted)">${m.role}</small></td>
      <td>${m.availableDays} / ${m.totalDays}</td>
      <td>
        ${m.allocation} pts
        <div class="capacity-bar"><div class="capacity-bar-fill" style="width:${Math.min(100, (m.allocation / (sprint.team.reduce((s,t) => s + t.allocation, 0) || 1)) * 100)}%"></div></div>
      </td>
      <td>${m.notes}</td>
    </tr>
  `).join('');

  // Risks
  const risksEl = document.getElementById('risks-list');
  risksEl.innerHTML = sprint.risks.map(r => `
    <div class="risk-item">
      <div class="risk-header">
        <span class="risk-level ${r.level}">${r.level}</span>
        <span class="risk-title">${r.title}</span>
      </div>
      <div class="risk-mitigation">${r.impact} — <em>${r.mitigation}</em></div>
    </div>
  `).join('');

  // DOD
  const dodEl = document.getElementById('dod-list');
  dodEl.innerHTML = sprint.dod.map((d, idx) => `
    <li class="dod-item">
      <div class="dod-check ${d.checked ? 'checked' : ''}" onclick="toggleDod(${idx})"></div>
      <span style="${d.checked ? 'text-decoration:line-through;color:var(--text-muted)' : ''}">${d.text}</span>
    </li>
  `).join('');

  // Dates
  const datesEl = document.getElementById('dates-list');
  datesEl.innerHTML = sprint.dates.map(d => `
    <li class="date-item ${d.date === today ? 'today' : ''}">
      <span class="date-value">${d.date.slice(5)}</span>
      <span class="date-label">${d.label}</span>
    </li>
  `).join('');
}

/* Actions */
function cycleStatus(idx) {
  const states = ['todo', 'wip', 'done', 'blocked'];
  const cur = states.indexOf(sprint.backlog[idx].status);
  sprint.backlog[idx].status = states[(cur + 1) % states.length];
  saveSprint();
  render();
}

function removeTask(idx) {
  if (confirm('Remove this task?')) {
    sprint.backlog.splice(idx, 1);
    saveSprint();
    render();
  }
}

function toggleDod(idx) {
  sprint.dod[idx].checked = !sprint.dod[idx].checked;
  saveSprint();
  render();
}

/* Modal — Add Task */
function openAddTask() {
  document.getElementById('modal-overlay').classList.add('active');
  document.getElementById('task-title').value = '';
  document.getElementById('task-estimate').value = '3';
  document.getElementById('task-owner').value = sprint.team[0]?.name || '';
  document.getElementById('task-priority').value = 'P1';
  document.getElementById('task-deps').value = 'None';
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('active');
}

function saveTask() {
  const title = document.getElementById('task-title').value.trim();
  if (!title) return;
  sprint.backlog.push({
    id: Date.now(),
    priority: document.getElementById('task-priority').value,
    title,
    estimate: parseInt(document.getElementById('task-estimate').value) || 3,
    owner: document.getElementById('task-owner').value,
    status: 'todo',
    deps: document.getElementById('task-deps').value || 'None',
  });
  saveSprint();
  closeModal();
  render();
}

function editTask(idx) {
  const task = sprint.backlog[idx];
  document.getElementById('modal-overlay').classList.add('active');
  document.getElementById('task-title').value = task.title;
  document.getElementById('task-estimate').value = task.estimate;
  document.getElementById('task-owner').value = task.owner;
  document.getElementById('task-priority').value = task.priority;
  document.getElementById('task-deps').value = task.deps;
  // Replace save handler
  const saveBtn = document.getElementById('save-task-btn');
  saveBtn.onclick = function() {
    task.title = document.getElementById('task-title').value.trim();
    task.estimate = parseInt(document.getElementById('task-estimate').value) || 3;
    task.owner = document.getElementById('task-owner').value;
    task.priority = document.getElementById('task-priority').value;
    task.deps = document.getElementById('task-deps').value || 'None';
    saveSprint();
    closeModal();
    saveBtn.onclick = saveTask;
    render();
  };
}

/* Health Check */
async function checkHealth() {
  const badge = document.getElementById('health-badge');
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      badge.className = 'health-badge';
      badge.querySelector('.health-text').textContent = 'API OK';
    } else {
      throw new Error();
    }
  } catch {
    badge.className = 'health-badge down';
    badge.querySelector('.health-text').textContent = 'API DOWN';
  }
}

/* Modules info */
function renderModules() {
  const modules = [
    { name: 'SLM', routes: 'push / pull', status: 'ok' },
    { name: 'SLA', routes: 'push / pull', status: 'ok' },
    { name: 'Session', routes: 'push / pull', status: 'ok' },
    { name: 'Lead', routes: 'push / pull', status: 'ok' },
    { name: 'Tore', routes: 'push / pull', status: 'ok' },
  ];
  const el = document.getElementById('modules-grid');
  el.innerHTML = modules.map(m => `
    <div class="module-item">
      <div class="module-name">${m.name}</div>
      <div class="module-routes">${m.routes}</div>
      <div class="module-status ok">operational</div>
    </div>
  `).join('');
}

/* Reset */
function resetSprint() {
  if (confirm('Reset sprint to defaults? All changes will be lost.')) {
    localStorage.removeItem('vlbh-sprint');
    loadSprint();
    render();
    renderModules();
  }
}

/* Init */
document.addEventListener('DOMContentLoaded', () => {
  loadSprint();
  render();
  renderModules();
  checkHealth();
});
