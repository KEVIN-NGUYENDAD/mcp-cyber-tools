// ============================================================================
// SENTINELOPS - SOC COMMAND CENTER
// Real-time dashboard reading from state files
// ============================================================================

let stateData = {
  assets: null,
  incidents: null,
  risk: null,
  health: null,
  defender: null,
  firewall: null,
  alerts: null,
  waap: null,
  domain: null
};

let currentTopology = 'physical';
let refreshInterval = 30000;

// ============================================================================
// INITIALIZATION
// ============================================================================

async function init() {
  console.log('[INIT] SentinelOps starting...');
  await loadAllData();
  renderOverviewPage();
  if (typeof setupEventListeners === 'function') setupEventListeners();
  startAutoRefresh();
  console.log('[INIT] SentinelOps ready');
}

// ============================================================================
// DATA LOADING
// ============================================================================

async function loadAllData() {
  try {
    // Load from public API endpoint or local JSON
    const baseUrl = '/api/state';

    const [assets, incidents, risk, health, defender, firewall, alerts, waap, domain] = await Promise.allSettled([
      fetch(`${baseUrl}/assets.json`).then(r => r.json()).catch(() => ({ assets: [] })),
      fetch(`${baseUrl}/incidents.json`).then(r => r.json()).catch(() => ({ incidents: [] })),
      fetch(`${baseUrl}/risk_score.json`).then(r => r.json()).catch(() => ({ overall_score: 0 })),
      fetch(`${baseUrl}/system_health.json`).then(r => r.json()).catch(() => ({})),
      fetch(`${baseUrl}/defender_status.json`).then(r => r.json()).catch(() => ({})),
      fetch(`${baseUrl}/firewall_status.json`).then(r => r.json()).catch(() => ({})),
      fetch(`${baseUrl}/notification_history.json`).then(r => r.json()).catch(() => ({ sent_alerts: [] })),
      fetch(`${baseUrl}/waap_status.json`).then(r => r.json()).catch(() => ({})),
      fetch(`${baseUrl}/domain_status.json`).then(r => r.json()).catch(() => ({}))
    ]);

    stateData.assets = assets.value || { assets: [] };
    stateData.incidents = incidents.value || { incidents: [] };
    stateData.risk = risk.value || { overall_score: 0 };
    stateData.health = health.value || {};
    stateData.defender = defender.value || {};
    stateData.firewall = firewall.value || {};
    stateData.alerts = alerts.value || { sent_alerts: [] };
    stateData.waap = waap.value || {};
    stateData.domain = domain.value || {};

    updateLastUpdate();
    console.log('[DATA] Loaded:', Object.keys(stateData).length, 'data sources');
  } catch (error) {
    console.error('[ERROR] Loading data:', error);
  }
}

function updateLastUpdate() {
  const now = new Date();
  const time = now.toLocaleTimeString();
  document.getElementById('lastUpdate').textContent = `Last update: ${time}`;
}

// ============================================================================
// PAGE NAVIGATION
// ============================================================================

function switchPage(pageName) {
  // Hide all pages
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

  // Show selected page
  document.getElementById(pageName).classList.add('active');

  // Update nav
  document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
  event.target.classList.add('active');

  // Render page content
  switch (pageName) {
    case 'overview':
      renderOverviewPage();
      break;
    case 'network':
      setTimeout(() => renderNetworkTopology(), 100);
      break;
    case 'incidents':
      renderIncidentBoard();
      break;
    case 'analytics':
      renderAnalytics();
      break;
    case 'scorecard':
      renderExecutiveScorecard();
      break;
    case 'history':
      renderTimeline();
      break;
  }
}

// ============================================================================
// OVERVIEW PAGE
// ============================================================================

