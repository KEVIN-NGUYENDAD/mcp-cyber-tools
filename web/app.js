// ============================================================================
// SENTINELOPS - SOC COMMAND CENTER
// Real-time dashboard reading from state files
// ============================================================================

console.log('[APP.JS] Script loaded at:', new Date().toISOString());

let stateData = {
  assets: null,
  shadowAssets: null,
  incidents: null,
  risk: null,
  health: null,
  defender: null,
  firewall: null,
  alerts: null,
  waap: null,
  domain: null,
  threatPersistence: null,
  threatLateral: null,
  threatCredential: null,
  threatProcesses: null
};

let currentTopology = 'physical';
let refreshInterval = 30000;

// ============================================================================
// INITIALIZATION
// ============================================================================

async function init() {
  console.log('[INIT] SentinelOps starting...');
  try {
    await loadAllData();
    renderOverviewPage();
    if (typeof setupEventListeners === 'function') setupEventListeners();
    startAutoRefresh();
    console.log('[INIT] SentinelOps ready');
  } catch (error) {
    console.error('[INIT] Startup error:', error);
  }
}

// ============================================================================
// DATA LOADING
// ============================================================================

async function loadAllData() {
  try {
    // Load from public API endpoint or local JSON
    const baseUrl = '/api/state';

    const [assets, shadowAssets, incidents, risk, health, defender, firewall, alerts, waap, domain, threatPersistence, threatLateral, threatCredential, threatProcesses, sensorCoverage] = await Promise.allSettled([
      fetch(`${baseUrl}/assets.json`).then(r => r.json()).catch(() => ({ assets: [] })),
      fetch(`${baseUrl}/shadow_assets.json`).then(r => r.json()).catch(() => ({ shadows: [] })),
      fetch(`${baseUrl}/incidents.json`).then(r => r.json()).catch(() => ({ incidents: [] })),
      fetch(`${baseUrl}/risk_score.json`).then(r => r.json()).catch(() => ({ overall_score: 0 })),
      fetch(`${baseUrl}/system_health.json`).then(r => r.json()).catch(() => ({})),
      fetch(`${baseUrl}/defender_status.json`).then(r => r.json()).catch(() => ({})),
      fetch(`${baseUrl}/firewall_status.json`).then(r => r.json()).catch(() => ({})),
      fetch(`${baseUrl}/notification_history.json`).then(r => r.json()).catch(() => ({ sent_alerts: [] })),
      fetch(`${baseUrl}/waap_status.json`).then(r => r.json()).catch(() => ({})),
      fetch(`${baseUrl}/domain_status.json`).then(r => r.json()).catch(() => ({})),
      fetch(`${baseUrl}/hunting_persistence.json`).then(r => r.json()).catch(() => ({ indicators: [] })),
      fetch(`${baseUrl}/hunting_lateral_movement.json`).then(r => r.json()).catch(() => ({ indicators: [] })),
      fetch(`${baseUrl}/hunting_credential_dumping.json`).then(r => r.json()).catch(() => ({ indicators: [] })),
      fetch(`${baseUrl}/hunting_suspicious_processes.json`).then(r => r.json()).catch(() => ({ indicators: [] })),
      fetch(`${baseUrl}/sensor_coverage.json`).then(r => r.json()).catch(() => null)
    ]);

    stateData.assets = assets.value || { assets: [] };
    stateData.shadowAssets = shadowAssets.value || { shadows: [] };
    stateData.incidents = incidents.value || { incidents: [] };
    stateData.risk = risk.value || { overall_score: 0 };
    stateData.health = health.value || {};
    stateData.defender = defender.value || {};
    stateData.firewall = firewall.value || {};
    stateData.alerts = alerts.value || { sent_alerts: [] };
    stateData.waap = waap.value || {};
    stateData.domain = domain.value || {};
    stateData.threatPersistence = threatPersistence.value || { indicators: [] };
    stateData.threatLateral = threatLateral.value || { indicators: [] };
    stateData.threatCredential = threatCredential.value || { indicators: [] };
    stateData.threatProcesses = threatProcesses.value || { indicators: [] };
    stateData.sensorCoverage = sensorCoverage.value || null;
    // stateData.mcp tung duoc viet cung thanh { status: 'ONLINE', tool_count: '90+' ... }.
    // Gio no la ket qua kiem that; null khi chua tung chay tool_validator.py.
    stateData.mcp = stateData.sensorCoverage ? stateData.sensorCoverage.tool_summary || null : null;

    updateLastUpdate();
    console.log('[DATA] Loaded:', Object.keys(stateData).length, 'data sources');
  } catch (error) {
    console.error('[ERROR] Loading data:', error);
  }
}

function updateLastUpdate() {
  try {
    const now = new Date();
    const time = now.toLocaleTimeString();
    const lastUpdateEl = document.getElementById('lastUpdate');
    if (lastUpdateEl) {
      lastUpdateEl.textContent = `Last update: ${time}`;
    }
  } catch (error) {
    console.error('[ERROR] updateLastUpdate:', error);
  }
}

// ============================================================================
// PAGE NAVIGATION
// ============================================================================

function switchPage(pageName) {
  try {
    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

    // Show selected page
    const pageEl = document.getElementById(pageName);
    if (!pageEl) {
      console.error('[ERROR] Page not found:', pageName);
      return;
    }
    pageEl.classList.add('active');

    // Update nav - find the clicked nav item
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    const navItem = event?.target?.closest('.nav-item');
    if (navItem) navItem.classList.add('active');

    // Render page content with safety checks
    switch (pageName) {
      case 'overview':
        renderOverviewPage();
        break;
      case 'assets':
        renderAssetCommandCenter();
        break;
      case 'threats':
        renderThreatIntelligence();
        break;
      case 'brief':
        renderDailyBriefArchive();
        break;
      case 'network':
        setTimeout(() => renderNetworkTopology(), 100);
        break;
      case 'incidents':
        if (typeof renderIncidentBoard === 'function') renderIncidentBoard();
        break;
      case 'analytics':
        if (typeof renderAnalytics === 'function') renderAnalytics();
        break;
      case 'scorecard':
        if (typeof renderExecutiveScorecard === 'function') renderExecutiveScorecard();
        break;
      case 'history':
        if (typeof renderTimeline === 'function') renderTimeline();
        break;
      default:
        console.warn('[WARN] Unknown page:', pageName);
    }
  } catch (error) {
    console.error('[ERROR] switchPage:', error);
  }
}

// ============================================================================
// OVERVIEW PAGE
// ============================================================================

