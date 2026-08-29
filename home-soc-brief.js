import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { HomeNetworkDiscovery } from './home-network-discovery.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class HomeSocBrief {
  constructor() {
    this.reportsDir = './reports/home-soc-briefs';
    this.stateDir = './reports/home-soc-state';
    this.discovery = new HomeNetworkDiscovery();
    this.ensureDirectories();
  }

  ensureDirectories() {
    [this.reportsDir, this.stateDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }

  loadDeviceBriefs() {
    // Load device scores from existing briefs
    const scores = {
      desktop: null,
      laptop: null,
      iphone: null
    };

    const today = new Date().toISOString().split('T')[0];

    // Try to load iPhone brief for device score
    const iphoneBriefPath = `iphone-security-brief-${today}.html`;
    if (fs.existsSync(iphoneBriefPath)) {
      try {
        const content = fs.readFileSync(iphoneBriefPath, 'utf8');
        const match = content.match(/(\d+)\/100/);
        if (match) {
          scores.iphone = parseInt(match[1]);
        }
      } catch (e) {
        // Continue
      }
    }

    // Try to load nightly brief for system scores
    const nightlyBriefPath = `nightly-security-brief-${today}.html`;
    if (fs.existsSync(nightlyBriefPath)) {
      try {
        const content = fs.readFileSync(nightlyBriefPath, 'utf8');
        const match = content.match(/Security Score[^>]*>(\d+)</);
        if (match) {
          // Assume this is desktop/laptop average
          scores.desktop = parseInt(match[1]);
          scores.laptop = parseInt(match[1]);
        }
      } catch (e) {
        // Continue
      }
    }

    // Defaults if not found
    return {
      desktop: scores.desktop || 80,
      laptop: scores.laptop || 80,
      iphone: scores.iphone || 95
    };
  }

  loadRouterStatus() {
    // Load router status from router-agent output
    const routerStatusPath = path.join(this.stateDir, 'router-status.json');

    const defaultStatus = {
      gateway: 'unknown',
      isOnline: false,
      deviceCount: 0,
      dnsConfig: { primary: 'unknown' },
      firmware: { version: 'unknown' }
    };

    if (fs.existsSync(routerStatusPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(routerStatusPath, 'utf8'));
        return {
          gateway: data.router?.status?.gateway || 'unknown',
          isOnline: data.router?.status?.healthCheck === 'ONLINE',
          deviceCount: data.devices?.count || 0,
          dnsConfig: data.network?.dns || { primary: 'unknown' },
          firmware: data.router?.firmware || { version: 'unknown' },
          upnp: data.network?.upnp?.enabled || false,
          guestWiFi: data.network?.guestWiFi?.detected || false
        };
      } catch (e) {
        return defaultStatus;
      }
    }

    return defaultStatus;
  }

  generateReportFromHistory(deviceHistory) {
    // Generate network report from accumulated history
    const devices = deviceHistory.devices || [];
    const cameraStatus = deviceHistory.cameraStatus || [];
    const changes = this.loadChangesLog();

    // Count devices and cameras
    const onlineCount = devices.length;
    const cameraCount = cameraStatus.filter(c => c.status === 'online').length;

    // Assess risks from accumulated data
    const cameraRisks = [];
    const routerRisks = [];

    // Simple risk assessment from camera status
    if (cameraCount === 0 && cameraStatus.length > 0) {
      cameraRisks.push({
        device: 'cameras',
        type: 'camera',
        severity: 'HIGH',
        title: 'All Cameras Offline',
        description: 'No cameras responding to network pings',
        confidence: 95
      });
    }

    // Score calculation based on state
    let score = 80;
    if (changes.length > 5) score -= 5; // Multiple changes
    if (cameraRisks.length > 0) score -= 10;

    return {
      score: Math.max(0, Math.min(100, score)),
      threatLevel: this.determineThreatLevel(score),
      deviceCount: onlineCount,
      onlineCount: onlineCount,
      offlineCount: 0,
      cameras: cameraCount,
      changes: {
        newDevices: changes.filter(c => c.type === 'new-device'),
        offlineDevices: changes.filter(c => c.type === 'device-offline'),
        portChanges: [],
        vendorChanges: []
      },
      risks: [...cameraRisks, ...routerRisks].slice(0, 5)
    };
  }

  calculateHomeScore(networkScore, deviceScores) {
    // Weighted: Network 30%, Desktop 25%, Laptop 25%, iPhone 20%
    const homeScore = Math.round(
      (networkScore * 0.30) +
      (deviceScores.desktop * 0.25) +
      (deviceScores.laptop * 0.25) +
      (deviceScores.iphone * 0.20)
    );

    return homeScore;
  }

  determineThreatLevel(score) {
    if (score >= 85) return 'GREEN';
    if (score >= 70) return 'YELLOW';
    if (score >= 50) return 'ORANGE';
    return 'RED';
  }

  generateHTML(homeScore, threatLevel, networkReport, deviceScores, discoveredDevices) {
    const threatColors = {
      RED: '#dc2626',
      ORANGE: '#ea580c',
      YELLOW: '#ca8a04',
      GREEN: '#16a34a'
    };

    const threatLabels = {
      RED: 'CRITICAL - Action Required',
      ORANGE: 'High Risk - Review Soon',
      YELLOW: 'Medium Risk - Monitor',
      GREEN: 'Secure - All Good'
    };

    const severityColors = {
      CRITICAL: '#dc2626',
      HIGH: '#f97316',
      MEDIUM: '#eab308',
      LOW: '#22c55e'
    };

    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Home SOC Brief - ${new Date().toISOString().split('T')[0]}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
      background: #f8f9fa;
      color: #1f2937;
      line-height: 1.5;
    }
    .container {
      max-width: 1000px;
      margin: 0 auto;
      background: white;
      min-height: 100vh;
    }
    .header {
      background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
      color: white;
      padding: 24px;
      border-left: 6px solid ${threatColors[threatLevel]};
    }
    .header-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 16px;
    }
    .header-title { font-size: 28px; font-weight: bold; }
    .threat-badge {
      background: ${threatColors[threatLevel]};
      color: white;
      padding: 8px 16px;
      border-radius: 4px;
      font-weight: bold;
      font-size: 12px;
    }
    .score-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 12px;
      margin-top: 16px;
    }
    .score-card {
      background: rgba(255,255,255,0.1);
      border: 1px solid rgba(255,255,255,0.2);
      padding: 12px;
      border-radius: 4px;
      text-align: center;
    }
    .score-value { font-size: 24px; font-weight: bold; }
    .score-label { font-size: 11px; opacity: 0.9; margin-top: 4px; }
    .content { padding: 24px; }
    .section {
      margin-bottom: 24px;
      border-bottom: 1px solid #e5e7eb;
      padding-bottom: 24px;
    }
    .section:last-child { border-bottom: none; }
    .section-title {
      font-size: 14px;
      font-weight: bold;
      color: #1f2937;
      margin-bottom: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .device-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }
    .device-box {
      background: #f3f4f6;
      border: 1px solid #e5e7eb;
      border-left: 4px solid #3b82f6;
      padding: 12px;
      border-radius: 4px;
    }
    .device-name { font-weight: bold; color: #1f2937; margin-bottom: 4px; font-size: 13px; }
    .device-info { font-size: 11px; color: #6b7280; }
    .device-status { font-size: 12px; color: #10b981; margin-top: 4px; font-weight: bold; }
    .risk {
      background: #fef2f2;
      border-left: 4px solid #f97316;
      padding: 12px;
      margin-bottom: 8px;
      border-radius: 4px;
    }
    .risk.critical { border-left-color: #dc2626; }
    .risk.high { border-left-color: #f97316; }
    .risk.medium { background: #fef9c3; border-left-color: #eab308; }
    .risk-title { font-weight: bold; color: #1f2937; margin-bottom: 4px; }
    .risk-device {
      display: inline-block;
      background: #e0e7ff;
      color: #3730a3;
      padding: 2px 6px;
      border-radius: 3px;
      font-size: 10px;
      font-weight: bold;
      margin-right: 6px;
    }
    .risk-meta { font-size: 11px; color: #6b7280; margin-top: 6px; }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
    }
    .full-width { grid-column: 1/-1; }
    .stat-box {
      background: #ecfdf5;
      border: 1px solid #a7f3d0;
      border-left: 4px solid #10b981;
      padding: 12px;
      border-radius: 4px;
      margin-bottom: 8px;
    }
    .stat-label { font-size: 11px; color: #047857; font-weight: bold; }
    .stat-value { font-size: 16px; font-weight: bold; color: #1f2937; margin-top: 4px; }
    @media (max-width: 640px) {
      .grid { grid-template-columns: 1fr; }
      .device-grid { grid-template-columns: 1fr; }
      .score-grid { grid-template-columns: repeat(2, 1fr); }
      .header-top { flex-direction: column; }
      .threat-badge { align-self: flex-start; margin-top: 12px; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="header-top">
        <div>
          <div class="header-title">🏠 Home SOC Brief</div>
          <div style="font-size: 12px; opacity: 0.8; margin-top: 4px;">
            Network + All Devices | ${new Date().toISOString().split('T')[0]}
          </div>
        </div>
        <div class="threat-badge">${threatLabels[threatLevel]}</div>
      </div>
      <div class="score-grid">
        <div class="score-card">
          <div class="score-value">${homeScore}</div>
          <div class="score-label">HOME SCORE</div>
        </div>
        <div class="score-card">
          <div class="score-value">${networkReport.score}</div>
          <div class="score-label">NETWORK</div>
        </div>
        <div class="score-card">
          <div class="score-value">${deviceScores.desktop}</div>
          <div class="score-label">DESKTOP</div>
        </div>
        <div class="score-card">
          <div class="score-value">${deviceScores.laptop}</div>
          <div class="score-label">LAPTOP</div>
        </div>
        <div class="score-card">
          <div class="score-value">${deviceScores.iphone}</div>
          <div class="score-label">iPHONE</div>
        </div>
      </div>
    </div>

    <div class="content">
      <div class="grid">
        <div>
          <div class="section">
            <div class="section-title">Network Status</div>
            <div class="stat-box">
              <div class="stat-label">Total Devices</div>
              <div class="stat-value">${networkReport.deviceCount}</div>
            </div>
            <div class="stat-box">
              <div class="stat-label">Online</div>
              <div class="stat-value">${networkReport.onlineCount}</div>
            </div>
            <div class="stat-box">
              <div class="stat-label">Cameras</div>
              <div class="stat-value">${networkReport.cameras}</div>
            </div>
          </div>
        </div>

        <div>
          <div class="section">
            <div class="section-title">Device Health</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
              <div style="background: #f3f4f6; padding: 8px; border-radius: 4px; text-align: center;">
                <div style="font-size: 11px; color: #6b7280;">Desktop</div>
                <div style="font-size: 16px; font-weight: bold;">${deviceScores.desktop}/100</div>
              </div>
              <div style="background: #f3f4f6; padding: 8px; border-radius: 4px; text-align: center;">
                <div style="font-size: 11px; color: #6b7280;">Laptop</div>
                <div style="font-size: 16px; font-weight: bold;">${deviceScores.laptop}/100</div>
              </div>
            </div>
            <div style="background: #f3f4f6; padding: 8px; border-radius: 4px; text-align: center; margin-top: 8px;">
              <div style="font-size: 11px; color: #6b7280;">iPhone</div>
              <div style="font-size: 16px; font-weight: bold;">${deviceScores.iphone}/100</div>
            </div>
          </div>
        </div>
      </div>

      <div class="section">
        <div class="section-title">Changes Detected Today</div>
        ${networkReport.changes.newDevices.length > 0
          ? `<div style="margin-bottom: 8px;"><strong>New Devices:</strong> ${networkReport.changes.newDevices.length}</div>`
          : ''}
        ${networkReport.changes.offlineDevices.length > 0
          ? `<div style="margin-bottom: 8px;"><strong>Offline:</strong> ${networkReport.changes.offlineDevices.length}</div>`
          : ''}
        ${networkReport.changes.portChanges.length > 0
          ? `<div style="margin-bottom: 8px;"><strong>Port Changes:</strong> ${networkReport.changes.portChanges.length}</div>`
          : ''}
        ${networkReport.changes.newDevices.length === 0 && networkReport.changes.offlineDevices.length === 0 && networkReport.changes.portChanges.length === 0
          ? '<div style="color: #6b7280; font-size: 13px;">✓ No changes detected</div>'
          : ''}
      </div>

      <div class="section">
        <div class="section-title">Top Risks (${networkReport.risks.length})</div>
        ${networkReport.risks.length === 0
          ? '<div style="color: #6b7280; font-size: 13px;">✓ No critical risks detected</div>'
          : networkReport.risks.map(risk => `
              <div class="risk ${risk.severity.toLowerCase()}">
                <div class="risk-title">
                  <span class="risk-device">${risk.device.toUpperCase()}</span>
                  ${risk.title}
                </div>
                <div class="risk-meta">${risk.description}</div>
              </div>
            `).join('')
        }
      </div>

      <div class="section">
        <div class="section-title">SOC Summary</div>
        <div style="background: #f3f4f6; padding: 12px; border-radius: 4px; line-height: 1.6;">
          <div><strong>1. What changed today?</strong> ${
            networkReport.changes.newDevices.length > 0 ? `${networkReport.changes.newDevices.length} new device(s)` :
            networkReport.changes.offlineDevices.length > 0 ? `${networkReport.changes.offlineDevices.length} device(s) offline` :
            'No significant changes'
          }</div>
          <div style="margin-top: 8px;"><strong>2. Highest risk?</strong> ${
            networkReport.risks.length > 0 ? networkReport.risks[0].title : 'No critical risks'
          }</div>
          <div style="margin-top: 8px;"><strong>3. Which device needs attention?</strong> ${
            networkReport.risks.length > 0 ? networkReport.risks[0].device : 'All devices normal'
          }</div>
          <div style="margin-top: 8px;"><strong>4. What did system learn?</strong> Home network established, ${networkReport.deviceCount} devices tracked</div>
          <div style="margin-top: 8px;"><strong>5. Improve next?</strong> Review camera security, disable unused ports</div>
        </div>
      </div>
    </div>
  </div>
</body>
</html>`;

    return html;
  }

  loadDeviceHistory() {
    // Load accumulated evidence from network collector
    const historyPath = path.join(this.stateDir, 'device-history.json');

    if (fs.existsSync(historyPath)) {
      try {
        return JSON.parse(fs.readFileSync(historyPath, 'utf8'));
      } catch (e) {
        return null;
      }
    }

    return null;
  }

  loadChangesLog() {
    // Load recorded changes
    const changesPath = path.join(this.stateDir, 'changes.json');

    if (fs.existsSync(changesPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(changesPath, 'utf8'));
        return data.changes || [];
      } catch (e) {
        return [];
      }
    }

    return [];
  }

  generateBrief() {
    const today = new Date().toISOString().split('T')[0];

    console.log('Generating Home SOC Brief from accumulated evidence...');

    // Load accumulated history from collector (not full scan)
    const deviceHistory = this.loadDeviceHistory();

    // Fallback to network discovery if no history
    let networkReport;
    if (deviceHistory && deviceHistory.devices && deviceHistory.devices.length > 0) {
      // Use accumulated evidence
      console.log('  (using device history from collector)');
      networkReport = this.generateReportFromHistory(deviceHistory);
    } else {
      // First run - do full discovery
      console.log('  (first run - performing full discovery)');
      networkReport = this.discovery.discover();
    }

    // Load device scores
    const deviceScores = this.loadDeviceBriefs();

    // Load router status from router-agent
    const routerStatus = this.loadRouterStatus();

    // Calculate home score
    const homeScore = this.calculateHomeScore(networkReport.score, deviceScores);
    const threatLevel = this.determineThreatLevel(homeScore);

    // Get discovered devices
    const currentDevicesPath = path.join(this.stateDir, 'current-devices.json');
    let discoveredDevices = [];
    if (fs.existsSync(currentDevicesPath)) {
      try {
        discoveredDevices = JSON.parse(fs.readFileSync(currentDevicesPath, 'utf8'));
      } catch (e) {
        // Continue
      }
    }

    // Generate HTML
    const html = this.generateHTML(homeScore, threatLevel, networkReport, deviceScores, discoveredDevices);

    // Save to local file
    const localFilename = `home-soc-brief-${today}.html`;
    fs.writeFileSync(localFilename, html);

    // Archive to reports
    const archivedFilename = path.join(this.reportsDir, `${today}.html`);
    fs.writeFileSync(archivedFilename, html);

    // Output summary
    console.log(`✓ Home SOC Brief generated`);
    console.log(`  File: ${localFilename}`);
    console.log(`  Home Score: ${homeScore}/100`);
    console.log(`  Threat Level: ${threatLevel}`);
    console.log(`  Network Score: ${networkReport.score}/100`);
    console.log(`  Desktop Score: ${deviceScores.desktop}/100`);
    console.log(`  Laptop Score: ${deviceScores.laptop}/100`);
    console.log(`  iPhone Score: ${deviceScores.iphone}/100`);
    console.log(`  Devices Online: ${networkReport.onlineCount}/${networkReport.deviceCount}`);
    console.log(`  Router Status: ${routerStatus.isOnline ? 'ONLINE' : 'OFFLINE'}`);
    console.log(`  Router Gateway: ${routerStatus.gateway}`);
    console.log(`  Cameras: ${networkReport.cameras}`);
    console.log(`  Top Risks: ${networkReport.risks.length}`);
  }
}

// Execute
const briefer = new HomeSocBrief();
briefer.generateBrief();

export { HomeSocBrief };