function renderOverviewPage() {
  if (!stateData.assets || !stateData.incidents || !stateData.risk) {
    console.log('[WARN] Data not ready');
    return;
  }

  const assets = stateData.assets.assets || [];
  const incidents = stateData.incidents.incidents || [];
  const riskScore = stateData.risk.overall_score || 0;
  const alerts = stateData.alerts.sent_alerts || [];

  // Calculate metrics
  const criticalIncidents = incidents.filter(i => i.severity === 'CRITICAL').length;
  const healthyAssets = assets.filter(a => (a.vulnerability_count || 0) <= 10).length;
  const avgRisk = assets.length > 0 ? Math.round(assets.reduce((sum, a) => sum + (a.vulnerability_count || 0), 0) / assets.length) : 0;

  // Update KPIs
  document.getElementById('kpi-assets').textContent = assets.length;
  document.getElementById('kpi-assets-sub').textContent = `${healthyAssets} healthy`;

  document.getElementById('kpi-incidents').textContent = incidents.length;
  document.getElementById('kpi-incidents-sub').textContent = `${criticalIncidents} critical`;

  document.getElementById('kpi-risk').textContent = riskScore;
  document.getElementById('kpi-risk-sub').textContent = getRiskLevel(riskScore);

  // Calculate WAAP Health Score from security_summary
  let waapScore = 0;
  if (stateData.waap.security_summary) {
    if (stateData.waap.security_summary.ssl_valid) waapScore += 60;
    if (stateData.waap.security_summary.waf_active) waapScore += 15;
    if (stateData.waap.security_summary.cdn_active) waapScore += 15;
    if (stateData.waap.security_summary.protection_active) waapScore += 10;
  }
  document.getElementById('kpi-waap').textContent = waapScore > 0 ? waapScore : '-';

  // Calculate DNS Health from dns_complete
  let dnsHealth = 0;
  let dnsChecks = 0;
  if (stateData.domain.dns_complete) {
    const checks = ['has_nameservers', 'has_a_records', 'has_mx_records', 'has_spf', 'has_dmarc'];
    checks.forEach(check => {
      if (check in stateData.domain.dns_complete) {
        dnsChecks++;
        if (stateData.domain.dns_complete[check]) dnsHealth++;
      }
    });
  }
  const dnsPercent = dnsChecks > 0 ? Math.round((dnsHealth / dnsChecks) * 100) : '-';
  document.getElementById('kpi-dns').textContent = dnsPercent !== '-' ? dnsPercent + '%' : '-';

  const minutesOld = Math.round((Date.now() - new Date(stateData.assets.timestamp || Date.now())) / 60000);
  document.getElementById('kpi-fresh').textContent = minutesOld;
  document.getElementById('kpi-fresh-sub').textContent = minutesOld > 5 ? 'STALE' : 'FRESH';

  // Mission Control
  document.getElementById('mc-threat').textContent = getThreatLevel(riskScore);
  document.getElementById('mc-assets').textContent = assets.length;
  document.getElementById('mc-incidents').textContent = incidents.length;
  document.getElementById('mc-critical').textContent = criticalIncidents;
  document.getElementById('mc-risk').textContent = riskScore + '/100';
  document.getElementById('mc-fresh').textContent = minutesOld + ' min';

  // Recent Activity
  const recentIncidents = incidents.slice(0, 3);
  const activityHtml = recentIncidents.length > 0
    ? recentIncidents.map(inc => `
        <div style="padding: 10px 0; border-bottom: 1px solid var(--color-border); font-size: 0.9em;">
          <span class="badge ${getBadgeClass(inc.severity)}">${inc.severity}</span>
          <span style="margin-left: 10px; color: var(--color-accent);">${inc.incident_id}</span>
          <div style="color: var(--color-text-dim); margin-top: 5px;">${inc.title}</div>
        </div>
      `).join('')
    : '<div style="color: var(--color-text-dim);">No recent incidents</div>';

  document.getElementById('recent-activity').innerHTML = activityHtml;

  // Alert Status
  const criticalAlerts = alerts.filter(a => a.severity === 'CRITICAL').length;
  const highAlerts = alerts.filter(a => a.severity === 'HIGH').length;
  const lastAlert = alerts.length > 0 ? new Date(alerts[0].sent_at).toLocaleString() : '-';

  document.getElementById('alerts-total').textContent = alerts.length;
  document.getElementById('alerts-last').textContent = lastAlert;
  document.getElementById('alerts-critical').textContent = criticalAlerts;
  document.getElementById('alerts-high').textContent = highAlerts;

  // Update Executive Security Row
  updateExecutiveSecurityRow(assets);
}

