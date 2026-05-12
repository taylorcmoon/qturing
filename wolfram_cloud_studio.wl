(* ::Package:: *)

(*
  wolfram_cloud_studio.wl

  A customizable, context-aware Wolfram Cloud frontend.

  Features
  --------
  - Full HTML/CSS/JS single-page app served from Wolfram Cloud
  - Dark & light theme switcher
  - Intent-driven computation: natural language → WolframAlpha result
  - WL expression evaluator with sandboxed execution
  - Context panel: auto-detects running local dev processes
  - Live inline documentation
  - Settings panel that reconfigures the live deployment

  Usage    wolframscript -file wolfram_cloud_studio.wl

  -----
  Run in a Wolfram notebook or via wolframscript:


  The script deploys to Wolfram Cloud and prints the public URL.
  Re-running updates the deployment in place.

  Endpoints deployed
  ------------------
  GET  /              → HTML single-page application
  POST /api/evaluate  → Evaluate a WL expression (sandboxed)
  POST /api/alpha     → Query WolframAlpha, returns short answer
  GET  /api/context   → Live context: running dev processes, system info
  POST /api/config    → Read/write $AppConfig key-value pairs
  GET  /api/status    → Version, uptime, config snapshot
*)

Print["[WCS] Wolfram Cloud Studio - starting up..."];

(* ========================================================= *)
(* App Configuration                                         *)
(* ========================================================= *)

ClearAll[$AppConfig];

$AppConfig = <|
  "AppName"             -> "Wolfram Cloud Studio",
  "Version"             -> "1.0.0",
  "Theme"               -> "dark",
  "CloudSlug"           -> "wolfram-cloud-studio",
  "EnableWolframAlpha"  -> True,
  "EnableEvaluate"      -> True,
  "MaxOutputChars"      -> 4000,
  "DeployedAt"          -> DateString["ISODateTime"],
  "Permissions"         -> "Public"
|>;

(* ========================================================= *)
(* Theme CSS                                                 *)
(* ========================================================= *)

ClearAll[$ThemeVars];

$ThemeVars["dark"] = "
  --bg:          #0d0d12;
  --surface:     #17171f;
  --surface2:    #20202c;
  --surface3:    #2a2a38;
  --accent:      #cc5500;
  --accent-h:    #e8661a;
  --text:        #e2e2ef;
  --muted:       #6e6e84;
  --border:      #2c2c3a;
  --ok:          #22c55e;
  --warn:        #f59e0b;
  --err:         #ef4444;
";

$ThemeVars["light"] = "
  --bg:          #f4f4f9;
  --surface:     #ffffff;
  --surface2:    #eeeeF5;
  --surface3:    #e4e4ee;
  --accent:      #cc5500;
  --accent-h:    #e8661a;
  --text:        #18182a;
  --muted:       #7070 88;
  --border:      #d4d4e2;
  --ok:          #16a34a;
  --warn:        #d97706;
  --err:         #dc2626;
";

(* ========================================================= *)
(* Full CSS                                                  *)
(* ========================================================= *)

ClearAll[$BaseCSS];

$BaseCSS = "
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  background: var(--bg);
  color: var(--text);
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Header ── */
header {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 52px;
  padding: 0 20px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  z-index: 10;
}

header .logo {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.3px;
  color: var(--text);
}

header .logo span { color: var(--accent); }

header .version {
  font-size: 11px;
  color: var(--muted);
  background: var(--surface3);
  padding: 2px 8px;
  border-radius: 99px;
}

header .spacer { flex: 1; }

header .theme-btn {
  cursor: pointer;
  background: var(--surface3);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 12px;
  transition: background 0.15s;
}

header .theme-btn:hover { background: var(--surface2); }

/* ── Shell ── */
.shell {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ── Sidebar ── */
.sidebar {
  width: 200px;
  flex-shrink: 0;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 12px 8px;
  gap: 2px;
  overflow-y: auto;
}

.nav-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  padding: 8px 10px 4px;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  padding: 8px 10px;
  border: none;
  background: transparent;
  color: var(--text);
  font-size: 13px;
  text-align: left;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}

.nav-btn .icon { font-size: 15px; }

.nav-btn:hover { background: var(--surface3); }

.nav-btn.active {
  background: rgba(204, 85, 0, 0.15);
  color: var(--accent-h);
  font-weight: 500;
}

/* ── Main content ── */
.content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── Cards ── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
}

.card h2 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 14px;
  color: var(--text);
}

.card h3 {
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 10px;
}

/* ── Overview grid ── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.stat {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 16px;
}

.stat .label {
  font-size: 11px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 4px;
}

.stat .value {
  font-size: 20px;
  font-weight: 700;
  color: var(--accent-h);
}

.stat .sub {
  font-size: 11px;
  color: var(--muted);
}

/* ── Input / buttons ── */
textarea, input[type=text] {
  width: 100%;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  font-family: var(--font-mono, monospace);
  font-size: 13px;
  padding: 10px 12px;
  resize: vertical;
  outline: none;
  transition: border-color 0.15s;
}

textarea:focus, input[type=text]:focus {
  border-color: var(--accent);
}

.btn-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 10px;
}

button.btn {
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s;
  background: var(--surface3);
  color: var(--text);
}