function renderOverviewPage() {
  console.log('[RENDER] renderOverviewPage called');
  try {
    console.log('[DEBUG] stateData:', { assets: !!stateData.assets, incidents: !!stateData.incidents, risk: !!stateData.risk });
    if (!stateData.assets || !stateData.incidents || !stateData.risk) {
      console.log('[WARN] Data not ready - RETURNING EARLY');
      return;
    }
    console.log('[RENDER] Data ready - proceeding');

    const assets = stateData.assets.assets || [];
    const incidents = stateData.incidents.incidents || [];
    const riskScore = stateData.risk.overall_score || 0;
    const alerts = stateData.alerts.sent_alerts || [];

    // Calculate metrics
    const criticalIncidents = incidents.filter(i => i?.severity === 'CRITICAL').length;
    const healthyAssets = assets.filter(a => (a?.vulnerability_count || 0) <= 10).length;
    const avgRisk = assets.length > 0 ? Math.round(assets.reduce((sum, a) => sum + (a?.vulnerability_count || 0), 0) / assets.length) : 0;

    // Update KPIs with existence checks
    const kpiAssets = document.getElementById('kpi-assets');
    const kpiAssetsSub = document.getElementById('kpi-assets-sub');
    if (kpiAssets) kpiAssets.textContent = assets.length;
    if (kpiAssetsSub) kpiAssetsSub.textContent = `${healthyAssets} healthy`;

    const kpiIncidents = document.getElementById('kpi-incidents');
    const kpiIncidentsSub = document.getElementById('kpi-incidents-sub');
    const kpiRisk = document.getElementById('kpi-risk');
    const kpiRiskSub = document.getElementById('kpi-risk-sub');

    if (kpiIncidents) kpiIncidents.textContent = incidents.length;
    if (kpiIncidentsSub) kpiIncidentsSub.textContent = `${criticalIncidents} critical`;
    if (kpiRisk) kpiRisk.textContent = riskScore;
    if (kpiRiskSub) kpiRiskSub.textContent = getRiskLevel(riskScore);

    // Calculate WAAP Health Score from security_summary
    let waapScore = 0;
    if (stateData.waap?.security_summary) {
      if (stateData.waap.security_summary.ssl_valid) waapScore += 60;
      if (stateData.waap.security_summary.waf_active) waapScore += 15;
      if (stateData.waap.security_summary.cdn_active) waapScore += 15;
      if (stateData.waap.security_summary.protection_active) waapScore += 10;
    }
    const kpiWaap = document.getElementById('kpi-waap');
    if (kpiWaap) kpiWaap.textContent = waapScore > 0 ? waapScore : '-';

    // Calculate DNS Health from dns_complete
    let dnsHealth = 0;
    let dnsChecks = 0;
    if (stateData.domain?.dns_complete) {
      const checks = ['has_nameservers', 'has_a_records', 'has_mx_records', 'has_spf', 'has_dmarc'];
      checks.forEach(check => {
        if (check in stateData.domain.dns_complete) {
          dnsChecks++;
          if (stateData.domain.dns_complete[check]) dnsHealth++;
        }
      });
    }
    const dnsPercent = dnsChecks > 0 ? Math.round((dnsHealth / dnsChecks) * 100) : '-';
    const kpiDns = document.getElementById('kpi-dns');
    if (kpiDns) kpiDns.textContent = dnsPercent !== '-' ? dnsPercent + '%' : '-';

    const minutesOld = Math.round((Date.now() - new Date(stateData.assets?._fetched_at || stateData.assets?.timestamp || Date.now())) / 60000);
    const kpiFresh = document.getElementById('kpi-fresh');
    const kpiFreshSub = document.getElementById('kpi-fresh-sub');
    if (kpiFresh) kpiFresh.textContent = minutesOld;
    if (kpiFreshSub) kpiFreshSub.textContent = minutesOld > 5 ? 'STALE' : 'FRESH';

    // Mission Control
    const mcThreat = document.getElementById('mc-threat');
    const mcAssets = document.getElementById('mc-assets');
    const mcIncidents = document.getElementById('mc-incidents');
    const mcCritical = document.getElementById('mc-critical');
    const mcRisk = document.getElementById('mc-risk');
    const mcFresh = document.getElementById('mc-fresh');

    if (mcThreat) mcThreat.textContent = getThreatLevel(riskScore);
    if (mcAssets) mcAssets.textContent = assets.length;
    if (mcIncidents) mcIncidents.textContent = incidents.length;
    if (mcCritical) mcCritical.textContent = criticalIncidents;
    if (mcRisk) mcRisk.textContent = riskScore + '/100';
    if (mcFresh) mcFresh.textContent = minutesOld + ' min';

    // Recent Activity
    const recentIncidents = incidents.slice(0, 3);
    const activityHtml = recentIncidents.length > 0
      ? recentIncidents.map(inc => `
          <div style="padding: 10px 0; border-bottom: 1px solid var(--color-border); font-size: 0.9em;">
            <span class="badge ${getBadgeClass(inc?.severity)}">${inc?.severity || 'UNKNOWN'}</span>
            <span style="margin-left: 10px; color: var(--color-accent);">${inc?.incident_id || 'N/A'}</span>
            <div style="color: var(--color-text-dim); margin-top: 5px;">${inc?.title || 'N/A'}</div>
          </div>
        `).join('')
      : '<div style="color: var(--color-text-dim);">No recent incidents</div>';

    const recentActivityEl = document.getElementById('recent-activity');
    if (recentActivityEl) recentActivityEl.innerHTML = activityHtml;

    // Alert Status
    const criticalAlerts = alerts.filter(a => a?.severity === 'CRITICAL').length;
    const highAlerts = alerts.filter(a => a?.severity === 'HIGH').length;
    const lastAlert = alerts.length > 0 ? new Date(alerts[0]?.sent_at).toLocaleString() : '-';

    const alertsTotal = document.getElementById('alerts-total');
    const alertsLast = document.getElementById('alerts-last');
    const alertsCritical = document.getElementById('alerts-critical');
    const alertsHigh = document.getElementById('alerts-high');

    if (alertsTotal) alertsTotal.textContent = alerts.length;
    if (alertsLast) alertsLast.textContent = lastAlert;
    if (alertsCritical) alertsCritical.textContent = criticalAlerts;
    if (alertsHigh) alertsHigh.textContent = highAlerts;

    // Update Executive Security Row
    updateExecutiveSecurityRow(assets);

    // Render Network Topology
    setTimeout(() => renderNetworkTopology(), 100);
  } catch (error) {
    console.error('[ERROR] renderOverviewPage:', error);
  }
}

function updateExecutiveSecurityRow(assets) {
  try {
    // WAAP Security with null safety
    let waapScore = 0;
    if (stateData.waap?.security_summary) {
      if (stateData.waap.security_summary.ssl_valid) waapScore += 60;
      if (stateData.waap.security_summary.waf_active) waapScore += 15;
      if (stateData.waap.security_summary.cdn_active) waapScore += 15;
      if (stateData.waap.security_summary.protection_active) waapScore += 10;
    }
    const sslStatus = stateData.waap?.ssl_status ? stateData.waap.ssl_status.toUpperCase() : 'UNKNOWN';
    const wafStatus = stateData.waap?.security_summary?.waf_active ? '✓ ACTIVE' : '✗ INACTIVE';
    const cdnStatus = stateData.waap?.security_summary?.cdn_active ? '✓ ACTIVE' : '✗ INACTIVE';
    const certDays = stateData.waap?.days_until_expiry || '-';

    const execWaapScore = document.getElementById('exec-waap-score');
    const execWaapSsl = document.getElementById('exec-waap-ssl');
    const execWaapWaf = document.getElementById('exec-waap-waf');
    const execWaapCdn = document.getElementById('exec-waap-cdn');
    const execWaapCert = document.getElementById('exec-waap-cert');

    if (execWaapScore) execWaapScore.textContent = waapScore > 0 ? waapScore + '/100' : '-';
    if (execWaapSsl) execWaapSsl.textContent = sslStatus;
    if (execWaapWaf) execWaapWaf.textContent = wafStatus;
    if (execWaapCdn) execWaapCdn.textContent = cdnStatus;
    if (execWaapCert) execWaapCert.textContent = certDays + ' days';

    // Vulnerability Center with array safety
    const validAssets = Array.isArray(assets) ? assets : [];
    const totalVulns = validAssets.reduce((sum, a) => sum + (a?.vulnerability_count || 0), 0);
    const critVulns = validAssets.reduce((sum, a) => sum + (a?.critical || 0), 0);
    const highVulns = validAssets.reduce((sum, a) => sum + (a?.high || 0), 0);
    const medVulns = validAssets.reduce((sum, a) => sum + (a?.medium || 0), 0);
    const lowVulns = validAssets.reduce((sum, a) => sum + (a?.low || 0), 0);

    const execVulnTotal = document.getElementById('exec-vuln-total');
    const execVulnAssets = document.getElementById('exec-vuln-assets');
    const execVulnCrit = document.getElementById('exec-vuln-crit');
    const execVulnHigh = document.getElementById('exec-vuln-high');
    const execVulnMed = document.getElementById('exec-vuln-med');
    const execVulnLow = document.getElementById('exec-vuln-low');

    if (execVulnTotal) execVulnTotal.textContent = totalVulns;
    if (execVulnAssets) execVulnAssets.textContent = validAssets.length;
    if (execVulnCrit) execVulnCrit.textContent = critVulns;
    if (execVulnHigh) execVulnHigh.textContent = highVulns;
    if (execVulnMed) execVulnMed.textContent = medVulns;
    if (execVulnLow) execVulnLow.textContent = lowVulns;

    // MCP Intelligence
    const execMcpQueue = document.getElementById('exec-mcp-queue');
    if (execMcpQueue) execMcpQueue.textContent = '0';

    renderSensorCoverage();
  } catch (error) {
    console.error('[ERROR] updateExecutiveSecurityRow:', error);
  }
}

// ============================================================================
// SENSOR COVERAGE
// ============================================================================
//
// Mot cam bien chet va mot may sach deu bao "0 phat hien". Khoi nay ton tai de
// hai truong hop do khong con doc giong nhau tren man hinh.
//
// Nguon: state/sensor_coverage.json, sinh boi scripts/tool_validator.py.
// Khong co file do thi khong ve gi ca — noi thang la chua tung kiem, chu khong
// hien mot mau xanh mac dinh.

const SENSOR_COVERAGE_ICON = { covered: '✅', partial: '⚠', blind: '❌' };
const SENSOR_COVERAGE_COLOR = {
  covered: '#00C896', partial: '#FFB020', blind: '#FF3B5C'
};