function updateExecutiveSecurityRow(assets) {
  // WAAP Security
  let waapScore = 0;
  if (stateData.waap.security_summary) {
    if (stateData.waap.security_summary.ssl_valid) waapScore += 60;
    if (stateData.waap.security_summary.waf_active) waapScore += 15;
    if (stateData.waap.security_summary.cdn_active) waapScore += 15;
    if (stateData.waap.security_summary.protection_active) waapScore += 10;
  }
  const sslStatus = stateData.waap.ssl_status ? stateData.waap.ssl_status.toUpperCase() : 'UNKNOWN';
  const wafStatus = stateData.waap.security_summary?.waf_active ? '✓ ACTIVE' : '✗ INACTIVE';
  const cdnStatus = stateData.waap.security_summary?.cdn_active ? '✓ ACTIVE' : '✗ INACTIVE';
  const certDays = stateData.waap.days_until_expiry || '-';

  document.getElementById('exec-waap-score').textContent = waapScore > 0 ? waapScore + '/100' : '-';
  document.getElementById('exec-waap-ssl').textContent = sslStatus;
  document.getElementById('exec-waap-waf').textContent = wafStatus;
  document.getElementById('exec-waap-cdn').textContent = cdnStatus;
  document.getElementById('exec-waap-cert').textContent = certDays + ' days';

  // Vulnerability Center
  const totalVulns = assets.reduce((sum, a) => sum + (a.vulnerability_count || 0), 0);
  const critVulns = assets.reduce((sum, a) => sum + (a.critical || 0), 0);
  const highVulns = assets.reduce((sum, a) => sum + (a.high || 0), 0);
  const medVulns = assets.reduce((sum, a) => sum + (a.medium || 0), 0);
  const lowVulns = assets.reduce((sum, a) => sum + (a.low || 0), 0);

  document.getElementById('exec-vuln-total').textContent = totalVulns;
  document.getElementById('exec-vuln-assets').textContent = assets.length;
  document.getElementById('exec-vuln-crit').textContent = critVulns;
  document.getElementById('exec-vuln-high').textContent = highVulns;
  document.getElementById('exec-vuln-med').textContent = medVulns;
  document.getElementById('exec-vuln-low').textContent = lowVulns;

  // MCP Intelligence
  document.getElementById('exec-mcp-queue').textContent = '0';
}

// ============================================================================
// NETWORK MAP PAGE
// ============================================================================

function switchTopology(mode) {
  currentTopology = mode;
  document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
  event.target.classList.add('active');
  renderNetworkTopology();
}

function renderNetworkTopology() {
  const assets = stateData.assets.assets || [];
  const incidents = stateData.incidents.incidents || [];

  // Calculate stats
  const healthyCount = assets.filter(a => (a.vulnerability_count || 0) <= 10).length;
  const warningCount = assets.filter(a => (a.vulnerability_count || 0) > 10 && (a.vulnerability_count || 0) <= 20).length;
  const criticalCount = assets.filter(a => (a.vulnerability_count || 0) > 20).length;
  const avgRisk = assets.length > 0 ? Math.round(assets.reduce((sum, a) => sum + (a.vulnerability_count || 0), 0) / assets.length) : 0;

  document.getElementById('net-healthy').textContent = healthyCount;
  document.getElementById('net-warning').textContent = warningCount;
  document.getElementById('net-critical').textContent = criticalCount;
  document.getElementById('net-avg-risk').textContent = avgRisk;

  // Draw topology
  const svg = document.getElementById('topology-svg');
  svg.innerHTML = '';

  if (currentTopology === 'physical') {
    drawPhysicalTopology(svg, assets);
  } else {
    drawSecurityTopology(svg, incidents);
  }

  // Render command centers
  renderMCPCommandCenter();
  renderWAAPCommandCenter();
  renderVulnerabilityCenter();
  renderExecutiveActionCenter();
}

