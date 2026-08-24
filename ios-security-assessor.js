/**
 * iOS Security Assessment Framework
 *
 * Generates executive security assessment for iPhone/iPad
 * Input: Device security data (manual collection or MDM export)
 * Output: Executive summary with risk scoring and recommendations
 */

import { writeFileSync } from "fs";

class iOSSecurityAssessor {
  constructor(deviceData = {}) {
    this.timestamp = new Date().toISOString();
    this.reportDate = new Date().toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric"
    });
    this.reportTime = new Date().toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit"
    });

    // Device data structure
    this.device = {
      model: deviceData.model || "iPhone (Unknown)",
      osVersion: deviceData.osVersion || "Unknown",
      buildVersion: deviceData.buildVersion || "Unknown",
      serialNumber: deviceData.serialNumber || "Not provided",
      imei: deviceData.imei || "Redacted",
      iccid: deviceData.iccid || "Redacted"
    };

    // Security assessment data
    this.security = {
      faceIdEnabled: deviceData.faceIdEnabled !== false,
      touchIdEnabled: deviceData.touchIdEnabled !== false,
      passcodeEnabled: deviceData.passcodeEnabled !== false,
      passcodeLength: deviceData.passcodeLength || 6,
      autoLockTimeout: deviceData.autoLockTimeout || 60,
      allowSimplePasscode: deviceData.allowSimplePasscode === true,
      requireAlphanumericPasscode: deviceData.requireAlphanumericPasscode !== false,
      maximumFailedAttempts: deviceData.maximumFailedAttempts || 6,
      eraseDataAfterFailedAttempts: deviceData.eraseDataAfterFailedAttempts !== false
    };

    // Jailbreak indicators
    this.jailbreakIndicators = deviceData.jailbreakIndicators || [];

    // Network configuration
    this.network = {
      vpnInstalled: deviceData.vpnInstalled === true,
      vpnProvider: deviceData.vpnProvider || "None",
      vpnAlwaysOn: deviceData.vpnAlwaysOn === true,
      dnsOverHttps: deviceData.dnsOverHttps === true,
      dnsProvider: deviceData.dnsProvider || "System Default",
      wifiAutoConnect: deviceData.wifiAutoConnect === true,
      captivePortalWarnings: deviceData.captivePortalWarnings !== false,
      autoJoinOpen: deviceData.autoJoinOpen === false
    };

    // Installed profiles
    this.installedProfiles = deviceData.installedProfiles || [];
    this.mdmEnrolled: deviceData.mdmEnrolled === true,
    this.mdmProvider: deviceData.mdmProvider || "None",

    // App security
    this.appSecurity = {
      appStoreOnly: deviceData.appStoreOnly !== false,
      unknownSourcesAllowed: deviceData.unknownSourcesAllowed === true,
      sideloadingEnabled: deviceData.sideloadingEnabled === true,
      automaticUpdatesEnabled: deviceData.automaticUpdatesEnabled !== false
    };

    // Data protection
    this.dataProtection = {
      iCloudBackupEnabled: deviceData.iCloudBackupEnabled !== false,
      encryptedBackup: deviceData.encryptedBackup === true,
      iCloudKeychain: deviceData.iCloudKeychain === true,
      locationServices: deviceData.locationServices === true,
      locationHistoryStored: deviceData.locationHistoryStored === false,
      crashReporting: deviceData.crashReporting === true,
      analyticsSharing: deviceData.analyticsSharing === false
    };

    // Permissions overview
    this.permissions = deviceData.permissions || {
      camera: "Restricted",
      microphone: "Restricted",
      contacts: "Partial",
      calendar: "Partial",
      location: "Partial",
      health: "Restricted",
      photos: "Partial",
      bluetooth: "Enabled"
    };
  }

  // Calculate risk score
  calculateRiskScore() {
    let score = 100;
    const deductions = [];

    // Passcode assessment (critical)
    if (!this.security.passcodeEnabled) {
      score -= 30;
      deductions.push("No passcode protection: -30 points");
    } else if (this.security.passcodeLength < 6) {
      score -= 15;
      deductions.push(`Weak passcode (${this.security.passcodeLength} digits): -15 points`);
    } else if (this.security.allowSimplePasscode) {
      score -= 10;
      deductions.push("Simple passcode allowed: -10 points");
    }

    // Biometric security
    if (!this.security.faceIdEnabled && !this.security.touchIdEnabled) {
      score -= 5;
      deductions.push("No biometric protection: -5 points");
    }

    // Auto-lock timeout
    if (this.security.autoLockTimeout > 300) {
      score -= 8;
      deductions.push(`Long auto-lock timeout (${this.security.autoLockTimeout}s): -8 points`);
    }

    // Jailbreak indicators
    if (this.jailbreakIndicators.length > 0) {
      score -= 25;
      deductions.push(`Jailbreak indicators found: -25 points`);
    }

    // VPN configuration
    if (!this.network.vpnInstalled) {
      score -= 5;
      deductions.push("No VPN configured: -5 points");
    } else if (!this.network.vpnAlwaysOn) {
      score -= 3;
      deductions.push("VPN not always-on: -3 points");
    }

    // DNS over HTTPS
    if (!this.network.dnsOverHttps) {
      score -= 8;
      deductions.push("DNS over HTTPS not enabled: -8 points");
    }

    // MDM enrollment
    if (!this.mdmEnrolled) {
      score -= 5;
      deductions.push("Not enrolled in MDM: -5 points");
    }

    // Data protection
    if (!this.dataProtection.encryptedBackup) {
      score -= 10;
      deductions.push("Unencrypted backup: -10 points");
    }

    // App security
    if (this.appSecurity.unknownSourcesAllowed || this.appSecurity.sideloadingEnabled) {
      score -= 15;
      deductions.push("Sideloading or unknown sources enabled: -15 points");
    }

    // Automatic updates
    if (!this.appSecurity.automaticUpdatesEnabled) {
      score -= 8;
      deductions.push("Automatic updates disabled: -8 points");
    }

    // Analytics and crash reporting
    if (this.dataProtection.analyticsSharing) {
      score -= 3;
      deductions.push("Analytics data sharing enabled: -3 points");
    }

    // Auto-join open networks
    if (this.network.wifiAutoConnect && this.network.autoJoinOpen) {
      score -= 8;
      deductions.push("Auto-join open WiFi enabled: -8 points");
    }

    score = Math.max(0, Math.min(100, score));

    return { score, deductions };
  }

  determineThreatLevel(score) {
    if (score >= 90) return "LOW";
    if (score >= 75) return "MEDIUM";
    if (score >= 50) return "HIGH";
    return "CRITICAL";
  }

  generateRecommendations() {
    const recommendations = [];

    // Passcode
    if (!this.security.passcodeEnabled) {
      recommendations.push({
        priority: "CRITICAL",
        title: "Enable Passcode Protection",
        description: "Set a strong alphanumeric passcode (minimum 6 characters, preferably 8+)",
        impact: "HIGH",
        effort: "LOW"
      });
    }

    // Jailbreak
    if (this.jailbreakIndicators.length > 0) {
      recommendations.push({
        priority: "CRITICAL",
        title: "Remove Jailbreak",
        description: `Restore device to remove jailbreak. Indicators: ${this.jailbreakIndicators.join(", ")}`,
        impact: "CRITICAL",
        effort: "HIGH"
      });
    }

    // VPN
    if (!this.network.vpnInstalled) {
      recommendations.push({
        priority: "HIGH",
        title: "Install and Enable VPN",
        description: "Configure reliable VPN with always-on policy for network privacy",
        impact: "MEDIUM",
        effort: "LOW"
      });
    }

    // DNS over HTTPS
    if (!this.network.dnsOverHttps) {
      recommendations.push({
        priority: "HIGH",
        title: "Enable DNS over HTTPS",
        description: "Settings → Privacy & Security → DNS over HTTPS → Configure",
        impact: "MEDIUM",
        effort: "LOW"
      });
    }

    // MDM Enrollment
    if (!this.mdmEnrolled) {
      recommendations.push({
        priority: "MEDIUM",
        title: "Enroll in MDM",
        description: "Use organizational MDM for device management and policy enforcement",
        impact: "MEDIUM",
        effort: "MEDIUM"
      });
    }

    // Encrypted backup
    if (!this.dataProtection.encryptedBackup) {
      recommendations.push({
        priority: "HIGH",
        title: "Enable Encrypted Backup",
        description: "Settings → [Your Name] → iCloud → iCloud Backup → Enable with password",
        impact: "HIGH",
        effort: "LOW"
      });
    }

    // Automatic updates
    if (!this.appSecurity.automaticUpdatesEnabled) {
      recommendations.push({
        priority: "HIGH",
        title: "Enable Automatic Updates",
        description: "Settings → General → Software Update → Automatic Updates",
        impact: "HIGH",
        effort: "LOW"
      });
    }

    // Auto-lock
    if (this.security.autoLockTimeout > 300) {
      recommendations.push({
        priority: "MEDIUM",
        title: "Reduce Auto-lock Timeout",
        description: "Set to 1-2 minutes maximum. Settings → Display & Brightness → Auto-Lock",
        impact: "MEDIUM",
        effort: "LOW"
      });
    }

    // WiFi security
    if (this.network.autoJoinOpen) {
      recommendations.push({
        priority: "MEDIUM",
        title: "Disable Auto-Join for Open Networks",
        description: "Settings → WiFi → WiFi Networks → Disable auto-join",
        impact: "MEDIUM",
        effort: "LOW"
      });
    }

    return recommendations.sort((a, b) => {
      const priorityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    }).slice(0, 5);
  }

  generateExecutiveSummary(riskScore, threatLevel) {
    if (threatLevel === "CRITICAL") {
      return `Device security posture is CRITICAL. Immediate action required. ${this.jailbreakIndicators.length > 0 ? "Jailbreak detected." : "No passcode protection detected."}`;
    } else if (threatLevel === "HIGH") {
      return `Device has significant security vulnerabilities. Multiple controls require attention. Recommend VPN, DNS, and encryption setup.`;
    } else if (threatLevel === "MEDIUM") {
      return `Device security is adequate but can be improved. Recommend enabling additional privacy controls and MDM enrollment.`;
    } else {
      return `Device security posture is strong. Maintain current security practices and keep iOS updated.`;
    }
  }

  generateHTML() {
    const riskData = this.calculateRiskScore();
    const threatLevel = this.determineThreatLevel(riskData.score);
    const recommendations = this.generateRecommendations();
    const summary = this.generateExecutiveSummary(riskData.score, threatLevel);

    const threatColors = {
      LOW: "#388E3C",
      MEDIUM: "#FBC02D",
      HIGH: "#F57C00",
      CRITICAL: "#D32F2F"
    };

    const threatColor = threatColors[threatLevel] || "#1976D2";

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>iOS Security Assessment - ${this.reportDate}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, "Segoe UI", sans-serif;
      background: #FCFCFB;
      color: #2E2C27;
      line-height: 1.6;
    }
    .container {
      max-width: 960px;
      margin: 0 auto;
      padding: 40px 30px;
    }
    .header {
      margin-bottom: 30px;
      padding-bottom: 20px;
      border-bottom: 2px solid #E1E1DF;
    }
    h1 {
      font-size: 32px;
      margin-bottom: 20px;
      color: #2E2C27;
      font-weight: 600;
    }
    .header-meta {
      font-size: 11px;
      color: #6B6A63;
      margin-bottom: 15px;
    }
    .score-card {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 15px;
      margin-top: 20px;
    }
    .score-box {
      padding: 20px;
      background: #F9F9F7;
      border-radius: 6px;
      border-left: 4px solid ${threatColor};
      text-align: center;
    }
    .score-value {
      font-size: 48px;
      font-weight: bold;
      color: ${threatColor};
      margin-bottom: 5px;
    }
    .score-label {
      font-size: 12px;
      color: #6B6A63;
    }
    .threat-badge {
      display: inline-block;
      padding: 6px 12px;
      background: ${threatColor};
      color: white;
      border-radius: 4px;
      font-size: 11px;
      font-weight: bold;
      margin-top: 10px;
    }
    .summary-box {
      background: ${threatColor}22;
      border-left: 4px solid ${threatColor};
      padding: 15px;
      border-radius: 4px;
      margin-top: 20px;
      font-size: 14px;
      line-height: 1.7;
    }
    .main-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-top: 30px;
    }
    .section {
      background: #F9F9F7;
      padding: 20px;
      border-radius: 6px;
      border: 1px solid #E4E3DC;
    }
    .section h2 {
      font-size: 16px;
      margin-bottom: 15px;
      color: #2E2C27;
      border-bottom: 2px solid #E1E1DF;
      padding-bottom: 10px;
      font-weight: 600;
    }
    .item {
      margin-bottom: 12px;
      padding: 10px;
      background: #FCFCFB;
      border-radius: 4px;
      border-left: 3px solid #1976D2;
      font-size: 12px;
    }
    .item.pass {
      border-left-color: #388E3C;
    }
    .item.fail {
      border-left-color: #D32F2F;
    }
    .item.warn {
      border-left-color: #FBC02D;
    }
    .item-title {
      font-weight: bold;
      color: #2E2C27;
      margin-bottom: 4px;
    }
    .item-value {
      color: #6B6A63;
      font-size: 11px;
    }
    .recommendation {
      margin-bottom: 15px;
      padding: 12px;
      background: #FCFCFB;
      border-radius: 4px;
      border-left: 3px solid #1976D2;
    }
    .recommendation.critical {
      border-left-color: #D32F2F;
    }
    .recommendation.high {
      border-left-color: #F57C00;
    }
    .rec-title {
      font-weight: bold;
      color: #2E2C27;
      margin-bottom: 4px;
    }
    .rec-desc {
      font-size: 12px;
      color: #6B6A63;
      margin-bottom: 4px;
    }
    .rec-meta {
      font-size: 11px;
      color: #B4B3A8;
    }
    .full-width {
      grid-column: 1 / -1;
    }
    .footer {
      margin-top: 30px;
      padding-top: 20px;
      border-top: 1px solid #E1E1DF;
      font-size: 11px;
      color: #B4B3A8;
      text-align: center;
    }
    @media (max-width: 768px) {
      .main-grid { grid-template-columns: 1fr; }
      .score-card { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="header-meta">${this.reportDate} • ${this.reportTime}</div>
      <h1>iOS Security Assessment</h1>
      <div class="score-card">
        <div class="score-box">
          <div class="score-value">${riskData.score}</div>
          <div class="score-label">Risk Score</div>
          <div class="threat-badge">${threatLevel} RISK</div>
        </div>
        <div class="score-box">
          <div class="score-value">${this.device.model}</div>
          <div class="score-label">Device Model</div>
        </div>
        <div class="score-box">
          <div class="score-value">${this.device.osVersion}</div>
          <div class="score-label">iOS Version</div>
        </div>
      </div>
      <div class="summary-box">${summary}</div>
    </div>

    <div class="main-grid">
      <!-- Device Info -->
      <div class="section">
        <h2>Device Information</h2>
        <div class="item">
          <div class="item-title">Model</div>
          <div class="item-value">${this.device.model}</div>
        </div>
        <div class="item">
          <div class="item-title">iOS Version</div>
          <div class="item-value">${this.device.osVersion} (${this.device.buildVersion})</div>
        </div>
        <div class="item">
          <div class="item-title">Serial Number</div>
          <div class="item-value">${this.device.serialNumber}</div>
        </div>
      </div>

      <!-- Authentication Security -->
      <div class="section">
        <h2>Authentication</h2>
        <div class="item ${this.security.passcodeEnabled ? 'pass' : 'fail'}">
          <div class="item-title">Passcode</div>
          <div class="item-value">${this.security.passcodeEnabled ? '✓ Enabled' : '✗ Disabled'}</div>
        </div>
        <div class="item ${this.security.faceIdEnabled ? 'pass' : 'warn'}">
          <div class="item-title">Face ID</div>
          <div class="item-value">${this.security.faceIdEnabled ? '✓ Enabled' : '✗ Disabled'}</div>
        </div>
        <div class="item ${this.security.touchIdEnabled ? 'pass' : 'warn'}">
          <div class="item-title">Touch ID</div>
          <div class="item-value">${this.security.touchIdEnabled ? '✓ Enabled' : '✗ Disabled'}</div>
        </div>
        <div class="item ${!this.security.allowSimplePasscode ? 'pass' : 'fail'}">
          <div class="item-title">Alphanumeric Passcode</div>
          <div class="item-value">${!this.security.allowSimplePasscode ? '✓ Required' : '✗ Allowed Simple'}</div>
        </div>
      </div>

      <!-- Jailbreak Status -->
      <div class="section">
        <h2>Integrity Check</h2>
        <div class="item ${this.jailbreakIndicators.length === 0 ? 'pass' : 'fail'}">
          <div class="item-title">Jailbreak Status</div>
          <div class="item-value">${this.jailbreakIndicators.length === 0 ? '✓ Clean' : '✗ Compromised'}</div>
        </div>
        ${this.jailbreakIndicators.length > 0 ? `
          <div class="item fail">
            <div class="item-title">Indicators Found</div>
            <div class="item-value">${this.jailbreakIndicators.join(', ')}</div>
          </div>
        ` : ''}
      </div>

      <!-- Network Security -->
      <div class="section">
        <h2>Network Security</h2>
        <div class="item ${this.network.vpnInstalled ? 'pass' : 'fail'}">
          <div class="item-title">VPN Status</div>
          <div class="item-value">${this.network.vpnInstalled ? '✓ Configured' : '✗ Not Configured'}</div>
        </div>
        ${this.network.vpnInstalled ? `
          <div class="item ${this.network.vpnAlwaysOn ? 'pass' : 'warn'}">
            <div class="item-title">Always-On VPN</div>
            <div class="item-value">${this.network.vpnAlwaysOn ? '✓ Enabled' : '✗ Disabled'}</div>
          </div>
        ` : ''}
        <div class="item ${this.network.dnsOverHttps ? 'pass' : 'fail'}">
          <div class="item-title">DNS over HTTPS</div>
          <div class="item-value">${this.network.dnsOverHttps ? '✓ Enabled' : '✗ Disabled'}</div>
        </div>
        <div class="item ${!this.network.autoJoinOpen ? 'pass' : 'warn'}">
          <div class="item-title">Auto-Join Open WiFi</div>
          <div class="item-value">${!this.network.autoJoinOpen ? '✓ Disabled' : '✗ Enabled'}</div>
        </div>
      </div>

      <!-- Data Protection -->
      <div class="section">
        <h2>Data Protection</h2>
        <div class="item ${this.dataProtection.encryptedBackup ? 'pass' : 'fail'}">
          <div class="item-title">Encrypted Backup</div>
          <div class="item-value">${this.dataProtection.encryptedBackup ? '✓ Enabled' : '✗ Disabled'}</div>
        </div>
        <div class="item ${this.dataProtection.iCloudKeychain ? 'pass' : 'warn'}">
          <div class="item-title">iCloud Keychain</div>
          <div class="item-value">${this.dataProtection.iCloudKeychain ? '✓ Enabled' : '✗ Disabled'}</div>
        </div>
        <div class="item ${this.appSecurity.automaticUpdatesEnabled ? 'pass' : 'fail'}">
          <div class="item-title">Automatic Updates</div>
          <div class="item-value">${this.appSecurity.automaticUpdatesEnabled ? '✓ Enabled' : '✗ Disabled'}</div>
        </div>
      </div>

      <!-- MDM Status -->
      <div class="section">
        <h2>Device Management</h2>
        <div class="item ${this.mdmEnrolled ? 'pass' : 'warn'}">
          <div class="item-title">MDM Enrollment</div>
          <div class="item-value">${this.mdmEnrolled ? '✓ Enrolled' : '✗ Not Enrolled'}</div>
        </div>
        ${this.mdmEnrolled ? `
          <div class="item">
            <div class="item-title">MDM Provider</div>
            <div class="item-value">${this.mdmProvider}</div>
          </div>
        ` : ''}
        <div class="item">
          <div class="item-title">Installed Profiles</div>
          <div class="item-value">${this.installedProfiles.length} profile${this.installedProfiles.length !== 1 ? 's' : ''}</div>
        </div>
      </div>

      <!-- Recommendations -->
      <div class="section full-width">
        <h2>Top Recommendations</h2>
        ${recommendations.map(rec => `
          <div class="recommendation ${rec.priority.toLowerCase()}">
            <div class="rec-title">#${recommendations.indexOf(rec) + 1}: ${rec.title}</div>
            <div class="rec-desc">${rec.description}</div>
            <div class="rec-meta">Impact: ${rec.impact} • Effort: ${rec.effort}</div>
          </div>
        `).join('')}
      </div>
    </div>

    <div class="footer">
      <p>Generated: ${this.timestamp}</p>
      <p>iOS Security Assessment Report</p>
    </div>
  </div>
</body>
</html>`;
  }

  async generateAssessment() {
    console.log("Generating iOS Security Assessment...");
    const html = this.generateHTML();

    const filename = `ios-security-assessment-${new Date().toISOString().split("T")[0]}.html`;
    writeFileSync(filename, html);

    const riskData = this.calculateRiskScore();
    const threatLevel = this.determineThreatLevel(riskData.score);

    console.log(`✓ iOS Security Assessment generated`);
    console.log(`  File: ${filename}`);
    console.log(`  Device: ${this.device.model}`);
    console.log(`  iOS Version: ${this.device.osVersion}`);
    console.log(`  Risk Score: ${riskData.score}/100`);
    console.log(`  Threat Level: ${threatLevel}`);

    return { filename, html };
  }
}

// Example usage with sample data
const sampleDevice = {
  model: "iPhone 15 Pro",
  osVersion: "17.6.1",
  buildVersion: "21H123",
  serialNumber: "REDACTED",
  faceIdEnabled: true,
  touchIdEnabled: false,
  passcodeEnabled: true,
  passcodeLength: 8,
  autoLockTimeout: 60,
  allowSimplePasscode: false,
  requireAlphanumericPasscode: true,
  vpnInstalled: true,
  vpnProvider: "ProtonVPN",
  vpnAlwaysOn: true,
  dnsOverHttps: true,
  dnsProvider: "Cloudflare (1.1.1.1)",
  encryptedBackup: true,
  iCloudKeychain: true,
  automaticUpdatesEnabled: true,
  mdmEnrolled: false,
  jailbreakIndicators: [],
  installedProfiles: ["MDM Profile"],
  appSecurity: {
    appStoreOnly: true,
    automaticUpdatesEnabled: true
  }
};

if (import.meta.url === `file://${process.argv[1]}`) {
  const assessor = new iOSSecurityAssessor(sampleDevice);
  assessor.generateAssessment().catch(console.error);
}

export { iOSSecurityAssessor };
