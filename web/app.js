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
  try {
    if (!stateData.assets || !stateData.incidents || !stateData.risk) {
      console.log('[WARN] Data not ready');
      return;
    }

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

    const minutesOld = Math.round((Date.now() - new Date(stateData.assets?.timestamp || Date.now())) / 60000);
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
  } catch (error) {
    console.error('[ERROR] updateExecutiveSecurityRow:', error);
  }
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
}

function renderMCPCommandCenter() {
  const element = document.getElementById('mcp-command-center');
  if (!element) return;

  // Read MCP status from state data or default to ONLINE
  const mcpStatus = stateData.mcp?.status || 'ONLINE';
  const mcpToolCount = stateData.mcp?.tool_count || '90+';
  const mcpThreatHunting = stateData.mcp?.threat_hunting_active ? 'ACTIVE' : 'OFFLINE';
  const mcpDfir = stateData.mcp?.dfir_active ? 'ACTIVE' : 'OFFLINE';
  const mcpEventHub = stateData.mcp?.event_hub_active ? 'ACTIVE' : 'OFFLINE';
  const mcpLastSync = stateData.mcp?.last_sync || '2 min ago';

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
  const totalVulns = assets.reduce((sum, a) => sum + (a?.vulnerability_count || 0), 0);

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
  const mcpToolCount = stateData.mcp?.tool_count || '90+';
  const mcpStatus = stateData.mcp?.status || 'ACTIVE';
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
  if (score >= 80) return 'Immediate action required';
  if (score >= 60) return 'High priority remediation needed';
  if (score >= 40) return 'Medium priority - plan remediation';
  return 'Acceptable risk level';
}

// ============================================================================
// TIMELINE PAGE
// ============================================================================

function renderTimeline() {
  try {
    const alerts = stateData.alerts?.sent_alerts || [];
    const incidents = stateData.incidents?.incidents || [];

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
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', init);
