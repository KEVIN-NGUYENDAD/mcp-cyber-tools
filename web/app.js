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
}

function drawPhysicalTopology(svg, assets) {
  const width = svg.clientWidth;
  const height = svg.clientHeight;

  // Group by device type
  const routers = assets.filter(a => a.device_type === 'Router');
  const servers = assets.filter(a => a.device_type === 'Server');

  // Draw internet at top
  svg.innerHTML += `
    <text x="${width/2}" y="40" text-anchor="middle" fill="var(--color-accent)" font-size="14" font-weight="bold">🌍 INTERNET</text>
    <circle cx="${width/2}" cy="60" r="15" fill="none" stroke="var(--color-accent)" stroke-width="2"/>
  `;

  // Draw routers
  let routerX = 100;
  routers.forEach((router, idx) => {
    const risk = router.vulnerability_count || 0;
    const color = risk > 20 ? 'var(--color-critical)' : risk > 10 ? 'var(--color-warning)' : 'var(--color-healthy)';

    svg.innerHTML += `
      <g class="device-node" onclick="showDevicePanel(this, '${router.hostname}', '${router.ip}', ${risk})">
        <circle cx="${routerX}" cy="150" r="20" fill="none" stroke="${color}" stroke-width="2"/>
        <text x="${routerX}" y="155" text-anchor="middle" fill="${color}" font-size="12" font-weight="bold">🛡</text>
        <text x="${routerX}" y="190" text-anchor="middle" fill="var(--color-text)" font-size="10">${router.hostname}</text>
      </g>
    `;
    routerX += 120;
  });

  // Draw connection from internet to routers
  routers.forEach((_, idx) => {
    const x = 100 + idx * 120;
    svg.innerHTML += `<line x1="${width/2}" y1="75" x2="${x}" y2="130" stroke="var(--color-border)" stroke-width="1" stroke-dasharray="5,5"/>`;
  });

  // Draw servers
  let serverIdx = 0;
  const serversPerRow = 5;
  servers.forEach((server, idx) => {
    const risk = server.vulnerability_count || 0;
    const color = risk > 20 ? 'var(--color-critical)' : risk > 10 ? 'var(--color-warning)' : 'var(--color-healthy)';
    const row = Math.floor(idx / serversPerRow);
    const col = idx % serversPerRow;
    const x = 100 + col * 100;
    const y = 300 + row * 120;

    svg.innerHTML += `
      <g class="device-node" onclick="showDevicePanel(this, '${server.hostname}', '${server.ip}', ${risk})">
        <circle cx="${x}" cy="${y}" r="18" fill="none" stroke="${color}" stroke-width="2"/>
        <text x="${x}" y="${y+4}" text-anchor="middle" fill="${color}" font-size="12" font-weight="bold">💻</text>
        <text x="${x}" y="${y+35}" text-anchor="middle" fill="var(--color-text)" font-size="9">${server.hostname}</text>
      </g>
    `;

    // Connect to first router
    if (routers.length > 0) {
      svg.innerHTML += `<line x1="${100}" y1="170" x2="${x}" y2="${y-18}" stroke="var(--color-border)" stroke-width="1" stroke-dasharray="3,3"/>`;
    }
  });
}

function drawSecurityTopology(svg, incidents) {
  // Enhanced Security Relationship Chain
  // Internet → WAAP → Gateway → Assets → Incidents → MCP Intelligence
  const width = svg.clientWidth;
  const height = svg.clientHeight;
  const centerX = width / 2;

  // Layer definitions
  const layers = [
    { y: 40, icon: '🌍', label: 'INTERNET', nodes: 1 },
    { y: 120, icon: '🛡️', label: 'WAAP DEFENSE', nodes: 1 },
    { y: 200, icon: '🚪', label: 'GATEWAY', nodes: 1 },
    { y: 280, icon: '💻', label: 'ASSETS', nodes: Math.min(5, Math.max(1, (stateData.assets.assets || []).length)) },
    { y: 380, icon: '🚨', label: 'INCIDENTS', nodes: Math.min(3, (incidents || []).length) },
    { y: 450, icon: '🤖', label: 'MCP INTELLIGENCE', nodes: 1 }
  ];

  // Draw layers with vertical connections
  let previousLayer = null;

  layers.forEach((layer, layerIdx) => {
    const nodeRadius = 15;
    const spacing = (width - 100) / (layer.nodes + 1);

    for (let i = 0; i < layer.nodes; i++) {
      const x = 50 + spacing * (i + 1);

      // Draw node
      const color = layerIdx === 4 ? 'var(--color-critical)' : layerIdx === 3 ? 'var(--color-warning)' : 'var(--color-accent)';
      svg.innerHTML += `
        <g>
          <circle cx="${x}" cy="${layer.y}" r="${nodeRadius}" fill="none" stroke="${color}" stroke-width="2"/>
          <text x="${x}" y="${layer.y + 5}" text-anchor="middle" fill="${color}" font-size="12" font-weight="bold">${layer.icon}</text>
        </g>
      `;

      // Draw connection to previous layer
      if (previousLayer) {
        const prevSpacing = (width - 100) / (previousLayer.nodes + 1);
        const prevX = 50 + prevSpacing * ((previousLayer.nodes > 1) ? Math.floor(layer.nodes / 2) : 1);
        const lineColor = layerIdx === 4 ? 'var(--color-critical)' : layerIdx === 3 ? 'var(--color-warning)' : 'var(--color-accent)';
        svg.innerHTML += `<line x1="${prevX}" y1="${previousLayer.y + nodeRadius}" x2="${x}" y2="${layer.y - nodeRadius}" stroke="${lineColor}" stroke-width="1.5" stroke-dasharray="5,5"/>`;
      }
    }

    // Draw layer label
    svg.innerHTML += `<text x="15" y="${layer.y + 5}" fill="var(--color-text-dim)" font-size="11" font-weight="bold">${layer.label}</text>`;

    previousLayer = layer;
  });

  // Add legend
  svg.innerHTML += `
    <text x="20" y="${height - 20}" fill="var(--color-text-dim)" font-size="10">
      Security Chain: Internet → WAAP → Gateway → Assets → Incidents → Intelligence
    </text>
  `;
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
  return `
    <div class="incident-card">
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
    case 'HIGH': return 'var(--color-warning)';
    case 'MEDIUM': return '#ffff00';
    case 'LOW': return 'var(--color-healthy)';
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