// Ba nang luc phat hien duoc goi ten. Chung KHONG phai mot cach xem khac cua
// bang nguon ben duoi — chung tra loi mot cau hoi khac.
//
//   bang nguon : "co mo duoc log nay khong?"
//   bang nay   : "log nay co dang GHI thu ta can khong?"
//
// Vi du song tren chinh may nay: log PowerShell/Operational doc duoc het, nen
// nguon `event_logs` hien COVERED. Nhung chinh sach Script Block Logging dang
// tat, nen PowerShell chi ghi nhung khoi lenh no tu cho la dang ngo. Doc duoc
// toan bo mot cuon so ghi chep co chon loc khong phai la nhin thay moi thu —
// va neu chi co mot cot thi khac biet do bien mat.
function renderCapabilityCoverage(capabilities) {
  const box = document.getElementById('capability-coverage');
  if (!box) return;

  if (!capabilities || !capabilities.length) {
    box.innerHTML = '';
    return;
  }

  const rows = capabilities.map(c => {
    const color = SENSOR_COVERAGE_COLOR[c.status] || 'var(--color-text-dim)';
    const icon = SENSOR_COVERAGE_ICON[c.status] || '?';
    return `
      <div style="display: grid; grid-template-columns: 180px 120px 1fr; gap: 10px; align-items: start; padding: 9px 12px; border-top: 1px solid var(--color-border, rgba(255,255,255,0.08));">
        <div>
          <div style="color: var(--color-text); font-size: 0.9em;">${escapeHtmlSafe(c.label)}</div>
          <div style="color: var(--color-text-dim); font-size: 0.72em; font-family: monospace;">${escapeHtmlSafe(c.detail || '')}</div>
        </div>
        <div style="font-weight: bold; color: ${color}; white-space: nowrap;">${icon} ${String(c.status).toUpperCase()}</div>
        <div style="font-size: 0.78em; color: var(--color-text-dim); line-height: 1.45;">
          ${escapeHtmlSafe(c.reason || '')}
          ${c.action ? `<div style="margin-top: 4px; color: ${color};">→ ${escapeHtmlSafe(c.action)}</div>` : ''}
        </div>
      </div>`;
  }).join('');

  const s = { covered: 0, partial: 0, blind: 0 };
  capabilities.forEach(c => { if (s[c.status] !== undefined) s[c.status] += 1; });

  box.innerHTML = `
    <div style="border: 1px solid var(--color-border, rgba(255,255,255,0.1)); border-radius: 6px; background: rgba(255,255,255,0.02);">
      <div style="display: flex; justify-content: space-between; align-items: baseline; gap: 8px; padding: 9px 12px;">
        <span style="font-size: 0.85em; color: var(--color-text); letter-spacing: 0.04em;">NANG LUC PHAT HIEN</span>
        <span style="font-size: 0.75em; color: var(--color-text-dim); font-family: monospace;">
          ✅ ${s.covered} covered &middot; ⚠ ${s.partial} partial &middot; ❌ ${s.blind} blind
        </span>
      </div>
      ${rows}
    </div>`;
}

function renderSensorCoverage() {
  const grid = document.getElementById('sensor-coverage-grid');
  if (!grid) return;
  const meta = document.getElementById('sensor-coverage-meta');
  const note = document.getElementById('sensor-coverage-note');
  const coverage = stateData.sensorCoverage;

  const setToolCounts = (summary) => {
    const put = (id, value) => {
      const el = document.getElementById(id);
      if (el) el.textContent = value;
    };
    put('exec-mcp-tools', summary ? summary.tool_count : '?');
    put('exec-mcp-pass', summary ? summary.pass : '?');
    put('exec-mcp-blind', summary ? summary.blind : '?');
    put('exec-mcp-fail', summary ? summary.fail : '?');
  };

  if (!coverage || !coverage.details) {
    grid.innerHTML = '<div style="color: var(--color-text-dim);">Chua chay scripts/tool_validator.py — chua biet cam bien nao dang nhin thay gi.</div>';
    if (meta) meta.textContent = 'NEVER VERIFIED';
    if (note) note.textContent = '';
    renderCapabilityCoverage(null);
    setToolCounts(null);
    return;
  }

  setToolCounts(coverage.tool_summary);
  renderCapabilityCoverage(coverage.detection_capabilities);

  const order = ['defender', 'firewall', 'security_log', 'event_logs',
                 'persistence', 'processes', 'network', 'ioc'];
  grid.innerHTML = order.map(key => {
    const d = coverage.details[key];
    if (!d) return '';
    const color = SENSOR_COVERAGE_COLOR[d.status] || 'var(--color-text-dim)';
    const icon = SENSOR_COVERAGE_ICON[d.status] || '?';
    return `
      <div style="border: 1px solid ${color}; border-left: 4px solid ${color}; border-radius: 6px; padding: 10px 12px; background: rgba(255,255,255,0.02);">
        <div style="display: flex; justify-content: space-between; align-items: baseline; gap: 8px;">
          <span style="font-size: 0.9em; color: var(--color-text);">${d.label}</span>
          <span style="font-weight: bold; color: ${color}; white-space: nowrap;">${icon} ${d.status.toUpperCase()}</span>
        </div>
        <div style="margin-top: 6px; font-size: 0.78em; color: var(--color-text-dim); font-family: monospace;">
          ${d.pass} pass &middot; ${d.empty} empty &middot; ${d.blind} blind &middot; ${d.fail} fail
        </div>
        ${d.reason ? `<div style="margin-top: 5px; font-size: 0.75em; color: ${color};">${escapeHtmlSafe(d.reason)}</div>` : ''}
      </div>`;
  }).join('');

  const s = coverage.summary || {};
  if (meta) {
    // Coverage khong tu lam moi theo pipeline (tool_validator.py goi that 99
    // tool, co tac dung phu). Nen tuoi cua no phai hien ra: mot ban do vung mu
    // cu ba ngay van doc nhu su that hom nay neu khong ai noi no bao nhieu tuoi.
    const ageHours = coverage.generated_at
      ? (Date.now() - new Date(coverage.generated_at).getTime()) / 3600000
      : null;
    const stale = ageHours !== null && ageHours > 24;
    meta.textContent = `${s.covered || 0} covered / ${s.partial || 0} partial / ${s.blind || 0} blind`
      + (coverage.generated_at ? ` — ${new Date(coverage.generated_at).toLocaleString()}` : '')
      + (stale ? ` (CU ${Math.floor(ageHours / 24)} ngay — chay lai tool_validator.py)` : '');
    meta.style.color = stale ? '#FFB020' : 'var(--color-text-dim)';
  }

  if (note) {
    const parts = [];
    const e = coverage.event_4688;
    if (e) {
      parts.push(`<strong>Event ID 4688 (Process Creation):</strong> observable = <strong style="color: ${e.observable ? '#00C896' : '#FF3B5C'};">${e.observable}</strong> (${e.status}). ${escapeHtmlSafe(e.reason || '')}`);
    }

    // Mot o do khong kem loi khuyen thi chi la mot o do. Neu vung mu sua duoc
    // ngay tren may nay, no phai hien ra canh chinh vung mu do — khong phai
    // nam trong mot file bao cao ma khong ai mo.
    const d = coverage.access_diagnosis;
    if (d && d.can_fix) {
      parts.push(`<div style="margin-top: 10px; padding: 10px 12px; border-left: 4px solid #FFB020; background: rgba(255,176,32,0.08); border-radius: 4px;">
        <strong style="color: #FFB020;">⚠ Vung mu nay SUA DUOC tren may nay.</strong><br>
        <span style="color: var(--color-text);">${escapeHtmlSafe(d.action)}</span>
      </div>`);
    }

    const fb = (coverage.fallback_sources || []).filter(f => f.readable);
    if (fb.length) {
      // Ten log Windows deu ket thuc bang '/Operational', nen cat lay doan cuoi
      // thi bon nguon khac nhau hien ra thanh bon dong "Operational" giong het.
      // Phan mang y nghia la doan TRUOC dau gach.
      const shortName = (log) => log.split('/')[0].replace(/^Microsoft-Windows-/, '');
      const items = fb.map(f =>
        `<li><code>${escapeHtmlSafe(shortName(f.log))}</code> — ${escapeHtmlSafe(f.covers)} (${f.records || '?'} ban ghi)</li>`
      ).join('');
      parts.push(`<div style="margin-top: 10px;">
        <strong>Nguon thay the dang doc duoc (khong can nang quyen):</strong>
        <ul style="margin: 6px 0 0 18px; padding: 0;">${items}</ul>
        <div style="margin-top: 6px; font-style: italic;">Day khong phai "da het mu" — day la "mu it hon, va biet phan nao con mu". Moi ban ghi tu cac nguon nay mang co <code>Fallback = true</code>.</div>
      </div>`);
    }

    note.innerHTML = parts.join('');
  }
}