button.btn:hover { background: var(--surface2); }

button.btn.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  font-weight: 600;
}

button.btn.primary:hover { background: var(--accent-h); }

/* ── Output ── */
.output-box {
  margin-top: 14px;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px 14px;
  font-family: var(--font-mono, monospace);
  font-size: 12.5px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-all;
  min-height: 60px;
  max-height: 380px;
  overflow-y: auto;
  color: var(--text);
}

.output-box.ok   { border-color: var(--ok);  }
.output-box.err  { border-color: var(--err); color: var(--err); }
.output-box.warn { border-color: var(--warn); }

/* ── Context panel ── */
.process-list { display: flex; flex-direction: column; gap: 8px; }

.process-item {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.process-item .pid {
  font-family: monospace;
  font-size: 11px;
  color: var(--muted);
  width: 50px;
  flex-shrink: 0;
}

.process-item .kind-badge {
  font-size: 10px;
  font-weight: 600;
  background: rgba(204, 85, 0, 0.15);
  color: var(--accent-h);
  padding: 2px 8px;
  border-radius: 99px;
  white-space: nowrap;
}

.process-item .cmd {
  font-family: monospace;
  font-size: 11px;
  color: var(--muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Docs ── */
.docs-nav { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 16px; }

.docs-tab {
  padding: 5px 12px;
  border: 1px solid var(--border);
  border-radius: 20px;
  background: var(--surface2);
  color: var(--muted);
  font-size: 12px;
  cursor: pointer;
}

.docs-tab.active {
  background: rgba(204,85,0,0.2);
  color: var(--accent-h);
  border-color: var(--accent);
}

.docs-section { display: none; }
.docs-section.active { display: block; }

.docs-section h4 {
  font-size: 13px;
  font-weight: 600;
  margin: 14px 0 6px;
  color: var(--text);
}

.docs-section p, .docs-section li {
  font-size: 13px;
  color: var(--muted);
  line-height: 1.7;
}

.docs-section ul { padding-left: 18px; }

.docs-section code {
  font-family: monospace;
  background: var(--surface3);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 12px;
  color: var(--accent-h);
}

/* ── Settings ── */
.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
  gap: 12px;
}

.setting-row:last-child { border-bottom: none; }

.setting-label { font-size: 13px; color: var(--text); }
.setting-desc  { font-size: 11px; color: var(--muted); margin-top: 2px; }

.setting-row input[type=text] { width: 220px; padding: 6px 10px; font-family: inherit; }

.toggle {
  position: relative;
  width: 42px;
  height: 24px;
  flex-shrink: 0;
}

.toggle input { opacity: 0; width: 0; height: 0; }

.toggle-slider {
  position: absolute;
  inset: 0;
  background: var(--surface3);
  border: 1px solid var(--border);
  border-radius: 99px;
  cursor: pointer;
  transition: background 0.2s;
}

.toggle-slider:before {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  left: 3px;
  top: 3px;
  background: var(--muted);
  border-radius: 50%;
  transition: transform 0.2s, background 0.2s;
}

.toggle input:checked + .toggle-slider { background: var(--accent); border-color: var(--accent); }
.toggle input:checked + .toggle-slider:before { transform: translateX(18px); background: #fff; }

/* ── Spinner ── */
.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  vertical-align: middle;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* ── History ── */
.history-list { display: flex; flex-direction: column; gap: 6px; max-height: 260px; overflow-y: auto; }

.history-item {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
}

.history-item:hover { border-color: var(--accent); }

.history-item .h-type {
  font-size: 10px;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  flex-shrink: 0;
  width: 48px;
}

.history-item .h-expr {
  font-family: monospace;
  font-size: 12px;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-state {
  text-align: center;
  color: var(--muted);
  font-size: 13px;
  padding: 32px;
}

/* ── Responsive ── */
@media (max-width: 700px) {
  .sidebar { display: none; }
  .content { padding: 16px; }
  .stats-grid { grid-template-columns: 1fr 1fr; }
}
";

(* ========================================================= *)
(* JavaScript SPA                                            *)
(* ========================================================= *)

ClearAll[$AppJS];

$AppJS = "
'use strict';

/* ── State ── */
const state = {
  tab: 'overview',
  theme: document.documentElement.getAttribute('data-theme') || 'dark',
  history: JSON.parse(sessionStorage.getItem('wcs-history') || '[]'),
  context: null,
  config: null,
};

/* ── Utilities ── */
function $(sel) { return document.querySelector(sel); }
function $all(sel) { return [...document.querySelectorAll(sel)]; }

function showTab(name) {
  state.tab = name;
  $all('.tab-panel').forEach(p => p.style.display = 'none');
  const panel = document.getElementById('tab-' + name);
  if (panel) panel.style.display = '';
  $all('.nav-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
}

function setOutput(el, text, type) {
  el.textContent = text;
  el.className = 'output-box ' + (type || '');
}

function addHistory(type, expr) {
  state.history.unshift({ type, expr, ts: new Date().toISOString() });
  if (state.history.length > 50) state.history.pop();
  sessionStorage.setItem('wcs-history', JSON.stringify(state.history));
  renderHistory();
}

async function apiFetch(path, body) {
  const opts = body
    ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
    : { method: 'GET' };
  try {
    const r = await fetch(path, opts);
    return await r.json();
  } catch (e) {
    return { error: String(e) };
  }
}

/* ── Theme ── */
function applyTheme(t) {
  state.theme = t;
  document.documentElement.setAttribute('data-theme', t);
  const btn = $('.theme-btn');
  if (btn) btn.textContent = t === 'dark' ? '☀ Light' : '☾ Dark';
  localStorage.setItem('wcs-theme', t);
}

/* ── Overview ── */
async function loadOverview() {
  const r = await apiFetch('api/status');
  if (r.error) return;
  const grid = $('#stat-grid');
  if (!grid) return;
  grid.innerHTML = Object.entries(r).map(([k, v]) => `
    <div class='stat'>
      <div class='label'>${k}</div>
      <div class='value' style='font-size:14px'>${String(v).slice(0, 40)}</div>
    </div>
  `).join('');
}

/* ── Evaluate ── */
async function runEvaluate() {
  const expr = $('#eval-input').value.trim();
  if (!expr) return;
  const out = $('#eval-output');
  setOutput(out, '⟳ evaluating…');
  addHistory('WL', expr);
  const r = await apiFetch('api/evaluate', { expression: expr });
  if (r.error) setOutput(out, r.error, 'err');
  else setOutput(out, r.result ?? r.output ?? JSON.stringify(r, null, 2), 'ok');
}

/* ── WolframAlpha ── */
async function runAlpha() {
  const q = $('#alpha-input').value.trim();
  if (!q) return;
  const out = $('#alpha-output');
  setOutput(out, '⟳ querying Wolfram|Alpha…');
  addHistory('Alpha', q);
  const r = await apiFetch('api/alpha', { query: q });
  if (r.error) setOutput(out, r.error, 'err');
  else setOutput(out, r.result ?? 'No result', 'ok');
}

/* ── Context ── */
async function loadContext() {
  const out = $('#context-list');
  if (!out) return;
  out.innerHTML = \"<div class='spinner'></div>\";
  const r = await apiFetch('api/context');
  state.context = r;
  if (r.error || !r.processes) {
    out.innerHTML = \"<div class='empty-state'>\" + (r.error || 'No process data') + '</div>';
    return;
  }
  const procs = r.processes;
  if (!procs.length) {
    out.innerHTML = \"<div class='empty-state'>No development processes detected</div>\";
    return;
  }
  out.innerHTML = procs.map(p => `
    <div class='process-item'>
      <span class='pid'>${p.pid || '—'}</span>
      <span class='kind-badge'>${p.kind || 'Process'}</span>
      <span class='cmd'>${(p.args || p.command || '').slice(0, 80)}</span>
    </div>
  `).join('');
}

/* ── Docs ── */
function showDocsSection(id) {
  $all('.docs-section').forEach(s => s.classList.remove('active'));
  $all('.docs-tab').forEach(t => t.classList.remove('active'));
  const s = document.getElementById('doc-' + id);
  if (s) s.classList.add('active');
  const t = document.querySelector('[data-doc=\"' + id + '\"]');
  if (t) t.classList.add('active');
}

/* ── History ── */
function renderHistory() {
  const el = $('#history-list');
  if (!el) return;
  if (!state.history.length) {
    el.innerHTML = \"<div class='empty-state'>No history yet</div>\";
    return;
  }
  el.innerHTML = state.history.map(h => `
    <div class='history-item' onclick='replayHistory(this)' data-type='${h.type}' data-expr='${encodeURIComponent(h.expr)}'>
      <span class='h-type'>${h.type}</span>
      <span class='h-expr'>${h.expr.slice(0, 80)}</span>
    </div>
  `).join('');
}

function replayHistory(el) {
  const type = el.dataset.type;
  const expr = decodeURIComponent(el.dataset.expr);
  if (type === 'WL') {
    showTab('evaluate');
    $('#eval-input').value = expr;
    runEvaluate();
  } else {
    showTab('alpha');
    $('#alpha-input').value = expr;
    runAlpha();
  }
}

/* ── Settings ── */
async function loadSettings() {
  const r = await apiFetch('api/config');
  state.config = r;
  const appNameInput = $('#cfg-appname');
  if (appNameInput && r.AppName) appNameInput.value = r.AppName;
  const maxCharsInput = $('#cfg-maxchars');
  if (maxCharsInput && r.MaxOutputChars) maxCharsInput.value = r.MaxOutputChars;
  const alphaToggle = $('#cfg-alpha');
  if (alphaToggle) alphaToggle.checked = !!r.EnableWolframAlpha;
  const evalToggle = $('#cfg-eval');
  if (evalToggle) evalToggle.checked = !!r.EnableEvaluate;
}

async function saveSettings() {
  const body = {
    AppName: $('#cfg-appname')?.value || state.config?.AppName,
    MaxOutputChars: parseInt($('#cfg-maxchars')?.value) || 4000,
    EnableWolframAlpha: $('#cfg-alpha')?.checked ?? true,
    EnableEvaluate: $('#cfg-eval')?.checked ?? true,
  };
  const r = await apiFetch('api/config', body);
  if (r.ok) {
    const s = $('#settings-status');
    if (s) { s.textContent = 'Saved!'; setTimeout(() => { s.textContent = ''; }, 2000); }
  }
  state.config = { ...state.config, ...body };
}

/* ── Init ── */
document.addEventListener('DOMContentLoaded', () => {
  const saved = localStorage.getItem('wcs-theme');
  applyTheme(saved || 'dark');

  $all('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const t = btn.dataset.tab;
      showTab(t);
      if (t === 'overview')  loadOverview();
      if (t === 'context')   loadContext();
      if (t === 'history')   renderHistory();
      if (t === 'settings')  loadSettings();
      if (t === 'docs')      showDocsSection('overview');
    });
  });

  const themeBtn = $('.theme-btn');
  if (themeBtn) themeBtn.addEventListener('click', () => applyTheme(state.theme === 'dark' ? 'light' : 'dark'));

  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      if (state.tab === 'evaluate') runEvaluate();
      if (state.tab === 'alpha')    runAlpha();
    }
  });

  $all('.docs-tab').forEach(t => {
    t.addEventListener('click', () => showDocsSection(t.dataset.doc));
  });

  showTab('overview');
  loadOverview();
});
";

