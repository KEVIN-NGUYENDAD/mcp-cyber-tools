import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class iPhoneSecurityBrief {
  constructor() {
    this.reportsDir = './reports/iphone-briefs';
    this.stateDir = './reports/iphone-state';
    this.ensureDirectories();
  }

  ensureDirectories() {
    [this.reportsDir, this.stateDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }

  getCurrentDeviceData() {
    // Load device data from iCloud/MDM API or local source
    // For now, returns template structure that integrations can populate
    const deviceDataPath = path.join(this.stateDir, 'current-device.json');

    if (fs.existsSync(deviceDataPath)) {
      try {
        return JSON.parse(fs.readFileSync(deviceDataPath, 'utf8'));
      } catch (e) {
        return this.getDefaultDeviceTemplate();
      }
    }

    return this.getDefaultDeviceTemplate();
  }

  getDefaultDeviceTemplate() {
    return {
      model: 'iPhone 15 Pro',
      iosVersion: '18.0',
      buildNumber: '22A5307f',
      timestamp: new Date().toISOString(),
      security: {
        passcodeEnabled: true,
        passcodeType: 'face-id',
        faceIdEnabled: true,
        touchIdEnabled: false,
        biometricFailures: 0,
        autoLockSeconds: 60,
        screenLockAge: 'today'
      },
      network: {
        vpnConnected: true,
        vpnApp: 'Mullvad VPN',
        dnsOverHttps: true,
        dnsProvider: 'CloudFlare',
        wifiAutoJoin: false,
        wifiNetworks: ['Home-Network'],
        cellularDataRestricted: false
      },
      device: {
        mdmEnrolled: true,
        mdmCompliant: true,
        unknownSourcesBlocked: true,
        findMyEnabled: true,
        autoUpdateEnabled: true,
        lastUpdateTime: '2 days ago'
      },
      apps: {
        totalInstalled: 147,
        newAppsToday: 0,
        trustedAppsCount: 120,
        untrustedAppsCount: 27,
        systemAppsOutdated: 0
      },
      profiles: {
        installed: [
          { name: 'MDM Management', type: 'mdm', issuer: 'Company IT', expiresIn: '180 days' },
          { name: 'VPN Configuration', type: 'vpn', issuer: 'Mullvad', expiresIn: '365 days' },
          { name: 'Email Configuration', type: 'email', issuer: 'Company IT', expiresIn: '90 days' }
        ]
      },
      storage: {
        totalCapacity: 256,
        used: 187,
        available: 69,
        systemUsed: 45,
        appsUsed: 95,
        mediaUsed: 47
      }
    };
  }

  getPreviousDeviceState() {
    const statePath = path.join(this.stateDir, 'previous-device-state.json');

    if (fs.existsSync(statePath)) {
      try {
        return JSON.parse(fs.readFileSync(statePath, 'utf8'));
      } catch (e) {
        return null;
      }
    }

    return null;
  }

  saveCurrentState(deviceData) {
    // Rotate previous state
    const statePath = path.join(this.stateDir, 'previous-device-state.json');
    const currentPath = path.join(this.stateDir, 'current-device-state.json');

    if (fs.existsSync(currentPath)) {
      const current = JSON.parse(fs.readFileSync(currentPath, 'utf8'));
      fs.writeFileSync(statePath, JSON.stringify(current, null, 2));
    }

    fs.writeFileSync(currentPath, JSON.stringify(deviceData, null, 2));
  }

  detectChanges(currentDevice, previousDevice) {
    if (!previousDevice) {
      return {
        iosVersionUpdated: false,
        securitySettingsChanged: false,
        profilesChanged: false,
        vpnStatusChanged: false,
        newAppsInstalled: 0,
        wifiNetworksChanged: false,
        mdmStatusChanged: false,
        autoUpdateStatusChanged: false,
        details: []
      };
    }

    const changes = {
      iosVersionUpdated: currentDevice.iosVersion !== previousDevice.iosVersion,
      securitySettingsChanged: false,
      profilesChanged: false,
      vpnStatusChanged: currentDevice.network.vpnConnected !== previousDevice.network.vpnConnected,
      newAppsInstalled: Math.max(0, currentDevice.apps.totalInstalled - previousDevice.apps.totalInstalled),
      wifiNetworksChanged: JSON.stringify(currentDevice.network.wifiNetworks) !== JSON.stringify(previousDevice.network.wifiNetworks),
      mdmStatusChanged: currentDevice.device.mdmEnrolled !== previousDevice.device.mdmEnrolled,
      autoUpdateStatusChanged: currentDevice.device.autoUpdateEnabled !== previousDevice.device.autoUpdateEnabled,
      details: []
    };

    // Check security settings
    if (currentDevice.security.passcodeEnabled !== previousDevice.security.passcodeEnabled) {
      changes.securitySettingsChanged = true;
      changes.details.push(`Passcode: ${previousDevice.security.passcodeEnabled ? 'disabled' : 'enabled'}`);
    }

    if (currentDevice.security.faceIdEnabled !== previousDevice.security.faceIdEnabled) {
      changes.securitySettingsChanged = true;
      changes.details.push(`FaceID: ${previousDevice.security.faceIdEnabled ? 'enabled' : 'disabled'}`);
    }

    if (currentDevice.security.autoLockSeconds !== previousDevice.security.autoLockSeconds) {
      changes.securitySettingsChanged = true;
      changes.details.push(`Auto-lock: ${previousDevice.security.autoLockSeconds}s → ${currentDevice.security.autoLockSeconds}s`);
    }

    // Check profiles
    if (JSON.stringify(currentDevice.profiles.installed) !== JSON.stringify(previousDevice.profiles.installed)) {
      changes.profilesChanged = true;
      changes.details.push(`Profiles changed: ${currentDevice.profiles.installed.length} installed`);
    }

    return changes;
  }

  calculateRiskScore(device) {
    let score = 95; // Start at excellent

    // Passcode & Biometrics (10 points)
    if (!device.security.passcodeEnabled) score -= 10;
    else if (device.security.autoLockSeconds > 300) score -= 3;

    // VPN (10 points)
    if (!device.network.vpnConnected) score -= 10;

    // DNS Security (8 points)
    if (!device.network.dnsOverHttps) score -= 8;

    // MDM/Management (10 points)
    if (!device.device.mdmEnrolled) score -= 10;
    else if (!device.device.mdmCompliant) score -= 5;

    // Auto-updates (8 points)
    if (!device.device.autoUpdateEnabled) score -= 8;

    // iOS Version (10 points - penalize if very old)
    const majorVersion = parseInt(device.iosVersion.split('.')[0]);
    if (majorVersion < 17) score -= 10;
    else if (majorVersion < 18) score -= 5;

    // WiFi Security (6 points)
    if (device.network.wifiAutoJoin) score -= 6;

    // Storage (5 points)
    const usagePercent = (device.storage.used / device.storage.totalCapacity) * 100;
    if (usagePercent > 90) score -= 5;
    else if (usagePercent > 80) score -= 2;

    // Unknown sources (5 points)
    if (!device.device.unknownSourcesBlocked) score -= 5;

    // Find My (5 points)
    if (!device.device.findMyEnabled) score -= 5;

    // Biometric failures (2 points per failure)
    score -= Math.min(6, device.security.biometricFailures * 2);

    return Math.max(0, Math.min(100, Math.round(score)));
  }

  determineThreatLevel(riskScore) {
    if (riskScore >= 85) return 'GREEN';
    if (riskScore >= 70) return 'YELLOW';
    if (riskScore >= 50) return 'ORANGE';
    return 'RED';
  }

  generateSecurityFindings(device, changes) {
    const findings = [];

    // Critical findings
    if (!device.security.passcodeEnabled) {
      findings.push({
        severity: 'CRITICAL',
        title: 'Passcode Disabled',
        description: 'Device is unprotected by passcode',
        confidence: 100,
        evidence: 1,
        recommendation: 'Enable passcode immediately'
      });
    }

    if (!device.network.vpnConnected) {
      findings.push({
        severity: 'HIGH',
        title: 'VPN Disconnected',
        description: 'Network traffic unencrypted',
        confidence: 100,
        evidence: 1,
        recommendation: 'Reconnect VPN'
      });
    }

    if (!device.device.mdmEnrolled) {
      findings.push({
        severity: 'HIGH',
        title: 'Not MDM Enrolled',
        description: 'Device not managed by IT',
        confidence: 100,
        evidence: 1,
        recommendation: 'Enroll in MDM'
      });
    }

    // Medium findings
    if (!device.network.dnsOverHttps) {
      findings.push({
        severity: 'MEDIUM',
        title: 'DNS Over HTTPS Disabled',
        description: 'DNS queries visible to ISP',
        confidence: 95,
        evidence: 1,
        recommendation: 'Enable DNS over HTTPS'
      });
    }

    if (device.security.autoLockSeconds > 300) {
      findings.push({
        severity: 'MEDIUM',
        title: 'Long Auto-lock Timeout',
        description: `Device locks after ${device.security.autoLockSeconds}s of inactivity`,
        confidence: 90,
        evidence: 1,
        recommendation: 'Reduce auto-lock to 60 seconds'
      });
    }

    if (device.network.wifiAutoJoin) {
      findings.push({
        severity: 'MEDIUM',
        title: 'WiFi Auto-join Enabled',
        description: 'Device auto-connects to previously known networks',
        confidence: 85,
        evidence: 1,
        recommendation: 'Disable WiFi auto-join'
      });
    }

    // Storage warning
    if ((device.storage.used / device.storage.totalCapacity) > 0.9) {
      findings.push({
        severity: 'LOW',
        title: 'Storage Nearly Full',
        description: `${Math.round((device.storage.used / device.storage.totalCapacity) * 100)}% capacity used`,
        confidence: 100,
        evidence: 1,
        recommendation: 'Free up storage space'
      });
    }

    return findings.sort((a, b) => {
      const severityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
      return severityOrder[a.severity] - severityOrder[b.severity];
    });
  }

  generateRecommendations(device, findings) {
    const recommendations = [];

    findings.slice(0, 5).forEach(finding => {
      recommendations.push({
        title: finding.recommendation,
        priority: finding.severity === 'CRITICAL' ? 'P1' : finding.severity === 'HIGH' ? 'P2' : 'P3',
        effort: 'LOW',
        impact: finding.severity,
        evidence: finding.evidence,
        confidence: finding.confidence
      });
    });

    // Add proactive recommendations
    if (device.device.autoUpdateEnabled) {
      recommendations.push({
        title: 'Verify auto-updates schedule',
        priority: 'P3',
        effort: 'LOW',
        impact: 'HIGH',
        evidence: 1,
        confidence: 80
      });
    }

    if (device.apps.untrustedAppsCount > device.apps.trustedAppsCount * 0.2) {
      recommendations.push({
        title: `Review ${device.apps.untrustedAppsCount} untrusted apps`,
        priority: 'P2',
        effort: 'MEDIUM',
        impact: 'MEDIUM',
        evidence: device.apps.untrustedAppsCount,
        confidence: 85
      });
    }

    return recommendations.slice(0, 5);
  }

  generateTrendSummary() {
    const trendsPath = path.join(this.stateDir, 'trends.json');

    let trends = { entries: [] };
    if (fs.existsSync(trendsPath)) {
      try {
        trends = JSON.parse(fs.readFileSync(trendsPath, 'utf8'));
      } catch (e) {
        // Start fresh
      }
    }

    return {
      daysTracked: trends.entries ? trends.entries.length : 0,
      avgRiskScore: trends.entries && trends.entries.length > 0
        ? Math.round(trends.entries.reduce((sum, e) => sum + e.riskScore, 0) / trends.entries.length)
        : 0,
      trend: 'stable', // Would compare scores over time
      improvementsSuggested: 3
    };
  }

  updateTrends(riskScore) {
    const trendsPath = path.join(this.stateDir, 'trends.json');

    let trends = { entries: [] };
    if (fs.existsSync(trendsPath)) {
      try {
        trends = JSON.parse(fs.readFileSync(trendsPath, 'utf8'));
      } catch (e) {
        // Start fresh
      }
    }

    trends.entries.push({
      date: new Date().toISOString().split('T')[0],
      riskScore: riskScore
    });

    // Keep last 30 days
    if (trends.entries.length > 30) {
      trends.entries = trends.entries.slice(-30);
    }

    fs.writeFileSync(trendsPath, JSON.stringify(trends, null, 2));
  }

  generateHTML(device, riskScore, threatLevel, changes, findings, recommendations, trends) {
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

    const changeCount = Object.values(changes).filter(v => v === true || (typeof v === 'number' && v > 0)).length;

    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>iPhone Security Brief - ${new Date().toISOString().split('T')[0]}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
      background: #f8f9fa;
      color: #1f2937;
      line-height: 1.5;
    }
    .container {
      max-width: 900px;
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
    .score-cards {
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
      font-size: 16px;
      font-weight: bold;
      color: #1f2937;
      margin-bottom: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      font-size: 14px;
    }
    .change-list {
      list-style: none;
      margin-left: 0;
    }
    .change-list li {
      padding: 6px 0;
      padding-left: 20px;
      position: relative;
    }
    .change-list li:before {
      content: "✓";
      position: absolute;
      left: 0;
      color: #16a34a;
      font-weight: bold;
    }
    .finding {
      background: #fef2f2;
      border-left: 4px solid ${severityColors['HIGH']};
      padding: 12px;
      margin-bottom: 8px;
      border-radius: 4px;
    }
    .finding.critical {
      background: #fef2f2;
      border-left-color: ${severityColors['CRITICAL']};
    }
    .finding.high {
      background: #fef3c7;
      border-left-color: ${severityColors['HIGH']};
    }
    .finding.medium {
      background: #fef9c3;
      border-left-color: ${severityColors['MEDIUM']};
    }
    .finding.low {
      background: #f0fdf4;
      border-left-color: ${severityColors['LOW']};
    }
    .finding-title {
      font-weight: bold;
      color: #1f2937;
      margin-bottom: 4px;
    }
    .finding-desc { font-size: 13px; color: #4b5563; }
    .finding-meta {
      font-size: 11px;
      color: #6b7280;
      margin-top: 6px;
    }
    .confidence-badge {
      display: inline-block;
      background: #e0e7ff;
      color: #3730a3;
      padding: 2px 6px;
      border-radius: 3px;
      font-size: 10px;
      font-weight: bold;
    }
    .recommendation {
      background: #f3f4f6;
      border: 1px solid #e5e7eb;
      padding: 12px;
      margin-bottom: 8px;
      border-radius: 4px;
    }
    .rec-title { font-weight: bold; color: #1f2937; margin-bottom: 6px; }
    .rec-meta {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      font-size: 11px;
      color: #6b7280;
    }
    .rec-badge {
      display: inline-block;
      padding: 2px 6px;
      border-radius: 3px;
      font-size: 10px;
      font-weight: bold;
    }
    .priority-p1 { background: #fee2e2; color: #991b1b; }
    .priority-p2 { background: #fef3c7; color: #92400e; }
    .priority-p3 { background: #dbeafe; color: #0c4a6e; }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
    }
    .full-width { grid-column: 1/-1; }
    .summary-box {
      background: #ecfdf5;
      border: 1px solid #a7f3d0;
      border-left: 4px solid #10b981;
      padding: 12px;
      border-radius: 4px;
      font-size: 13px;
    }
    @media (max-width: 640px) {
      .grid { grid-template-columns: 1fr; }
      .score-cards { grid-template-columns: repeat(2, 1fr); }
      .header-top { flex-direction: column; }
      .threat-badge { align-self: flex-start; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="header-top">
        <div>
          <div class="header-title">iPhone Security Brief</div>
          <div style="font-size: 12px; opacity: 0.8; margin-top: 4px;">${new Date().toISOString().split('T')[0]}</div>
        </div>
        <div class="threat-badge">${threatLabels[threatLevel]}</div>
      </div>
      <div class="score-cards">
        <div class="score-card">
          <div class="score-value">${riskScore}</div>
          <div class="score-label">SECURITY SCORE</div>
        </div>
        <div class="score-card">
          <div class="score-value">${changeCount}</div>
          <div class="score-label">CHANGES TODAY</div>
        </div>
        <div class="score-card">
          <div class="score-value">${findings.length}</div>
          <div class="score-label">FINDINGS</div>
        </div>
        <div class="score-card">
          <div class="score-value">${device.apps.totalInstalled}</div>
          <div class="score-label">APPS INSTALLED</div>
        </div>
      </div>
    </div>

    <div class="content">
      <div class="grid">
        <div>
          <div class="section">
            <div class="section-title">Changes Since Yesterday</div>
            ${changeCount === 0
              ? '<div style="color: #6b7280; font-size: 13px;">No changes detected</div>'
              : `<ul class="change-list">
                  ${changes.iosVersionUpdated ? '<li>iOS version updated</li>' : ''}
                  ${changes.securitySettingsChanged ? '<li>Security settings changed</li>' : ''}
                  ${changes.profilesChanged ? '<li>Device profiles changed</li>' : ''}
                  ${changes.vpnStatusChanged ? '<li>VPN status changed</li>' : ''}
                  ${changes.newAppsInstalled > 0 ? '<li>' + changes.newAppsInstalled + ' new apps installed</li>' : ''}
                  ${changes.wifiNetworksChanged ? '<li>WiFi networks changed</li>' : ''}
                  ${changes.mdmStatusChanged ? '<li>MDM enrollment changed</li>' : ''}
                  ${changes.autoUpdateStatusChanged ? '<li>Auto-update setting changed</li>' : ''}
                </ul>`
            }
          </div>
        </div>

        <div>
          <div class="section">
            <div class="section-title">Device Configuration</div>
            <ul class="change-list">
              <li>iOS ${device.iosVersion}</li>
              <li>${device.model}</li>
              <li>${device.security.passcodeEnabled ? '🔒 Passcode: Enabled' : '⚠️ Passcode: Disabled'}</li>
              <li>${device.network.vpnConnected ? '🔐 VPN: Connected' : '⚠️ VPN: Disconnected'}</li>
              <li>${((device.storage.used / device.storage.totalCapacity) * 100).toFixed(0)}% storage used</li>
            </ul>
          </div>
        </div>
      </div>

      <div class="section">
        <div class="section-title">Risk Findings (${findings.length})</div>
        ${findings.length === 0
          ? '<div class="summary-box">✓ No security issues detected</div>'
          : findings.map(f => `
              <div class="finding ${f.severity.toLowerCase()}">
                <div class="finding-title">${f.title}</div>
                <div class="finding-desc">${f.description}</div>
                <div class="finding-meta">
                  Confidence: <span class="confidence-badge">${f.confidence}%</span>
                </div>
              </div>
            `).join('')
        }
      </div>

      <div class="section">
        <div class="section-title">Recommendations (${recommendations.length})</div>
        ${recommendations.map(r => `
          <div class="recommendation">
            <div class="rec-title">${r.title}</div>
            <div class="rec-meta">
              <div>Priority: <span class="rec-badge priority-${r.priority.toLowerCase()}">${r.priority}</span></div>
              <div>Effort: ${r.effort}</div>
              <div>Impact: ${r.impact}</div>
            </div>
          </div>
        `).join('')}
      </div>

      <div class="section">
        <div class="section-title">Trend Summary</div>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
          <div class="summary-box">
            <strong>Days Tracked:</strong> ${trends.daysTracked}
          </div>
          <div class="summary-box">
            <strong>30-Day Avg:</strong> ${trends.avgRiskScore}/100
          </div>
        </div>
      </div>
    </div>
  </div>
</body>
</html>`;

    return html;
  }

  generateBrief() {
    const today = new Date().toISOString().split('T')[0];

    // Load device data
    const currentDevice = this.getCurrentDeviceData();
    const previousDevice = this.getPreviousDeviceState();

    // Save current state
    this.saveCurrentState(currentDevice);

    // Detect changes
    const changes = this.detectChanges(currentDevice, previousDevice);

    // Calculate risk score
    const riskScore = this.calculateRiskScore(currentDevice);
    const threatLevel = this.determineThreatLevel(riskScore);

    // Generate findings
    const findings = this.generateSecurityFindings(currentDevice, changes);

    // Generate recommendations
    const recommendations = this.generateRecommendations(currentDevice, findings);

    // Get trends
    const trends = this.generateTrendSummary();

    // Update trends
    this.updateTrends(riskScore);

    // Generate HTML
    const html = this.generateHTML(currentDevice, riskScore, threatLevel, changes, findings, recommendations, trends);

    // Save to local file
    const localFilename = `iphone-security-brief-${today}.html`;
    fs.writeFileSync(localFilename, html);

    // Archive to reports
    const archivedFilename = path.join(this.reportsDir, `${today}.html`);
    fs.writeFileSync(archivedFilename, html);

    // Output summary
    console.log(`✓ iPhone Security Brief generated`);
    console.log(`  File: ${localFilename}`);
    console.log(`  Security Score: ${riskScore}/100`);
    console.log(`  Threat Level: ${threatLevel}`);
    console.log(`  Changes: ${Object.values(changes).filter(v => v === true || (typeof v === 'number' && v > 0)).length}`);
    console.log(`  Findings: ${findings.length}`);
    console.log(`  Recommendations: ${recommendations.length}`);
  }
}

// Execute
const briefer = new iPhoneSecurityBrief();
briefer.generateBrief();

export { iPhoneSecurityBrief };