function escapeHtmlSafe(text) {
  return String(text == null ? '' : text)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ============================================================================
// NETWORK MAP PAGE
// ============================================================================

function switchTopology(mode) {
  try {
    currentTopology = mode;
    document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
    const toggleBtn = event?.target?.closest('.toggle-btn');
    if (toggleBtn) toggleBtn.classList.add('active');
    renderNetworkTopology();
  } catch (error) {
    console.error('[ERROR] switchTopology:', error);
  }
}

function renderNetworkTopology() {
  const assets = stateData.assets.assets || [];
  const incidents = stateData.incidents.incidents || [];

  // Calculate stats
  const healthyCount = assets.filter(a => (a.vulnerability_count || 0) <= 10).length;
  const warningCount = assets.filter(a => (a.vulnerability_count || 0) > 10 && (a.vulnerability_count || 0) <= 20).length;
  const criticalCount = assets.filter(a => (a.vulnerability_count || 0) > 20).length;
  const avgRisk = assets.length > 0 ? Math.round(assets.reduce((sum, a) => sum + (a.vulnerability_count || 0), 0) / assets.length) : 0;

  const netHealthy = document.getElementById('net-healthy');
  const netWarning = document.getElementById('net-warning');
  const netCritical = document.getElementById('net-critical');
  const netAvgRisk = document.getElementById('net-avg-risk');

  if (netHealthy) netHealthy.textContent = healthyCount;
  if (netWarning) netWarning.textContent = warningCount;
  if (netCritical) netCritical.textContent = criticalCount;
  if (netAvgRisk) netAvgRisk.textContent = avgRisk;

  // Draw topology to div container (not SVG)
  if (currentTopology === 'physical') {
    drawPhysicalTopology(assets);
  } else {
    drawSecurityTopology(incidents);
  }

  // Render command centers
  renderMCPCommandCenter();
  renderWAAPCommandCenter();
  renderVulnerabilityCenter();
  renderExecutiveActionCenter();
  renderIncidentBoard();
  renderTimeline();
  renderExecutiveScorecard();
}

function renderMCPCommandCenter() {
  const element = document.getElementById('mcp-command-center');
  if (!element) return;

  // Read MCP status from state data or default to ONLINE
  const mcpStatus = stateData.mcp?.status || 'UNVERIFIED';
  const mcpToolCount = stateData.mcp?.tool_count ?? '?';
  const mcpThreatHunting = stateData.mcp?.threat_hunting_active ? 'ACTIVE' : 'UNVERIFIED';
  const mcpDfir = stateData.mcp?.dfir_active ? 'ACTIVE' : 'UNVERIFIED';
  const mcpEventHub = stateData.mcp?.event_hub_active ? 'ACTIVE' : 'UNVERIFIED';
  const mcpLastSync = stateData.mcp?.last_sync || 'chua kiem bao gio';

  element.innerHTML = `
    <div style="background: rgba(139, 92, 246, 0.1); border: 2px solid #8B5CF6; border-radius: 8px; padding: 20px; margin-top: 20px;">
      <div style="color: #8B5CF6; font-weight: bold; font-size: 16px; text-transform: uppercase; margin-bottom: 15px;">🤖 MCP INTELLIGENCE CENTER</div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 13px; font-family: monospace;">
        <div>
          <div style="color: #a0a0a0;">Status</div>
          <div style="color: #00C896; font-weight: bold; font-size: 16px;">● ${mcpStatus}</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">Tool Count</div>
          <div style="color: #8B5CF6; font-weight: bold; font-size: 16px;">${mcpToolCount}</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">Threat Hunting</div>
          <div style="color: ${mcpThreatHunting === 'ACTIVE' ? '#00C896' : '#FF3B5C'}; font-weight: bold;">${mcpThreatHunting}</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">DFIR</div>
          <div style="color: ${mcpDfir === 'ACTIVE' ? '#00C896' : '#FF3B5C'}; font-weight: bold;">${mcpDfir}</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">Event Hub</div>
          <div style="color: ${mcpEventHub === 'ACTIVE' ? '#00C896' : '#FF3B5C'}; font-weight: bold;">${mcpEventHub}</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">Last Sync</div>
          <div style="color: #8B5CF6; font-weight: bold;">${mcpLastSync}</div>
        </div>
      </div>
    </div>
  `;
}

function renderWAAPCommandCenter() {
  const element = document.getElementById('waap-command-center');
  if (!element) return;

  const waapScore = calculateWAAPScore();
  const sslStatus = stateData.waap?.security_summary?.ssl_valid ? '✅' : '❌';
  const wafStatus = stateData.waap?.security_summary?.waf_active ? '✅' : '❌';
  const cdnStatus = stateData.waap?.security_summary?.cdn_active ? '✅' : '❌';

  element.innerHTML = `
    <div style="background: rgba(6, 182, 212, 0.1); border: 2px solid #06B6D4; border-radius: 8px; padding: 20px; margin-top: 20px;">
      <div style="color: #06B6D4; font-weight: bold; font-size: 16px; text-transform: uppercase; margin-bottom: 15px;">🛡️ WAAP COMMAND CENTER</div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 13px; font-family: monospace;">
        <div style="grid-column: 1/-1;">
          <div style="color: #a0a0a0; margin-bottom: 10px;">Security Score</div>
          <div style="font-size: 28px; font-weight: bold; color: ${waapScore >= 80 ? '#00C896' : waapScore >= 60 ? '#FFD93D' : '#FF3B5C'};">${waapScore}/100</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">SSL</div>
          <div style="font-weight: bold; font-size: 14px;">${sslStatus}</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">WAF</div>
          <div style="font-weight: bold; font-size: 14px;">${wafStatus}</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">CDN</div>
          <div style="font-weight: bold; font-size: 14px;">${cdnStatus}</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">Protection</div>
          <div style="font-weight: bold; font-size: 14px;">${stateData.waap?.security_summary?.protection_active ? '✅' : '⚠️'}</div>
        </div>
      </div>
    </div>
  `;
}

function renderVulnerabilityCenter() {
  const element = document.getElementById('vuln-command-center');
  if (!element) return;

  const assets = stateData.assets?.assets || [];
  if (!Array.isArray(assets)) {
    console.error('[RENDER] assets is not an array in renderVulnerabilityCenter');
    return;
  }
  const critVulns = assets.reduce((sum, a) => sum + (a?.critical || 0), 0);
  const highVulns = assets.reduce((sum, a) => sum + (a?.high || 0), 0);
  const medVulns = assets.reduce((sum, a) => sum + (a?.medium || 0), 0);
  const lowVulns = assets.reduce((sum, a) => sum + (a?.low || 0), 0);
  const infoVulns = assets.reduce((sum, a) => sum + (a?.info || 0), 0);
  const totalVulns = assets.reduce((sum, a) => sum + (a?.vulnerability_count || 0), 0);

  element.innerHTML = `
    <div style="background: rgba(249, 115, 22, 0.1); border: 2px solid #F97316; border-radius: 8px; padding: 20px; margin-top: 20px;">
      <div style="color: #F97316; font-weight: bold; font-size: 16px; text-transform: uppercase; margin-bottom: 15px;">🔍 VULNERABILITY CENTER</div>
      <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr; gap: 10px; font-size: 12px; font-family: monospace;">
        <div>
          <div style="color: #a0a0a0;">Total</div>
          <div style="color: #F97316; font-weight: bold; font-size: 18px;">${totalVulns}</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">Critical</div>
          <div style="color: #FF3B5C; font-weight: bold; font-size: 18px;">${critVulns}</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">High</div>
          <div style="color: #FFB347; font-weight: bold; font-size: 18px;">${highVulns}</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">Medium</div>
          <div style="color: #FFD93D; font-weight: bold; font-size: 18px;">${medVulns}</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">Low</div>
          <div style="color: #22ff22; font-weight: bold; font-size: 18px;">${lowVulns}</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">Info</div>
          <div style="color: #888888; font-weight: bold; font-size: 18px;">${infoVulns}</div>
        </div>
      </div>
    </div>
  `;
}

function renderExecutiveActionCenter() {
  const element = document.getElementById('exec-action-center');
  if (!element) return;

  const incidents = stateData.incidents.incidents || [];
  const criticalCount = incidents.filter(i => i.severity === 'CRITICAL').length;

  element.innerHTML = `
    <div style="background: rgba(10, 14, 39, 0.5); border: 2px solid rgba(139, 92, 246, 0.3); border-radius: 8px; padding: 20px; margin-top: 20px;">
      <div style="color: #00C896; font-weight: bold; font-size: 16px; text-transform: uppercase; margin-bottom: 15px;">📊 EXECUTIVE ACTION CENTER</div>

      <div style="margin-bottom: 20px;">
        <div style="color: #00C896; font-weight: bold; margin-bottom: 10px;">✅ COMPLETED</div>
        <div style="color: #a0a0a0; font-size: 12px; margin-left: 20px;">DNS Hardening</div>
        <div style="color: #a0a0a0; font-size: 12px; margin-left: 20px;">Threat Monitoring</div>
        <div style="color: #a0a0a0; font-size: 12px; margin-left: 20px;">Domain Security</div>
      </div>

      <div style="margin-bottom: 20px;">
        <div style="color: #FFB347; font-weight: bold; margin-bottom: 10px;">🟠 IN PROGRESS</div>
        <div style="color: #a0a0a0; font-size: 12px; margin-left: 20px;">WAAP Hardening (75%)</div>
        <div style="color: #a0a0a0; font-size: 12px; margin-left: 20px;">Vulnerability Remediation (45%)</div>
      </div>

      <div style="margin-bottom: 20px;">
        <div style="color: #FFD93D; font-weight: bold; margin-bottom: 10px;">🟡 TODO</div>
        <div style="color: #a0a0a0; font-size: 12px; margin-left: 20px;">Enable WAF</div>
        <div style="color: #a0a0a0; font-size: 12px; margin-left: 20px;">Enable CDN</div>
        <div style="color: #a0a0a0; font-size: 12px; margin-left: 20px;">Patch High-Risk Assets</div>
      </div>

      <div>
        <div style="color: #FF3B5C; font-weight: bold; margin-bottom: 10px;">🔴 IMMEDIATE ACTIONS</div>
        <div style="color: #a0a0a0; font-size: 12px; margin-left: 20px;">Investigate ${criticalCount} Critical Incidents</div>
        <div style="color: #a0a0a0; font-size: 12px; margin-left: 20px;">Analyze WMI Persistence</div>
        <div style="color: #a0a0a0; font-size: 12px; margin-left: 20px;">Review Lateral Movement</div>
        <div style="color: #a0a0a0; font-size: 12px; margin-left: 20px;">Check LSASS Activity</div>
      </div>
    </div>
  `;
}

function drawPhysicalTopology(assets) {
  // Render to topology container (div, not SVG)
  const container = document.getElementById('topology-content');
  if (!container) {
    console.error('[RENDER] topology-content container not found');
    return;
  }

  if (!Array.isArray(assets)) {
    console.error('[RENDER] assets is not an array');
    return;
  }

  let html = `<div style="padding: 20px; font-family: monospace; font-size: 12px; background: rgba(10, 14, 39, 0.5); border-radius: 8px; border: 1px solid rgba(139, 92, 246, 0.2);">`;
  html += `<div style="margin-bottom: 20px; color: #00C896; font-weight: bold; text-transform: uppercase;">🌍 INTERNET</div>`;

  // Gateway
  const gateway = assets.find(a => a?.device_type === 'Router');
  if (gateway) {
    const vulnCount = gateway.vulnerability_count || 0;
    html += `<div style="margin-left: 40px; margin-bottom: 15px; color: #06B6D4;">
      🚪 GATEWAY
      <div style="color: #a0a0a0; margin-left: 20px; font-size: 11px;">
        IP: ${gateway.ip || 'N/A'} | Vulns: ${vulnCount} | Risk: ${vulnCount > 30 ? '🔴 HIGH' : vulnCount > 15 ? '🟠 MEDIUM' : '🟢 LOW'}
      </div>
    </div>`;
  }

  // Assets
  const servers = assets.filter(a => a?.device_type === 'Server');
  if (servers && servers.length > 0) {
    html += `<div style="margin-left: 80px; color: #F97316; font-weight: bold; margin-bottom: 10px;">💻 SERVERS (${servers.length})</div>`;
    servers.slice(0, 5).forEach(server => {
      const vulnCount = server?.vulnerability_count || 0;
      const riskColor = vulnCount > 30 ? '#FF3B5C' : vulnCount > 15 ? '#FFB347' : '#22ff22';
      html += `<div style="margin-left: 100px; margin-bottom: 8px; color: ${riskColor}; font-size: 11px;">
        ${server?.hostname || 'Unknown'} | ${server?.ip || 'N/A'} | Vulns: ${vulnCount}
      </div>`;
    });
  }

  html += `</div>`;
  container.innerHTML = html;
}

function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? [parseInt(result[1], 16), parseInt(result[2], 16), parseInt(result[3], 16)] : [0, 0, 0];
}