(* ========================================================= *)
(* HTML Builder                                              *)
(* ========================================================= *)

ClearAll[BuildHTML];

BuildHTML[theme_String : "dark"] :=
  StringJoin[{
    "<!DOCTYPE html>\n<html lang='en' data-theme='", theme, "'>\n<head>\n",
    "<meta charset='UTF-8'>\n",
    "<meta name='viewport' content='width=device-width,initial-scale=1'>\n",
    "<title>", $AppConfig["AppName"], "</title>\n",
    "<style>\n",
    ":root {", $ThemeVars[theme], "}\n",
    $BaseCSS,
    "\n</style>\n",
    "</head>\n<body>\n",

    (* ── Header ── *)
    "<header>\n",
    "  <div class='logo'>Wolfram<span>|</span>Cloud Studio</div>\n",
    "  <span class='version'>v", $AppConfig["Version"], "</span>\n",
    "  <div class='spacer'></div>\n",
    "  <button class='theme-btn'>☀ Light</button>\n",
    "</header>\n",

    (* ── Shell ── *)
    "<div class='shell'>\n",

    (* ── Sidebar ── *)
    "<nav class='sidebar'>\n",
    "  <div class='nav-label'>Main</div>\n",
    "  <button class='nav-btn active' data-tab='overview'><span class='icon'>⬡</span> Overview</button>\n",
    "  <button class='nav-btn' data-tab='evaluate'><span class='icon'>≫</span> Evaluate</button>\n",
    "  <button class='nav-btn' data-tab='alpha'><span class='icon'>α</span> Wolfram|Alpha</button>\n",
    "  <button class='nav-btn' data-tab='context'><span class='icon'>⟳</span> Context</button>\n",
    "  <div class='nav-label' style='margin-top:8px'>Other</div>\n",
    "  <button class='nav-btn' data-tab='history'><span class='icon'>☰</span> History</button>\n",
    "  <button class='nav-btn' data-tab='docs'><span class='icon'>?</span> Docs</button>\n",
    "  <button class='nav-btn' data-tab='settings'><span class='icon'>⚙</span> Settings</button>\n",
    "</nav>\n",

    (* ── Content ── *)
    "<main class='content'>\n",

    (* Overview *)
    "<div id='tab-overview' class='tab-panel'>\n",
    "  <div class='card'>\n",
    "    <h2>System Overview</h2>\n",
    "    <div class='stats-grid' id='stat-grid'>\n",
    "      <div class='stat'><div class='label'>Loading</div><div class='value'>…</div></div>\n",
    "    </div>\n",
    "  </div>\n",
    "</div>\n",

    (* Evaluate *)
    "<div id='tab-evaluate' class='tab-panel' style='display:none'>\n",
    "  <div class='card'>\n",
    "    <h2>Wolfram Language Evaluator</h2>\n",
    "    <p style='font-size:12px;color:var(--muted);margin-bottom:12px;'>",
    "Enter any Wolfram Language expression. Press <code>Ctrl+Enter</code> to run.</p>\n",
    "    <textarea id='eval-input' rows='5' placeholder='E.g. Prime[100]  or  Table[i^2, {i, 10}]'></textarea>\n",
    "    <div class='btn-row'>\n",
    "      <button class='btn primary' onclick='runEvaluate()'>Run  ▶</button>\n",
    "      <button class='btn' onclick=\"$('#eval-input').value=''\">Clear</button>\n",
    "    </div>\n",
    "    <div id='eval-output' class='output-box'>Output will appear here…</div>\n",
    "  </div>\n",
    "</div>\n",

    (* Alpha *)
    "<div id='tab-alpha' class='tab-panel' style='display:none'>\n",
    "  <div class='card'>\n",
    "    <h2>Wolfram|Alpha Query</h2>\n",
    "    <p style='font-size:12px;color:var(--muted);margin-bottom:12px;'>",
    "Ask anything in plain English. Press <code>Ctrl+Enter</code> to query.</p>\n",
    "    <input type='text' id='alpha-input' placeholder='E.g. distance from Earth to Mars  or  GDP of Japan 2023'>\n",
    "    <div class='btn-row'>\n",
    "      <button class='btn primary' onclick='runAlpha()'>Ask  α</button>\n",
    "      <button class='btn' onclick=\"$('#alpha-input').value=''\">Clear</button>\n",
    "    </div>\n",
    "    <div id='alpha-output' class='output-box'>Answer will appear here…</div>\n",
    "  </div>\n",
    "</div>\n",

    (* Context *)
    "<div id='tab-context' class='tab-panel' style='display:none'>\n",
    "  <div class='card'>\n",
    "    <h2>Live Context</h2>\n",
    "    <p style='font-size:12px;color:var(--muted);margin-bottom:14px;'>",
    "Auto-detected development processes running on this host.</p>\n",
    "    <button class='btn' onclick='loadContext()' style='margin-bottom:14px'>↺ Refresh</button>\n",
    "    <div class='process-list' id='context-list'>",
    "<div class='empty-state'>Click Refresh to scan</div></div>\n",
    "  </div>\n",
    "</div>\n",

    (* History *)
    "<div id='tab-history' class='tab-panel' style='display:none'>\n",
    "  <div class='card'>\n",
    "    <h2>Session History</h2>\n",
    "    <p style='font-size:12px;color:var(--muted);margin-bottom:12px;'>",
    "Click any item to replay it.</p>\n",
    "    <div class='history-list' id='history-list'>",
    "<div class='empty-state'>No history yet</div></div>\n",
    "  </div>\n",
    "</div>\n",

    (* Docs *)
    "<div id='tab-docs' class='tab-panel' style='display:none'>\n",
    "  <div class='card'>\n",
    "    <h2>Documentation</h2>\n",
    "    <div class='docs-nav'>\n",
    "      <button class='docs-tab active' data-doc='overview'>Overview</button>\n",
    "      <button class='docs-tab' data-doc='evaluate'>Evaluator</button>\n",
    "      <button class='docs-tab' data-doc='alpha'>Wolfram|Alpha</button>\n",
    "      <button class='docs-tab' data-doc='context'>Context</button>\n",
    "      <button class='docs-tab' data-doc='api'>API Reference</button>\n",
    "    </div>\n",

    "    <div id='doc-overview' class='docs-section active'>\n",
    "      <h4>What is Wolfram Cloud Studio?</h4>\n",
    "      <p>A self-updating, context-aware frontend deployed entirely on Wolfram Cloud. ",
    "It observes your local environment, evaluates WL expressions, and queries ",
    "Wolfram|Alpha — all from one interface.</p>\n",
    "      <h4>Navigation</h4>\n",
    "      <ul>\n",
    "        <li><b>Overview</b> — live deployment stats</li>\n",
    "        <li><b>Evaluate</b> — run any Wolfram Language expression</li>\n",
    "        <li><b>Wolfram|Alpha</b> — natural-language queries</li>\n",
    "        <li><b>Context</b> — auto-detected dev processes on the host</li>\n",
    "        <li><b>History</b> — session replay for past queries</li>\n",
    "        <li><b>Settings</b> — live reconfiguration without redeployment</li>\n",
    "      </ul>\n",
    "    </div>\n",

    "    <div id='doc-evaluate' class='docs-section'>\n",
    "      <h4>Wolfram Language Evaluator</h4>\n",
    "      <p>Evaluates arbitrary WL in a sandboxed cloud kernel. ",
    "Output is returned as a plain string (OutputForm).</p>\n",
    "      <h4>Examples</h4>\n",
    "      <ul>\n",
    "        <li><code>Prime[1000]</code> — 1000th prime</li>\n",
    "        <li><code>IntegerDigits[2^100]</code> — digits of a large power</li>\n",
    "        <li><code>Solve[x^2 - 5x + 6 == 0, x]</code></li>\n",
    "        <li><code>StringJoin[Riffle[{\"a\",\"b\",\"c\"}, \"-\"]]</code></li>\n",
    "      </ul>\n",
    "      <h4>Keyboard shortcut</h4>\n",
    "      <p><code>Ctrl+Enter</code> (or <code>Cmd+Enter</code>) runs the current input.</p>\n",
    "    </div>\n",

    "    <div id='doc-alpha' class='docs-section'>\n",
    "      <h4>Wolfram|Alpha Integration</h4>\n",
    "      <p>Sends your query to Wolfram|Alpha and returns the short answer. ",
    "Works best for factual, computational, or scientific questions.</p>\n",
    "      <h4>Good queries</h4>\n",
    "      <ul>\n",
    "        <li>distance from Earth to Mars</li>\n",
    "        <li>population of Tokyo 2024</li>\n",
    "        <li>integral of sin(x)^2</li>\n",
    "        <li>100 USD in EUR</li>\n",
    "        <li>boiling point of ethanol</li>\n",
    "      </ul>\n",
    "    </div>\n",

    "    <div id='doc-context' class='docs-section'>\n",
    "      <h4>Context Detection</h4>\n",
    "      <p>The <b>Context</b> panel runs <code>ps -ax</code> on the cloud host and ",
    "classifies processes by development tool (Vite, FastAPI, Node, etc.). ",
    "It adapts the UI to suggest relevant panels.</p>\n",
    "      <h4>Supported process types</h4>\n",
    "      <ul>\n",
    "        <li>ViteFrontend, NextWebApp, WebpackFrontend</li>\n",
    "        <li>FastAPIService, FlaskService, DjangoService</li>\n",
    "        <li>NodeService, PythonService, WolframService</li>\n",
    "        <li>JupyterService, JavaService, ContainerRuntime</li>\n",
    "      </ul>\n",
    "    </div>\n",

    "    <div id='doc-api' class='docs-section'>\n",
    "      <h4>REST API Reference</h4>\n",
    "      <p>All endpoints accept/return JSON.</p>\n",
    "      <h4>GET /api/status</h4>\n",
    "      <p>Returns version, uptime, deployed-at, and current config snapshot.</p>\n",
    "      <h4>POST /api/evaluate</h4>\n",
    "      <p>Body: <code>{ \"expression\": \"...\" }</code><br/>",
    "Returns: <code>{ \"result\": \"...\" }</code> or <code>{ \"error\": \"...\" }</code></p>\n",
    "      <h4>POST /api/alpha</h4>\n",
    "      <p>Body: <code>{ \"query\": \"...\" }</code><br/>",
    "Returns: <code>{ \"result\": \"...\" }</code></p>\n",
    "      <h4>GET /api/context</h4>\n",
    "      <p>Returns <code>{ \"processes\": [...], \"system\": {...} }</code></p>\n",
    "      <h4>GET /api/config</h4>\n",
    "      <p>Returns current <code>$AppConfig</code> as JSON.</p>\n",
    "      <h4>POST /api/config</h4>\n",
    "      <p>Merges body keys into <code>$AppConfig</code> and returns <code>{ \"ok\": true }</code></p>\n",
    "    </div>\n",

    "  </div>\n",
    "</div>\n",

    (* Settings *)
    "<div id='tab-settings' class='tab-panel' style='display:none'>\n",
    "  <div class='card'>\n",
    "    <h2>Settings</h2>\n",

    "    <div class='setting-row'>\n",
    "      <div><div class='setting-label'>App Name</div>",
    "<div class='setting-desc'>Displayed in header and page title</div></div>\n",
    "      <input type='text' id='cfg-appname' value='", $AppConfig["AppName"], "'>\n",
    "    </div>\n",

    "    <div class='setting-row'>\n",
    "      <div><div class='setting-label'>Max Output Characters</div>",
    "<div class='setting-desc'>Truncation limit for evaluator results</div></div>\n",
    "      <input type='text' id='cfg-maxchars' value='",
    ToString[$AppConfig["MaxOutputChars"]], "'>\n",
    "    </div>\n",

    "    <div class='setting-row'>\n",
    "      <div><div class='setting-label'>Enable Wolfram|Alpha</div>",
    "<div class='setting-desc'>Allow Alpha queries from the frontend</div></div>\n",
    "      <label class='toggle'><input type='checkbox' id='cfg-alpha' checked>",
    "<span class='toggle-slider'></span></label>\n",
    "    </div>\n",

    "    <div class='setting-row'>\n",
    "      <div><div class='setting-label'>Enable Evaluator</div>",
    "<div class='setting-desc'>Allow WL expression evaluation</div></div>\n",
    "      <label class='toggle'><input type='checkbox' id='cfg-eval' checked>",
    "<span class='toggle-slider'></span></label>\n",
    "    </div>\n",

    "    <div class='btn-row' style='margin-top:16px'>\n",
    "      <button class='btn primary' onclick='saveSettings()'>Save Changes</button>\n",
    "      <span id='settings-status' style='font-size:12px;color:var(--ok);align-self:center'></span>\n",
    "    </div>\n",
    "  </div>\n",
    "</div>\n",

    "</main>\n",
    "</div>\n",

    "<script>\n", $AppJS, "\n</script>\n",
    "</body>\n</html>\n"
  }];