function renderMCPCommandCenter() {
  const element = document.getElementById('mcp-command-center');
  if (!element) return;

  element.innerHTML = `
    <div style="background: rgba(139, 92, 246, 0.1); border: 2px solid #8B5CF6; border-radius: 8px; padding: 20px; margin-top: 20px;">
      <div style="color: #8B5CF6; font-weight: bold; font-size: 16px; text-transform: uppercase; margin-bottom: 15px;">🤖 MCP INTELLIGENCE CENTER</div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 13px; font-family: monospace;">
        <div>
          <div style="color: #a0a0a0;">Status</div>
          <div style="color: #00C896; font-weight: bold; font-size: 16px;">● ONLINE</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">Tool Count</div>
          <div style="color: #8B5CF6; font-weight: bold; font-size: 16px;">90+</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">Threat Hunting</div>
          <div style="color: #00C896; font-weight: bold;">ACTIVE</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">DFIR</div>
          <div style="color: #00C896; font-weight: bold;">ACTIVE</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">Event Hub</div>
          <div style="color: #00C896; font-weight: bold;">ACTIVE</div>
        </div>
        <div>
          <div style="color: #a0a0a0;">Last Sync</div>
          <div style="color: #8B5CF6; font-weight: bold;">2 min ago</div>
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

  const assets = stateData.assets.assets || [];
  const critVulns = assets.reduce((sum, a) => sum + (a.critical || 0), 0);
  const highVulns = assets.reduce((sum, a) => sum + (a.high || 0), 0);
  const medVulns = assets.reduce((sum, a) => sum + (a.medium || 0), 0);
  const lowVulns = assets.reduce((sum, a) => sum + (a.low || 0), 0);
  const totalVulns = assets.reduce((sum, a) => sum + (a.vulnerability_count || 0), 0);

  element.innerHTML = `
    <div style="background: rgba(249, 115, 22, 0.1); border: 2px solid #F97316; border-radius: 8px; padding: 20px; margin-top: 20px;">
      <div style="color: #F97316; font-weight: bold; font-size: 16px; text-transform: uppercase; margin-bottom: 15px;">🔍 VULNERABILITY CENTER</div>
      <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr 1fr; gap: 10px; font-size: 12px; font-family: monospace;">
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

function drawPhysicalTopology(svg, assets) {
  const width = svg.clientWidth;
  const height = svg.clientHeight;

  // OPERATIONAL NETWORK DISPLAY - Real Asset Data
  svg.innerHTML = '';

  let html = `<div style="padding: 20px; font-family: monospace; font-size: 12px;">`;
  html += `<div style="margin-bottom: 20px; color: #00C896; font-weight: bold; text-transform: uppercase;">🌍 INTERNET</div>`;

  // Gateway
  const gateway = assets.find(a => a.device_type === 'Router');
  if (gateway) {
    html += `<div style="margin-left: 40px; margin-bottom: 15px; color: #06B6D4;">
      🚪 GATEWAY
      <div style="color: #a0a0a0; margin-left: 20px; font-size: 11px;">
        IP: ${gateway.ip}<br>
        Vulnerabilities: ${gateway.vulnerability_count}<br>
        Risk: ${gateway.vulnerability_count > 30 ? '🔴 HIGH' : gateway.vulnerability_count > 15 ? '🟠 MEDIUM' : '🟢 LOW'}
      </div>
    </div>`;
  }

  // Assets grouped by device type
  const servers = assets.filter(a => a.device_type === 'Server');
  if (servers.length > 0) {
    html += `<div style="margin-left: 80px; color: #F97316; font-weight: bold; margin-bottom: 10px;">💻 SERVERS</div>`;
    servers.forEach(server => {
      const riskColor = server.vulnerability_count > 30 ? '#FF3B5C' : server.vulnerability_count > 15 ? '#FFB347' : '#22ff22';
      html += `<div style="margin-left: 100px; margin-bottom: 8px; color: ${riskColor}; font-size: 11px;">
        ${server.hostname} | ${server.ip}<br>
        <span style="color: #a0a0a0;">Vulns: ${server.vulnerability_count} | Risk: ${server.vulnerability_count}</span>
      </div>`;
    });
  }

  html += `</div>`;
  svg.style.background = 'rgba(10, 14, 39, 0.5)';
  svg.style.padding = '20px';
  svg.style.borderRadius = '8px';
  svg.style.border = '1px solid rgba(139, 92, 246, 0.2)';
  svg.innerHTML = html;
}

function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? [parseInt(result[1], 16), parseInt(result[2], 16), parseInt(result[3], 16)] : [0, 0, 0];
}