function drawSecurityTopology(incidents) {
  const assets = stateData.assets?.assets || [];
  const waapScore = calculateWAAPScore();
  const container = document.getElementById('topology-content');
  if (!container) {
    console.error('[RENDER] topology-content container not found');
    return;
  }

  if (!Array.isArray(incidents)) {
    console.error('[RENDER] incidents is not an array');
    return;
  }

  let html = `<div style="padding: 20px; font-family: monospace; font-size: 13px; line-height: 2; background: rgba(10, 14, 39, 0.5); border-radius: 8px; border: 1px solid rgba(139, 92, 246, 0.2);">`;
  html += `<div style="color: #00C896; text-align: center; font-weight: bold; margin-bottom: 20px; font-size: 14px;">SECURITY OPERATIONS FLOW</div>`;

  html += `<div style="color: #00C896; font-weight: bold;">🌍 INTERNET</div>`;
  html += `<div style="text-align: center; color: #8B5CF6; margin: 10px 0;">↓</div>`;

  html += `<div style="color: #06B6D4; font-weight: bold;">🛡️ WAAP DEFENSE</div>`;
  html += `<div style="color: #a0a0a0; margin-left: 20px; font-size: 12px;">Score: ${waapScore}/100</div>`;
  html += `<div style="text-align: center; color: #8B5CF6; margin: 10px 0;">↓</div>`;

  html += `<div style="color: #F97316; font-weight: bold;">🚪 GATEWAY</div>`;
  const gateway = assets.find(a => a?.device_type === 'Router');
  if (gateway?.ip) {
    html += `<div style="color: #a0a0a0; margin-left: 20px; font-size: 12px;">${gateway.ip}</div>`;
  }
  html += `<div style="text-align: center; color: #8B5CF6; margin: 10px 0;">↓</div>`;

  html += `<div style="color: #FFD93D; font-weight: bold;">💻 ASSETS</div>`;
  html += `<div style="color: #a0a0a0; margin-left: 20px; font-size: 12px;">${assets.length} Devices</div>`;
  html += `<div style="text-align: center; color: #8B5CF6; margin: 10px 0;">↓</div>`;

  html += `<div style="color: #FF3B5C; font-weight: bold;">🚨 INCIDENTS</div>`;
  html += `<div style="color: #a0a0a0; margin-left: 20px; font-size: 12px;">${incidents.length} Open</div>`;
  html += `<div style="text-align: center; color: #8B5CF6; margin: 10px 0;">↓</div>`;

  html += `<div style="color: #8B5CF6; font-weight: bold;">🤖 MCP INTELLIGENCE</div>`;
  const mcpToolCount = stateData.mcp?.tool_count ?? '?';
  const mcpStatus = stateData.mcp?.status || 'UNVERIFIED';
  html += `<div style="color: #a0a0a0; margin-left: 20px; font-size: 12px;">${mcpToolCount} Tools | ${mcpStatus}</div>`;

  html += `</div>`;
  container.innerHTML = html;
}

function calculateWAAPScore() {
  let score = 0;
  if (stateData.waap?.security_summary) {
    if (stateData.waap.security_summary.ssl_valid) score += 60;
    if (stateData.waap.security_summary.waf_active) score += 15;
    if (stateData.waap.security_summary.cdn_active) score += 15;
    if (stateData.waap.security_summary.protection_active) score += 10;
  }
  return score;
}