(* ========================================================= *)
(* JSON Response Helper                                      *)
(* ========================================================= *)

ClearAll[JSONResponse];

JSONResponse[data_] :=
  HTTPResponse[
    ExportString[data, "JSON", "Compact" -> True],
    <|
      "Content-Type"                -> "application/json; charset=utf-8",
      "Access-Control-Allow-Origin" -> "*"
    |>
  ];

(* ========================================================= *)
(* Context Observer (safe, local ps)                        *)
(* ========================================================= *)

ClearAll[
  $DevKeywords, $ClassifyProcess,
  ContextProcessText, ContextClassify, ContextScan
];

$DevKeywords = {
  "node", "npm", "pnpm", "yarn", "vite", "next", "webpack",
  "python", "uvicorn", "fastapi", "flask", "django", "jupyter",
  "java", "spring", "wolfram", "mathkernel", "docker", "ruby",
  "go ", "cargo", "rust", "bun"
};

ContextProcessText[p_Association] :=
  ToLowerCase[
    StringRiffle[
      ToString /@ {
        Lookup[p, "command", ""],
        Lookup[p, "args", ""],
        Lookup[p, "comm", ""]
      },
      " "
    ]
  ];

ContextClassify[text_String] :=
  Which[
    StringContainsQ[text, "vite"],     "ViteFrontend",
    StringContainsQ[text, "next"],     "NextWebApp",
    StringContainsQ[text, "webpack"],  "WebpackFrontend",
    StringContainsQ[text, "uvicorn"] || StringContainsQ[text, "fastapi"], "FastAPIService",
    StringContainsQ[text, "flask"],    "FlaskService",
    StringContainsQ[text, "django"],   "DjangoService",
    StringContainsQ[text, "jupyter"],  "JupyterService",
    StringContainsQ[text, "spring"],   "JavaService",
    StringContainsQ[text, "docker"],   "ContainerRuntime",
    StringContainsQ[text, "wolfram"] || StringContainsQ[text, "mathkernel"], "WolframService",
    StringContainsQ[text, "python"],   "PythonService",
    StringContainsQ[text, "node"] || StringContainsQ[text, "npm"], "NodeService",
    True, "GenericProcess"
  ];