function drawSecurityTopology(svg, incidents) {
  const assets = stateData.assets.assets || [];
  const waapScore = calculateWAAPScore();

  svg.innerHTML = '';

  let html = `<div style="padding: 20px; font-family: monospace; font-size: 13px; line-height: 2;">`;
  html += `<div style="color: #00C896; text-align: center; font-weight: bold; margin-bottom: 20px; font-size: 14px;">SECURITY OPERATIONS FLOW</div>`;

  html += `<div style="color: #00C896; font-weight: bold;">🌍 INTERNET</div>`;
  html += `<div style="text-align: center; color: #8B5CF6; margin: 10px 0;">↓</div>`;

  html += `<div style="color: #06B6D4; font-weight: bold;">🛡️ WAAP DEFENSE</div>`;
  html += `<div style="color: #a0a0a0; margin-left: 20px; font-size: 12px;">Score: ${waapScore}/100</div>`;
  html += `<div style="text-align: center; color: #8B5CF6; margin: 10px 0;">↓</div>`;

  html += `<div style="color: #F97316; font-weight: bold;">🚪 GATEWAY</div>`;
  const gateway = assets.find(a => a.device_type === 'Router');
  if (gateway) {
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
  html += `<div style="color: #a0a0a0; margin-left: 20px; font-size: 12px;">90+ Tools | ACTIVE</div>`;

  html += `</div>`;
  svg.style.background = 'rgba(10, 14, 39, 0.5)';
  svg.style.padding = '20px';
  svg.style.borderRadius = '8px';
  svg.style.border = '1px solid rgba(139, 92, 246, 0.2)';
  svg.innerHTML = html;
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
  const incidents = stateData.incidents.incidents || [];

  const critical = incidents.filter(i => i.severity === 'CRITICAL');
  const high = incidents.filter(i => i.severity === 'HIGH');
  const medium = incidents.filter(i => i.severity === 'MEDIUM');
  const low = incidents.filter(i => i.severity === 'LOW');

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

  document.getElementById('incident-board').innerHTML = boardHtml;
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
  const incidents = stateData.incidents.incidents || [];
  const assets = stateData.assets.assets || [];

  // Vulnerability Assessment
  const vulnHtml = `
    <div style="font-size: 0.9em;">
      <div style="margin: 10px 0;">Total Vulnerabilities: <span style="color: var(--color-accent); font-weight: bold;">${assets.reduce((sum, a) => sum + (a.vulnerability_count || 0), 0)}</span></div>
      <div style="margin: 10px 0;">Critical: <span class="severity-critical">${assets.reduce((sum, a) => sum + (a.critical || 0), 0)}</span></div>
      <div style="margin: 10px 0;">High: <span class="severity-high">${assets.reduce((sum, a) => sum + (a.high || 0), 0)}</span></div>
      <div style="margin: 10px 0;">Medium: <span class="severity-medium">${assets.reduce((sum, a) => sum + (a.medium || 0), 0)}</span></div>
      <div style="margin: 10px 0;">Low: <span class="severity-low">${assets.reduce((sum, a) => sum + (a.low || 0), 0)}</span></div>
    </div>
  `;
  document.getElementById('vuln-assessment').innerHTML = vulnHtml;

  // WAAP Assessment - Calculate score from security_summary
  let waapScore = 0;
  if (stateData.waap.security_summary) {
    if (stateData.waap.security_summary.ssl_valid) waapScore += 60;
    if (stateData.waap.security_summary.waf_active) waapScore += 15;
    if (stateData.waap.security_summary.cdn_active) waapScore += 15;
    if (stateData.waap.security_summary.protection_active) waapScore += 10;
  }
  const sslStatus = stateData.waap.ssl_status ? stateData.waap.ssl_status.toUpperCase() : 'UNKNOWN';
  const waapHtml = `
    <div style="font-size: 0.9em;">
      <div style="margin: 10px 0;">Health Score: <span style="color: var(--color-accent); font-weight: bold;">${waapScore || '-'}/100</span></div>
      <div style="margin: 10px 0;">SSL Status: <span>${sslStatus}</span></div>
      <div style="margin: 10px 0;">Days to Renewal: <span style="color: var(--color-accent);">${stateData.waap.days_until_expiry || '-'}</span></div>
      <div style="margin: 10px 0;">WAF Active: <span>${stateData.waap.security_summary?.waf_active ? 'YES' : 'NO'}</span></div>
      <div style="margin: 10px 0;">CDN Active: <span>${stateData.waap.security_summary?.cdn_active ? 'YES' : 'NO'}</span></div>
    </div>
  `;
  document.getElementById('waap-assessment').innerHTML = waapHtml;

  // Domain Assessment - Calculate DNS Health from dns_complete
  let dnsHealth = 0;
  let dnsChecks = 0;
  if (stateData.domain.dns_complete) {
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
      <div style="margin: 10px 0;">Domain: <span>${stateData.domain.domain || 'UNKNOWN'}</span></div>
      <div style="margin: 10px 0;">SSL Expiry: <span style="color: var(--color-accent);">${stateData.domain.days_until_expiry || '-'} days</span></div>
      <div style="margin: 10px 0;">Nameservers: <span>${stateData.domain.nameservers?.length || 0} configured</span></div>
    </div>
  `;
  document.getElementById('domain-assessment').innerHTML = domainHtml;

  // Executive Analytics - Vulnerability Severity Chart
  const critVulns = assets.reduce((sum, a) => sum + (a.critical || 0), 0);
  const highVulns = assets.reduce((sum, a) => sum + (a.high || 0), 0);
  const medVulns = assets.reduce((sum, a) => sum + (a.medium || 0), 0);
  const lowVulns = assets.reduce((sum, a) => sum + (a.low || 0), 0);

  document.getElementById('chart-vuln-crit').textContent = critVulns;
  document.getElementById('chart-vuln-high').textContent = highVulns;
  document.getElementById('chart-vuln-med').textContent = medVulns;
  document.getElementById('chart-vuln-low').textContent = lowVulns;

  // WAAP Radar
  const sslValid = stateData.waap.security_summary?.ssl_valid ? '✓' : '✗';
  const wafActive = stateData.waap.security_summary?.waf_active ? '✓' : '✗';
  const cdnActive = stateData.waap.security_summary?.cdn_active ? '✓' : '✗';
  const protActive = stateData.waap.security_summary?.protection_active ? '✓' : '✗';

  document.getElementById('radar-ssl').textContent = sslValid;
  document.getElementById('radar-waf').textContent = wafActive;
  document.getElementById('radar-cdn').textContent = cdnActive;
  document.getElementById('radar-prot').textContent = protActive;

  // SOC Score Gauge
  const riskScore = stateData.risk.overall_score || 0;
  const dnsScore = dnsPercent !== '-' ? parseInt(dnsPercent) : 0;

  document.getElementById('gauge-risk').textContent = riskScore + '/100';
  document.getElementById('gauge-risk-bar').style.width = riskScore + '%';

  document.getElementById('gauge-waap').textContent = waapScore + '/100';
  document.getElementById('gauge-waap-bar').style.width = waapScore + '%';

  document.getElementById('gauge-dns').textContent = dnsScore + '%';
  document.getElementById('gauge-dns-bar').style.width = dnsScore + '%';
}

// ============================================================================
// EXECUTIVE SCORECARD PAGE
// ============================================================================

function renderExecutiveScorecard() {
  const incidents = stateData.incidents.incidents || [];
  const assets = stateData.assets.assets || [];
  const riskScore = stateData.risk.overall_score || 0;

  // Calculate metrics
  const totalVulns = assets.reduce((sum, a) => sum + (a.vulnerability_count || 0), 0);
  const critVulns = assets.reduce((sum, a) => sum + (a.critical || 0), 0);
  const highVulns = assets.reduce((sum, a) => sum + (a.high || 0), 0);
  const criticalIncidents = incidents.filter(i => i.severity === 'CRITICAL').length;
  const highIncidents = incidents.filter(i => i.severity === 'HIGH').length;
  const atRiskAssets = assets.filter(a => (a.vulnerability_count || 0) > 10).length;

  // Calculate WAAP Score
  let waapScore = 0;
  if (stateData.waap.security_summary) {
    if (stateData.waap.security_summary.ssl_valid) waapScore += 60;
    if (stateData.waap.security_summary.waf_active) waapScore += 15;
    if (stateData.waap.security_summary.cdn_active) waapScore += 15;
    if (stateData.waap.security_summary.protection_active) waapScore += 10;
  }

  // Calculate DNS Health
  let dnsHealth = 0;
  let dnsChecks = 0;
  if (stateData.domain.dns_complete) {
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
  document.getElementById('score-risk').textContent = riskScore;
  document.getElementById('score-risk-level').textContent = getThreatLevel(riskScore);

  document.getElementById('score-waap').textContent = waapScore > 0 ? waapScore : '-';
  document.getElementById('score-dns').textContent = dnsPercent + '%';
  document.getElementById('score-assets').textContent = assets.length;
  document.getElementById('score-incidents').textContent = incidents.length;
  document.getElementById('score-vulns').textContent = totalVulns;

  document.getElementById('score-threat').textContent = getThreatLevel(riskScore);
  document.getElementById('score-threat-detail').textContent = getRiskDetail(riskScore);

  // Summary metrics
  document.getElementById('summary-risk').textContent = riskScore + '/100';
  document.getElementById('summary-at-risk').textContent = atRiskAssets + ' of ' + assets.length;
  document.getElementById('summary-crit-vulns').textContent = critVulns;
  document.getElementById('summary-urgent').textContent = criticalIncidents + ' Critical, ' + highIncidents + ' High';

  document.getElementById('summary-dns').textContent = dnsPercent + '%';
  document.getElementById('summary-waap').textContent = waapScore > 0 ? waapScore + '/100' : 'Not Configured';

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

  document.getElementById('exec-recommendations').innerHTML = recHtml;
}

function getRiskDetail(score) {
  if (score >= 80) return 'Immediate action required';
  if (score >= 60) return 'High priority remediation needed';
  if (score >= 40) return 'Medium priority - plan remediation';
  return 'Acceptable risk level';
}

// ============================================================================
// TIMELINE PAGE
// ============================================================================

function renderTimeline() {
  const alerts = stateData.alerts.sent_alerts || [];
  const incidents = stateData.incidents.incidents || [];

  const events = [
    ...alerts.map(a => ({
      timestamp: a.sent_at,
      type: 'Alert Sent',
      title: `${a.severity} - ${a.title}`,
      severity: a.severity
    })),
    ...incidents.slice(0, 5).map(i => ({
      timestamp: i.created_at,
      type: 'Incident Created',
      title: i.title,
      severity: i.severity
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

  document.getElementById('timeline').innerHTML = timelineHtml || '<div style="color: var(--color-text-dim);">No events recorded</div>';
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function getRiskLevel(score) {
  if (score >= 80) return '🔴 CRITICAL';
  if (score >= 60) return '🟠 HIGH';
  if (score >= 40) return '🟡 MEDIUM';
  return '🟢 LOW';
}

function getThreatLevel(score) {
  if (score >= 80) return 'CRITICAL';
  if (score >= 60) return 'HIGH';
  if (score >= 40) return 'MEDIUM';
  return 'LOW';
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
    const activePage = document.querySelector('.page.active').id;
    if (activePage === 'overview') renderOverviewPage();
    else if (activePage === 'incidents') renderIncidentBoard();
  }, refreshInterval);
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', init);