function showDevicePanel(element, hostname, ip, vulns) {
  const panel = document.getElementById('device-panel');
  const content = document.getElementById('device-panel-content');

  const riskLevel = vulns > 20 ? 'CRITICAL' : vulns > 10 ? 'WARNING' : 'HEALTHY';
  const riskColor = vulns > 20 ? 'var(--color-critical)' : vulns > 10 ? 'var(--color-warning)' : 'var(--color-healthy)';

  content.innerHTML = `
    <div style="margin-bottom: 15px;">
      <div style="font-size: 1.3em; font-weight: bold; color: var(--color-accent); margin-bottom: 10px;">💻 Device Intelligence</div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
      <div>
        <div style="color: var(--color-text-dim); font-size: 0.9em; margin-bottom: 5px;">HOSTNAME</div>
        <div style="font-size: 1.2em; font-weight: bold; color: var(--color-accent);">${hostname}</div>
      </div>
      <div>
        <div style="color: var(--color-text-dim); font-size: 0.9em; margin-bottom: 5px;">IP ADDRESS</div>
        <div style="font-size: 1.2em; font-weight: bold; color: var(--color-text);">${ip}</div>
      </div>
      <div>
        <div style="color: var(--color-text-dim); font-size: 0.9em; margin-bottom: 5px;">VULNERABILITIES</div>
        <div style="font-size: 1.2em; font-weight: bold; color: var(--color-accent);">${vulns}</div>
      </div>
      <div>
        <div style="color: var(--color-text-dim); font-size: 0.9em; margin-bottom: 5px;">RISK LEVEL</div>
        <div style="font-size: 1.2em; font-weight: bold; color: ${riskColor};">${riskLevel}</div>
      </div>
    </div>

    <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid var(--color-border);">
      <button onclick="alert('Detailed view not yet implemented')" style="background: var(--color-accent); color: var(--color-bg); border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold;">
        VIEW DETAILS
      </button>
    </div>
  `;

  panel.classList.add('active');
  panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function closeDevicePanel() {
  document.getElementById('device-panel').classList.remove('active');
}

// ============================================================================
// INCIDENT BOARD PAGE
// ============================================================================

function renderIncidentBoard() {
  try {
    const incidents = stateData.incidents?.incidents || [];
    console.log('[RENDER] renderIncidentBoard - incidents:', incidents.length);
    if (!Array.isArray(incidents)) {
      console.error('[RENDER] incidents is not an array in renderIncidentBoard');
      return;
    }

    const critical = incidents.filter(i => i?.severity === 'CRITICAL');
    const high = incidents.filter(i => i?.severity === 'HIGH');
    const medium = incidents.filter(i => i?.severity === 'MEDIUM');
    const low = incidents.filter(i => i?.severity === 'LOW');

    const boardHtml = `
      <div class="board-column critical">
        <div class="board-header">🔴 CRITICAL (${critical.length})</div>
        ${critical.map(inc => renderIncidentCard(inc)).join('')}
      </div>

      <div class="board-column high">
        <div class="board-header">🟠 HIGH (${high.length})</div>
        ${high.map(inc => renderIncidentCard(inc)).join('')}
      </div>

      <div class="board-column medium">
        <div class="board-header">🟡 MEDIUM (${medium.length})</div>
        ${medium.map(inc => renderIncidentCard(inc)).join('')}
      </div>

      <div class="board-column low">
        <div class="board-header">🟢 LOW (${low.length})</div>
        ${low.map(inc => renderIncidentCard(inc)).join('')}
      </div>
    `;

    const boardEl = document.getElementById('incident-board');
    if (boardEl) boardEl.innerHTML = boardHtml;
  } catch (error) {
    console.error('[ERROR] renderIncidentBoard:', error);
  }
}

function renderIncidentCard(incident) {
  const severityClass = incident.severity.toLowerCase();
  return `
    <div class="incident-card ${severityClass}">
      <div class="incident-id">${incident.incident_id}</div>
      <div class="incident-title">${incident.title}</div>
      <div class="incident-meta">
        <span>Evidence: ${incident.evidence?.length || 0}</span>
        <span class="badge ${getBadgeClass(incident.severity)}">${incident.severity}</span>
      </div>
    </div>
  `;
}

// ============================================================================
// ANALYTICS PAGE
// ============================================================================

function renderAnalytics() {
  try {
    const incidents = stateData.incidents?.incidents || [];
    const assets = stateData.assets?.assets || [];
    if (!Array.isArray(incidents) || !Array.isArray(assets)) {
      console.error('[RENDER] incidents or assets is not an array in renderAnalytics');
      return;
    }

    // Vulnerability Assessment
    const vulnHtml = `
      <div style="font-size: 0.9em;">
        <div style="margin: 10px 0;">Total Vulnerabilities: <span style="color: var(--color-accent); font-weight: bold;">${assets.reduce((sum, a) => sum + (a?.vulnerability_count || 0), 0)}</span></div>
        <div style="margin: 10px 0;">Critical: <span class="severity-critical">${assets.reduce((sum, a) => sum + (a?.critical || 0), 0)}</span></div>
        <div style="margin: 10px 0;">High: <span class="severity-high">${assets.reduce((sum, a) => sum + (a?.high || 0), 0)}</span></div>
        <div style="margin: 10px 0;">Medium: <span class="severity-medium">${assets.reduce((sum, a) => sum + (a?.medium || 0), 0)}</span></div>
        <div style="margin: 10px 0;">Low: <span class="severity-low">${assets.reduce((sum, a) => sum + (a?.low || 0), 0)}</span></div>
      </div>
    `;
    const vulnEl = document.getElementById('vuln-assessment');
    if (vulnEl) vulnEl.innerHTML = vulnHtml;

    // WAAP Assessment - Calculate score from security_summary
    let waapScore = 0;
    if (stateData.waap?.security_summary) {
      if (stateData.waap.security_summary.ssl_valid) waapScore += 60;
      if (stateData.waap.security_summary.waf_active) waapScore += 15;
      if (stateData.waap.security_summary.cdn_active) waapScore += 15;
      if (stateData.waap.security_summary.protection_active) waapScore += 10;
    }
    const sslStatus = stateData.waap?.ssl_status ? stateData.waap.ssl_status.toUpperCase() : 'UNKNOWN';
    const waapHtml = `
      <div style="font-size: 0.9em;">
        <div style="margin: 10px 0;">Health Score: <span style="color: var(--color-accent); font-weight: bold;">${waapScore || '-'}/100</span></div>
        <div style="margin: 10px 0;">SSL Status: <span>${sslStatus}</span></div>
        <div style="margin: 10px 0;">Days to Renewal: <span style="color: var(--color-accent);">${stateData.waap?.days_until_expiry || '-'}</span></div>
        <div style="margin: 10px 0;">WAF Active: <span>${stateData.waap?.security_summary?.waf_active ? 'YES' : 'NO'}</span></div>
        <div style="margin: 10px 0;">CDN Active: <span>${stateData.waap?.security_summary?.cdn_active ? 'YES' : 'NO'}</span></div>
      </div>
    `;
    const waapEl = document.getElementById('waap-assessment');
    if (waapEl) waapEl.innerHTML = waapHtml;

    // Domain Assessment - Calculate DNS Health from dns_complete
    let dnsHealth = 0;
    let dnsChecks = 0;
    if (stateData.domain?.dns_complete) {
      const checks = ['has_nameservers', 'has_a_records', 'has_mx_records', 'has_spf', 'has_dmarc'];
      checks.forEach(check => {
        if (check in stateData.domain.dns_complete) {
          dnsChecks++;
          if (stateData.domain.dns_complete[check]) dnsHealth++;
        }
      });
    }
    const dnsPercent = dnsChecks > 0 ? Math.round((dnsHealth / dnsChecks) * 100) : '-';
    const domainHtml = `
      <div style="font-size: 0.9em;">
        <div style="margin: 10px 0;">DNS Health: <span style="color: var(--color-accent); font-weight: bold;">${dnsPercent !== '-' ? dnsPercent + '%' : '-'}</span></div>
        <div style="margin: 10px 0;">Domain: <span>${stateData.domain?.domain || 'UNKNOWN'}</span></div>
        <div style="margin: 10px 0;">SSL Expiry: <span style="color: var(--color-accent);">${stateData.domain?.days_until_expiry || '-'} days</span></div>
        <div style="margin: 10px 0;">Nameservers: <span>${stateData.domain?.nameservers?.length || 0} configured</span></div>
      </div>
    `;
    const domainEl = document.getElementById('domain-assessment');
    if (domainEl) domainEl.innerHTML = domainHtml;

    // Executive Analytics - Vulnerability Severity Chart
    const critVulns = assets.reduce((sum, a) => sum + (a?.critical || 0), 0);
    const highVulns = assets.reduce((sum, a) => sum + (a?.high || 0), 0);
    const medVulns = assets.reduce((sum, a) => sum + (a?.medium || 0), 0);
    const lowVulns = assets.reduce((sum, a) => sum + (a?.low || 0), 0);

    const chartCrit = document.getElementById('chart-vuln-crit');
    const chartHigh = document.getElementById('chart-vuln-high');
    const chartMed = document.getElementById('chart-vuln-med');
    const chartLow = document.getElementById('chart-vuln-low');

    if (chartCrit) chartCrit.textContent = critVulns;
    if (chartHigh) chartHigh.textContent = highVulns;
    if (chartMed) chartMed.textContent = medVulns;
    if (chartLow) chartLow.textContent = lowVulns;

    // WAAP Radar
    const sslValid = stateData.waap?.security_summary?.ssl_valid ? '✓' : '✗';
    const wafActive = stateData.waap?.security_summary?.waf_active ? '✓' : '✗';
    const cdnActive = stateData.waap?.security_summary?.cdn_active ? '✓' : '✗';
    const protActive = stateData.waap?.security_summary?.protection_active ? '✓' : '✗';

    const radarSsl = document.getElementById('radar-ssl');
    const radarWaf = document.getElementById('radar-waf');
    const radarCdn = document.getElementById('radar-cdn');
    const radarProt = document.getElementById('radar-prot');

    if (radarSsl) radarSsl.textContent = sslValid;
    if (radarWaf) radarWaf.textContent = wafActive;
    if (radarCdn) radarCdn.textContent = cdnActive;
    if (radarProt) radarProt.textContent = protActive;

    // SOC Score Gauge
    const riskScore = stateData.risk?.overall_score || 0;
    const dnsScore = dnsPercent !== '-' ? parseInt(dnsPercent) : 0;

    const gaugeRisk = document.getElementById('gauge-risk');
    const gaugeRiskBar = document.getElementById('gauge-risk-bar');
    const gaugeWaap = document.getElementById('gauge-waap');
    const gaugeWaapBar = document.getElementById('gauge-waap-bar');
    const gaugeDns = document.getElementById('gauge-dns');
    const gaugeDnsBar = document.getElementById('gauge-dns-bar');

    if (gaugeRisk) gaugeRisk.textContent = riskScore + '/100';
    if (gaugeRiskBar) gaugeRiskBar.style.width = riskScore + '%';
    if (gaugeWaap) gaugeWaap.textContent = waapScore + '/100';
    if (gaugeWaapBar) gaugeWaapBar.style.width = waapScore + '%';
    if (gaugeDns) gaugeDns.textContent = dnsScore + '%';
    if (gaugeDnsBar) gaugeDnsBar.style.width = dnsScore + '%';
  } catch (error) {
    console.error('[ERROR] renderAnalytics:', error);
  }
}

// ============================================================================
// EXECUTIVE SCORECARD PAGE
// ============================================================================

function renderExecutiveScorecard() {
  try {
    const incidents = stateData.incidents?.incidents || [];
    const assets = stateData.assets?.assets || [];
    const riskScore = stateData.risk?.overall_score || 0;
    console.log('[RENDER] renderExecutiveScorecard:', { incidents: incidents.length, assets: assets.length, riskScore });

    // Calculate metrics
    const totalVulns = assets.reduce((sum, a) => sum + (a?.vulnerability_count || 0), 0);
    const critVulns = assets.reduce((sum, a) => sum + (a?.critical || 0), 0);
    const highVulns = assets.reduce((sum, a) => sum + (a?.high || 0), 0);
    const criticalIncidents = incidents.filter(i => i?.severity === 'CRITICAL').length;
    const highIncidents = incidents.filter(i => i?.severity === 'HIGH').length;
    const atRiskAssets = assets.filter(a => (a?.vulnerability_count || 0) > 10).length;

    // Calculate WAAP Score
    let waapScore = 0;
    if (stateData.waap?.security_summary) {
      if (stateData.waap.security_summary.ssl_valid) waapScore += 60;
      if (stateData.waap.security_summary.waf_active) waapScore += 15;
      if (stateData.waap.security_summary.cdn_active) waapScore += 15;
      if (stateData.waap.security_summary.protection_active) waapScore += 10;
    }

    // Calculate DNS Health
    let dnsHealth = 0;
    let dnsChecks = 0;
    if (stateData.domain?.dns_complete) {
      const checks = ['has_nameservers', 'has_a_records', 'has_mx_records', 'has_spf', 'has_dmarc'];
      checks.forEach(check => {
        if (check in stateData.domain.dns_complete) {
          dnsChecks++;
          if (stateData.domain.dns_complete[check]) dnsHealth++;
        }
      });
    }
    const dnsPercent = dnsChecks > 0 ? Math.round((dnsHealth / dnsChecks) * 100) : 0;

    // Update scorecard values
    const scoreRisk = document.getElementById('score-risk');
    const scoreRiskLevel = document.getElementById('score-risk-level');
    const scoreWaap = document.getElementById('score-waap');
    const scoreDns = document.getElementById('score-dns');
    const scoreAssets = document.getElementById('score-assets');
    const scoreIncidents = document.getElementById('score-incidents');
    const scoreVulns = document.getElementById('score-vulns');
    const scoreThreat = document.getElementById('score-threat');
    const scoreThreatDetail = document.getElementById('score-threat-detail');

    if (scoreRisk) scoreRisk.textContent = riskScore;
    if (scoreRiskLevel) scoreRiskLevel.textContent = getThreatLevel(riskScore);
    if (scoreWaap) scoreWaap.textContent = waapScore > 0 ? waapScore : '-';
    if (scoreDns) scoreDns.textContent = dnsPercent + '%';
    if (scoreAssets) scoreAssets.textContent = assets.length;
    if (scoreIncidents) scoreIncidents.textContent = incidents.length;
    if (scoreVulns) scoreVulns.textContent = totalVulns;
    if (scoreThreat) scoreThreat.textContent = getThreatLevel(riskScore);
    if (scoreThreatDetail) scoreThreatDetail.textContent = getRiskDetail(riskScore);

    // Summary metrics
    const summaryRisk = document.getElementById('summary-risk');
    const summaryAtRisk = document.getElementById('summary-at-risk');
    const summaryCritVulns = document.getElementById('summary-crit-vulns');
    const summaryUrgent = document.getElementById('summary-urgent');
    const summaryDns = document.getElementById('summary-dns');
    const summaryWaap = document.getElementById('summary-waap');

    if (summaryRisk) summaryRisk.textContent = riskScore + '/100';
    if (summaryAtRisk) summaryAtRisk.textContent = atRiskAssets + ' of ' + assets.length;
    if (summaryCritVulns) summaryCritVulns.textContent = critVulns;
    if (summaryUrgent) summaryUrgent.textContent = criticalIncidents + ' Critical, ' + highIncidents + ' High';
    if (summaryDns) summaryDns.textContent = dnsPercent + '%';
    if (summaryWaap) summaryWaap.textContent = waapScore > 0 ? waapScore + '/100' : 'Not Configured';

    // Recommendations
    const recommendations = [];
    if (critVulns > 0) recommendations.push('🔴 Address ' + critVulns + ' critical vulnerabilities immediately');
    if (riskScore > 70) recommendations.push('🔴 Risk score is HIGH - escalate to security team');
    if (dnsPercent < 100) recommendations.push('🟠 Complete DNS security configuration (currently ' + dnsPercent + '%)');
    if (waapScore < 80) recommendations.push('🟠 Enhance WAAP protection - score at ' + waapScore + '/100');
    if (highVulns > 5) recommendations.push('🟡 High severity vulnerabilities require remediation planning');
    if (atRiskAssets > 3) recommendations.push('🟡 Multiple assets at risk - prioritize security patching');
    if (criticalIncidents > 0) recommendations.push('🔴 ' + criticalIncidents + ' critical incidents require immediate response');

    if (recommendations.length === 0) {
      recommendations.push('✅ Security posture is healthy - continue monitoring');
    }

    const recHtml = recommendations.slice(0, 5).map(rec => `
      <div style="background: rgba(10, 14, 39, 0.5); border-left: 3px solid var(--color-accent); padding: 12px 15px; border-radius: 4px; margin-bottom: 10px;">
        ${rec}
      </div>
    `).join('');

    const recEl = document.getElementById('exec-recommendations');
    if (recEl) recEl.innerHTML = recHtml;
  } catch (error) {
    console.error('[ERROR] renderExecutiveScorecard:', error);
  }
}

function getRiskDetail(score) {
  switch (getThreatLevel(score)) {
    case 'CRITICAL': return 'Immediate action required';
    case 'HIGH': return 'High priority remediation needed';
    case 'MEDIUM': return 'Medium priority - plan remediation';
    default: return 'Acceptable risk level';
  }
}

// ============================================================================
// TIMELINE PAGE
// ============================================================================

function renderTimeline() {
  try {
    const alerts = stateData.alerts?.sent_alerts || [];
    const incidents = stateData.incidents?.incidents || [];
    console.log('[RENDER] renderTimeline - incidents:', incidents.length, 'alerts:', alerts.length);

    const events = [
      ...alerts.map(a => ({
        timestamp: a?.sent_at,
        type: 'Alert Sent',
        title: `${a?.severity || 'UNKNOWN'} - ${a?.title || 'N/A'}`,
        severity: a?.severity
      })),
      ...incidents.slice(0, 5).map(i => ({
        timestamp: i?.created_at,
        type: 'Incident Created',
        title: i?.title || 'N/A',
        severity: i?.severity
      }))
    ].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, 20);

    const timelineHtml = events.map(evt => `
      <div class="timeline-item">
        <div class="timeline-marker"></div>
        <div class="timeline-content">
          <div class="timeline-time">${new Date(evt.timestamp).toLocaleString()}</div>
          <div style="color: var(--color-accent); font-weight: bold; margin-top: 5px;">${evt.type}</div>
          <div class="timeline-event" style="color: ${getSeverityColor(evt.severity)};">${evt.title}</div>
        </div>
      </div>
    `).join('');

    const timelineEl = document.getElementById('timeline');
    if (timelineEl) {
      timelineEl.innerHTML = timelineHtml || '<div style="color: var(--color-text-dim);">No events recorded</div>';
    }
  } catch (error) {
    console.error('[ERROR] renderTimeline:', error);
  }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// risk_score.json is risk-ascending: a higher overall_score means more danger.
// The engine also publishes risk_level, which carries the severity floor that
// raw thresholds cannot reproduce - so prefer it and keep the bands as fallback.
const RISK_EMOJI = { CRITICAL: '🔴', HIGH: '🟠', MEDIUM: '🟡', LOW: '🟢' };

function bandFromScore(score) {
  if (score >= 80) return 'CRITICAL';
  if (score >= 60) return 'HIGH';
  if (score >= 40) return 'MEDIUM';
  return 'LOW';
}

function getThreatLevel(score) {
  return stateData.risk?.risk_level || bandFromScore(score);
}

function getRiskLevel(score) {
  const level = getThreatLevel(score);
  return `${RISK_EMOJI[level] || '⚪'} ${level}`;
}

function getSeverityColor(severity) {
  switch (severity) {
    case 'CRITICAL': return 'var(--color-critical)';
    case 'HIGH': return 'var(--color-high)';
    case 'MEDIUM': return 'var(--color-medium)';
    case 'LOW': return 'var(--color-low)';
    default: return 'var(--color-text)';
  }
}

function getBadgeClass(severity) {
  switch (severity) {
    case 'CRITICAL': return 'badge-critical';
    case 'HIGH': return 'badge-high';
    default: return 'badge-healthy';
  }
}

function setRefreshInterval(ms) {
  refreshInterval = parseInt(ms);
  clearInterval(window.refreshTimer);
  startAutoRefresh();
}

function startAutoRefresh() {
  window.refreshTimer = setInterval(() => {
    loadAllData();
    try {
      const activePage = document.querySelector('.page.active');
      if (activePage) {
        const pageId = activePage.id;
        if (pageId === 'overview') renderOverviewPage();
        else if (pageId === 'incidents') renderIncidentBoard();
      }
    } catch (error) {
      console.error('[ERROR] Auto-refresh update:', error);
    }
  }, refreshInterval);
}

// ============================================================================
// ASSET COMMAND CENTER
// ============================================================================

function renderAssetCommandCenter() {
  try {
    // Sprint 11: bo nhanh `|| stateData.assets?.all_assets`. Luoc do kep da
    // duoc hop nhat ve khoa `assets`; giu lai nhanh du phong chinh la chua san
    // mot cho cho luoc do thu hai quay lai ma khong ai thay.
    const assets = stateData.assets?.assets || [];
    const shadowAssets = stateData.shadowAssets?.shadows || [];
    const risk = stateData.risk || {};

    // Calculate metrics
    //
    // Chi tinh trung binh tren nhung tai san DA duoc cham. `|| 0` cua ban cu
    // bien "chua cham" thanh diem 0, keo trung binh xuong va bao mot mang binh
    // thuong la khong dang tin — mot con so sai tu tin trong nhu mot ket luan.
    const scored = assets.filter(a => typeof a?.trust_score === 'number');
    const avgTrust = scored.length
      ? Math.round(scored.reduce((sum, a) => sum + a.trust_score, 0) / scored.length)
      : null;

    // `status` KHONG co trong luoc do chinh thuc cua assets.json. Ban cu doc no
    // roi ket luan moi thiet bi deu Offline — 11 thiet bi cung "🔴 Offline"
    // tren mot mang dang chay. Nguon duy nhat biet thiet bi nao dang tra loi la
    // bang ARP, va no nam trong shadow_assets.json.
    const arpSeen = new Set([
      ...(stateData.shadowAssets?.shadows || []).map(s => s.ip),
      ...assets.map(a => a?.ip).filter(ip =>
        !(stateData.shadowAssets?.unverified_assets || []).some(u => u.ip === ip))
    ].filter(Boolean));
    const liveCount = assets.filter(a => arpSeen.has(a?.ip)).length;

    // Update KPIs
    const els = {
      'assets-total': assets.length,
      'assets-online': `${liveCount} tra loi ARP`,
      'assets-trust': avgTrust === null ? 'chua cham' : avgTrust,
      'assets-risk': risk.overall_score || 0,
      'assets-risk-level': getRiskLevel(risk.overall_score || 0),
      'assets-shadow': shadowAssets.length
    };

    Object.entries(els).forEach(([id, value]) => {
      const el = document.getElementById(id);
      if (el) el.textContent = value;
    });

    // Populate asset table
    const tbody = document.getElementById('assets-table-body');
    if (tbody) {
      const rows = assets.slice(0, 50).map(asset => {
        // `device_type` la ten truong that; ban cu doc `type` va in "Unknown"
        // cho moi dong, ke ca khi loai thiet bi da duoc nhan dang ro rang.
        const kind = asset?.device_type || 'Khong ro';
        const score = typeof asset?.trust_score === 'number' ? asset.trust_score : null;
        const basis = asset?.trust_basis?.points_available;
        // Diem tran trui giau mat co so cham no. 92 tren 60 diem kha dung khong
        // cung nghia voi 92 tren 100 — va cot nay la noi duy nhat nguoi doc co
        // co hoi thay dieu do.
        const trustCell = score === null
          ? '<span style="color: var(--color-text-dim);">chua cham</span>'
          : `${score}<span style="color: var(--color-text-dim); font-size: 0.85em;">${basis ? ` /${basis}đ` : ''}</span>`;
        const live = arpSeen.has(asset?.ip);
        return `
        <tr style="border-bottom: 1px solid var(--color-border);">
          <td style="padding: 10px;">${asset?.ip || 'N/A'}</td>
          <td style="padding: 10px;">${kind}</td>
          <td style="padding: 10px; color: var(--color-accent);">${trustCell}</td>
          <td style="padding: 10px;">${live ? '🟢 Tra loi ARP' : '<span style="color: var(--color-text-dim);">⚪ Chua xac minh</span>'}</td>
        </tr>`;
      }).join('');
      // Rong o day nghia la doc duoc assets.json va trong do khong co thiet bi
      // nao — khac han voi khong doc duoc, thu ma asset_store bay gio bao loi.
      tbody.innerHTML = rows || '<tr><td colspan="4" style="padding: 10px; text-align: center;">Doc duoc assets.json, khong co thiet bi nao trong do</td></tr>';
    }
  } catch (error) {
    console.error('[ERROR] renderAssetCommandCenter:', error);
  }
}

// ============================================================================
// THREAT INTELLIGENCE
// ============================================================================

function renderThreatIntelligence() {
  try {
    const persistence = stateData.threatPersistence?.indicators || [];
    const lateral = stateData.threatLateral?.indicators || [];
    const credential = stateData.threatCredential?.indicators || [];
    const processes = stateData.threatProcesses?.indicators || [];

    const allIndicators = [...persistence, ...lateral, ...credential, ...processes];
    const critical = allIndicators.filter(i => i?.severity === 'CRITICAL').length;
    const high = allIndicators.filter(i => i?.severity === 'HIGH').length;

    // Update KPIs
    const els = {
      'threats-total': allIndicators.length,
      'threats-critical': critical,
      'threats-high': high,
      'threats-categories': new Set([...persistence.map(i => 'Persistence'), ...lateral.map(i => 'Lateral'), ...credential.map(i => 'Credential'), ...processes.map(i => 'Process')]).size
    };

    Object.entries(els).forEach(([id, value]) => {
      const el = document.getElementById(id);
      if (el) el.textContent = value;
    });

    // Render threat categories
    const renderThreatList = (indicators, containerId) => {
      const el = document.getElementById(containerId);
      if (el) {
        const html = indicators.slice(0, 10).map(ind => `
          <div style="padding: 8px; border-bottom: 1px solid var(--color-border); font-size: 0.85em;">
            <span class="badge badge-${ind?.severity?.toLowerCase() || 'medium'}">${ind?.severity || 'MEDIUM'}</span>
            <div style="color: var(--color-text-dim); margin-top: 4px;">${ind?.type || ind?.process || ind?.pattern || 'Unknown'}</div>
          </div>
        `).join('');
        el.innerHTML = html || '<div style="padding: 10px; color: var(--color-text-dim);">No indicators detected</div>';
      }
    };

    renderThreatList(persistence, 'threats-persistence');
    renderThreatList(lateral, 'threats-lateral');
    renderThreatList(credential, 'threats-credential');
    renderThreatList(processes, 'threats-processes');
  } catch (error) {
    console.error('[ERROR] renderThreatIntelligence:', error);
  }
}

// ============================================================================
// DAILY BRIEF ARCHIVE
// ============================================================================

async function loadBriefArchive() {
  const countEl = document.getElementById('brief-count');
  const updatedEl = document.getElementById('brief-updated');

  try {
    const res = await fetch('/api/daily-brief/list');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    const briefs = data.briefs || [];
    stateData.briefs = briefs;

    if (countEl) countEl.textContent = `${briefs.length} available`;
    if (updatedEl) updatedEl.textContent = briefs[0]?.date || '-';
  } catch (error) {
    console.error('[ERROR] loadBriefArchive:', error);
    if (countEl) countEl.textContent = 'unavailable';
    if (updatedEl) updatedEl.textContent = '-';
  }
}

async function fetchBrief(date) {
  const res = await fetch(`/api/daily-brief/${date}`);
  if (!res.ok) throw new Error(`Brief ${date} unavailable (HTTP ${res.status})`);
  return res.json();
}

function renderDailyBriefArchive() {
  try {
    const risk = stateData.risk || {};
    const incidents = stateData.incidents?.incidents || [];

    // Update KPIs
    const els = {
      'brief-score': risk.overall_score || 0,
      'brief-score-date': new Date(risk.timestamp).toLocaleDateString() || '-',
      'brief-risk': getRiskLevel(risk.overall_score || 0)
    };

    Object.entries(els).forEach(([id, value]) => {
      const el = document.getElementById(id);
      if (el) el.textContent = value;
    });

    // Brief count/latest come from the archive on disk, not a hardcoded value
    loadBriefArchive();

    // Render recommendations
    const actionsEl = document.getElementById('brief-actions');
    if (actionsEl) {
      const criticalCount = incidents.filter(i => i?.severity === 'CRITICAL').length;
      const highCount = incidents.filter(i => i?.severity === 'HIGH').length;
      const recommendations = [];

      if (criticalCount > 0) recommendations.push(`Investigate ${criticalCount} critical incidents`);
      if (highCount > 0) recommendations.push(`Review ${highCount} high-priority issues`);
      // Risk-ascending: a HIGH score is the alarming case, not a low one.
      if ((risk.overall_score || 0) >= 60) recommendations.push(`Risk score ${risk.overall_score}/100 - take immediate action`);
      if (recommendations.length === 0) recommendations.push('System operating normally');

      const html = recommendations.map((rec, idx) => `
        <div style="padding: 10px; border-bottom: 1px solid var(--color-border); display: flex; align-items: center;">
          <span style="color: var(--color-accent); margin-right: 10px;">→</span>
          <span>${rec}</span>
        </div>
      `).join('');
      actionsEl.innerHTML = html;
    }

    // Render timeline
    const timelineEl = document.getElementById('brief-timeline');
    if (timelineEl) {
      const recentIncidents = incidents.slice(0, 5);
      const html = recentIncidents.map(inc => `
        <div class="timeline-item">
          <div class="timeline-marker"></div>
          <div class="timeline-content">
            <div class="timeline-time">${new Date(inc?.created_at).toLocaleTimeString()}</div>
            <div class="timeline-event">${inc?.title || 'Incident'} <span class="badge badge-${inc?.severity?.toLowerCase()}">${inc?.severity}</span></div>
          </div>
        </div>
      `).join('');
      timelineEl.innerHTML = html || '<div style="color: var(--color-text-dim); padding: 10px;">No recent events</div>';
    }
  } catch (error) {
    console.error('[ERROR] renderDailyBriefArchive:', error);
  }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', init);

// DEPLOYMENT TRIGGER: 1788805876394940200