ContextScan[] :=
  Module[
    {raw, lines, parsed},

    raw = Quiet@Check[ReadString[{"ps", "-axo", "pid,ppid,comm,args"}], ""];

    If[raw === "" || MissingQ[raw], Return[{}]];

    lines = Rest[StringSplit[raw, "\n"]];

    parsed =
      Select[
        Map[
          Function[
            line,
            Module[
              {parts, m},
              parts = StringSplit[StringTrim[line], RegularExpression["\\s+"], 4];
              If[Length[parts] < 3, Nothing,
                <|
                  "pid"     -> Quiet@ToExpression[parts[[1]]],
                  "ppid"    -> Quiet@ToExpression[parts[[2]]],
                  "comm"    -> If[Length[parts] >= 3, parts[[3]], ""],
                  "args"    -> If[Length[parts] >= 4, parts[[4]], ""],
                  "command" -> If[Length[parts] >= 3, parts[[3]], ""]
                |>
              ]
            ]
          ],
          lines
        ],
        AssociationQ[#] &
      ];

    Select[
      Map[
        Function[
          p,
          Module[
            {text = ContextProcessText[p]},
            If[
              AnyTrue[$DevKeywords, StringContainsQ[text, #] &],
              Append[p, "kind" -> ContextClassify[text]],
              Nothing
            ]
          ]
        ],
        parsed
      ],
      AssociationQ[#] &
    ]
  ];

(* ========================================================= *)
(* Safe Evaluator                                            *)
(* ========================================================= *)

ClearAll[SafeEvaluate];

$ForbiddenPatterns = {
  "DeleteFile", "CopyFile", "MoveFile", "CreateDirectory",
  "RunProcess", "StartProcess", "SystemOpen", "CreateScheduledTask",
  "WebExecute", "CloudDeploy", "CloudDelete", "CloudSave",
  "SendMail", "HTTPRequest", "URLRead", "URLFetch",
  "Import", "Export", "OpenWrite", "OpenAppend", "Put", "PutAppend",
  "Unprotect", "Remove", "Quit", "Exit", "AbortKernelLink"
};

SafeEvaluate[expr_String] :=
  Module[
    {
      maxChars = Lookup[$AppConfig, "MaxOutputChars", 4000],
      enabled  = TrueQ[Lookup[$AppConfig, "EnableEvaluate", True]],
      blocked,
      result,
      str
    },

    If[! enabled,
      Return[<|"error" -> "Evaluator is disabled in settings"|>]
    ];

    If[StringLength[expr] > 2000,
      Return[<|"error" -> "Expression too long (max 2000 chars)"|>]
    ];

    blocked = Select[$ForbiddenPatterns, StringContainsQ[expr, #] &];

    If[blocked =!= {},
      Return[
        <|"error" -> "Expression contains restricted operations: " <> StringRiffle[blocked, ", "]|>
      ]
    ];

    result =
      Quiet@Check[
        TimeConstrained[
          ToExpression[expr, InputForm, HoldComplete],
          10,
          Missing["Timeout"]
        ],
        Missing["EvalError"]
      ];

    If[MissingQ[result],
      Return[
        <|"error" ->
          If[result === Missing["Timeout"],
            "Evaluation timed out (10 s limit)",
            "Evaluation error"
          ]
        |>
      ]
    ];

    str =
      Quiet@Check[
        StringTake[
          ToString[ReleaseHold[result], OutputForm],
          UpTo[maxChars]
        ],
        "Result could not be stringified"
      ];

    <|"result" -> str|>
  ];

(* ========================================================= *)
(* WolframAlpha Query                                        *)
(* ========================================================= *)

ClearAll[SafeAlpha];

SafeAlpha[query_String] :=
  Module[
    {
      enabled = TrueQ[Lookup[$AppConfig, "EnableWolframAlpha", True]],
      result
    },

    If[! enabled,
      Return[<|"error" -> "Wolfram|Alpha is disabled in settings"|>]
    ];

    If[StringLength[query] > 500,
      Return[<|"error" -> "Query too long (max 500 chars)"|>]
    ];

    result =
      Quiet@Check[
        WolframAlpha[query, "ShortAnswer"],
        Missing["AlphaError"]
      ];

    If[MissingQ[result] || result === $Failed || result === "",
      <|"result" -> "No result found for: " <> query|>,
      <|"result" -> ToString[result]|>
    ]
  ];

(* ========================================================= *)
(* HTTP Handler                                              *)
(* ========================================================= *)

ClearAll[HandleRequest];

HandleRequest[req_HTTPRequest] :=
  Module[
    {
      path    = Lookup[req, "Path", ""],
      method  = Lookup[req, "Method", "GET"],
      body
    },

    (* normalize: strip leading slash, lower case *)
    path = StringTrim[path, StartOfString ~~ "/" ...];
    path = ToLowerCase[path];

    Which[

      (* ─── Main HTML ─── *)
      path === "" || path === "index.html",
        HTTPResponse[
          BuildHTML[Lookup[$AppConfig, "Theme", "dark"]],
          <|"Content-Type" -> "text/html; charset=utf-8"|>
        ],

      (* ─── Status ─── *)
      path === "api/status",
        JSONResponse[
          <|
            "AppName"    -> $AppConfig["AppName"],
            "Version"    -> $AppConfig["Version"],
            "Theme"      -> $AppConfig["Theme"],
            "DeployedAt" -> $AppConfig["DeployedAt"],
            "Now"        -> DateString["ISODateTime"],
            "WolframAlpha" -> If[TrueQ[$AppConfig["EnableWolframAlpha"]], "on", "off"],
            "Evaluator"  -> If[TrueQ[$AppConfig["EnableEvaluate"]], "on", "off"]
          |>
        ],

      (* ─── Evaluate ─── *)
      path === "api/evaluate",
        With[
          {
            body = Quiet@Check[
              ImportString[req["Body"], "JSON"],
              <||>
            ],
            expr = Quiet@Check[
              Lookup[ImportString[req["Body"], "JSON"], "expression", ""],
              ""
            ]
          },
          JSONResponse[SafeEvaluate[expr]]
        ],

      (* ─── Alpha ─── *)
      path === "api/alpha",
        With[
          {
            q = Quiet@Check[
              Lookup[ImportString[req["Body"], "JSON"], "query", ""],
              ""
            ]
          },
          JSONResponse[SafeAlpha[q]]
        ],

      (* ─── Context ─── *)
      path === "api/context",
        JSONResponse[
          <|
            "scannedAt" -> DateString["ISODateTime"],
            "processes" -> ContextScan[],
            "system"    -> <|
              "platform" -> $SystemID,
              "version"  -> $VersionNumber
            |>
          |>
        ],

      (* ─── Config GET ─── *)
      path === "api/config" && method === "GET",
        JSONResponse[$AppConfig],

      (* ─── Config POST ─── *)
      path === "api/config" && method === "POST",
        Module[
          {patch},
          patch =
            Quiet@Check[
              ImportString[req["Body"], "JSON"],
              <||>
            ];
          If[
            AssociationQ[patch],
            $AppConfig = Join[$AppConfig, patch]
          ];
          JSONResponse[<|"ok" -> True|>]
        ],

      (* ─── 404 ─── *)
      True,
        HTTPResponse[
          ExportString[<|"error" -> "Not found", "path" -> path|>, "JSON"],
          <|"Content-Type" -> "application/json", "StatusCode" -> 404|>
        ]
    ]
  ];

(* ========================================================= *)
(* Deploy                                                    *)
(* ========================================================= *)

ClearAll[DeployApp, $DeployedObject];

DeployApp[] :=
  Module[
    {
      slug    = $AppConfig["CloudSlug"],
      perms   = $AppConfig["Permissions"],
      handler,
      obj
    },

    Print["[WCS] Building handler..."];

    handler = HTTPHandlerFunction[HandleRequest];

    Print["[WCS] Deploying to CloudObject[\"", slug, "\"]..."];

    obj =
      Quiet@Check[
        CloudDeploy[
          handler,
          CloudObject[slug],
          Permissions -> perms
        ],
        $Failed
      ];

    If[
      obj === $Failed,
      Print["[WCS] ERROR: CloudDeploy failed. Are you authenticated? Run CloudConnect[]."];
      Return[$Failed]
    ];

    $DeployedObject = obj;

    Print["[WCS] ✓ Deployed successfully!"];
    Print["[WCS] Public URL: ", CloudObjectURL[obj]];
    Print["[WCS] API endpoints:"];
    Print["  GET  ", CloudObjectURL[obj]];
    Print["  GET  ", CloudObjectURL[obj], "/api/status"];
    Print["  POST ", CloudObjectURL[obj], "/api/evaluate"];
    Print["  POST ", CloudObjectURL[obj], "/api/alpha"];
    Print["  GET  ", CloudObjectURL[obj], "/api/context"];
    Print["  GET  ", CloudObjectURL[obj], "/api/config"];
    Print["  POST ", CloudObjectURL[obj], "/api/config"];

    obj
  ];

(* ========================================================= *)
(* Entry Point                                               *)
(* ========================================================= *)

Print["[WCS] Initialized. Call DeployApp[] to deploy, or call handlers directly."];
Print["[WCS] Example: SafeEvaluate[\"Prime[100]\"]"];
Print["[WCS] Example: SafeAlpha[\"distance from Earth to Moon\"]"];
Print["[WCS] Example: DeployApp[]"];

DeployApp[]
