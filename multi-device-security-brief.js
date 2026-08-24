import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class MultiDeviceSecurityBrief {
  constructor() {
    this.reportsDir = './reports/multi-device-briefs';
    this.stateDir = './reports/multi-device-state';
    this.devicesStateDir = './reports';
    this.ensureDirectories();
  }

  ensureDirectories() {
    [this.reportsDir, this.stateDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }

  loadDeviceData(deviceName) {
    // Try to load device state from its respective directory
    const devicePaths = {
      desktop: path.join(this.devicesStateDir, 'nightly-state', 'system-state.json'),
      laptop: path.join(this.devicesStateDir, 'nightly-state', 'system-state.json'), // Could be separate
      iphone: path.join(this.devicesStateDir, 'iphone-state', 'current-device.json')
    };

    const devicePath = devicePaths[deviceName.toLowerCase()];
    if (!devicePath) return null;

    if (fs.existsSync(devicePath)) {
      try {
        return JSON.parse(fs.readFileSync(devicePath, 'utf8'));
      } catch (e) {
        console.error(`Failed to parse ${deviceName} data:`, e.message);
        return null;
      }
    }

    return null;
  }

  loadDeviceBrief(deviceName) {
    // Load the latest brief HTML for a device
    const briefPaths = {
      desktop: './nightly-security-brief-*.html',
      laptop: './nightly-security-brief-*.html', // Could be separate for multi-device
      iphone: './iphone-security-brief-*.html'
    };

    // For now, find latest matching file
    const today = new Date().toISOString().split('T')[0];
    const patterns = {
      desktop: `nightly-security-brief-${today}.html`,
      laptop: `nightly-security-brief-${today}.html`,
      iphone: `iphone-security-brief-${today}.html`
    };

    const filename = patterns[deviceName.toLowerCase()];
    if (filename && fs.existsSync(filename)) {
      try {
        return fs.readFileSync(filename, 'utf8');
      } catch (e) {
        return null;
      }
    }

    return null;
  }

  extractScoreFromBrief(briefHtml) {
    // Extract numeric score from brief HTML
    if (!briefHtml) return null;

    // Look for "Security Score: XX/100" pattern
    const scoreMatch = briefHtml.match(/Security Score[^>]*>(\d+)/i);
    if (scoreMatch) {
      return parseInt(scoreMatch[1]);
    }

    // Fallback pattern
    const scoreMatch2 = briefHtml.match(/<div[^>]*score-value[^>]*>(\d+)<\/div>/i);
    if (scoreMatch2) {
      return parseInt(scoreMatch2[1]);
    }

    return null;
  }

  extractThreatLevelFromBrief(briefHtml) {
    if (!briefHtml) return 'UNKNOWN';

    // Look for threat level indicators
    if (briefHtml.includes('RED') && briefHtml.match(/threat[^>]*RED/i)) return 'RED';
    if (briefHtml.includes('ORANGE') && briefHtml.match(/threat[^>]*ORANGE/i)) return 'ORANGE';
    if (briefHtml.includes('YELLOW') && briefHtml.match(/threat[^>]*YELLOW/i)) return 'YELLOW';
    if (briefHtml.includes('GREEN') && briefHtml.match(/threat[^>]*GREEN/i)) return 'GREEN';

    return 'YELLOW'; // Default
  }

  calculateOverallScore(deviceScores) {
    // Weighted average: Desktop 40%, Laptop 40%, iPhone 20%
    const weights = {
      desktop: 0.4,
      laptop: 0.4,
      iphone: 0.2
    };

    let totalScore = 0;
    let totalWeight = 0;

    Object.entries(deviceScores).forEach(([device, score]) => {
      if (score !== null && weights[device]) {
        totalScore += score * weights[device];
        totalWeight += weights[device];
      }
    });

    return totalWeight > 0 ? Math.round(totalScore / totalWeight) : null;
  }

  determineThreatLevel(score) {
    if (score >= 85) return 'GREEN';
    if (score >= 70) return 'YELLOW';
    if (score >= 50) return 'ORANGE';
    return 'RED';
  }

  generateChangesReport(deviceNames) {
    const changes = {};

    deviceNames.forEach(device => {
      const data = this.loadDeviceData(device);
      if (data) {
        changes[device] = {
          hasChanges: false,
          items: []
        };

        // For system devices (desktop/laptop), check for system changes
        if (device !== 'iphone' && data.users) {
          changes[device].hasChanges = true;
          changes[device].items.push(`${data.users?.length || 0} users`);
          changes[device].items.push(`${data.services?.length || 0} services`);
          changes[device].items.push(`${data.packages?.length || 0} packages`);
          changes[device].items.push(`${data.cronJobs?.length || 0} cron jobs`);
          changes[device].items.push(`${data.listeningPorts?.length || 0} listening ports`);
        }

        // For iPhone, check for device changes
        if (device === 'iphone') {
          changes[device].hasChanges = data.iosVersion ? true : false;
          if (data.iosVersion) changes[device].items.push(`iOS ${data.iosVersion}`);
          if (data.security?.passcodeEnabled) changes[device].items.push('Passcode enabled');
          if (data.network?.vpnConnected) changes[device].items.push('VPN connected');
        }
      }
    });

    return changes;
  }

  generateCrossDeviceRisks(deviceNames) {
    const risks = [];

    deviceNames.forEach(device => {
      const data = this.loadDeviceData(device);
      if (!data) return;

      // Generate device-specific risks
      if (device === 'iphone' && data.network) {
        if (!data.network.vpnConnected) {
          risks.push({
            device,
            severity: 'HIGH',
            title: 'VPN Disconnected',
            description: 'iPhone not connected to VPN',
            confidence: 100,
            evidence: 1
          });
        }
        if (!data.network.dnsOverHttps) {
          risks.push({
            device,
            severity: 'MEDIUM',
            title: 'DNS Over HTTPS Disabled',
            description: 'DNS queries not encrypted',
            confidence: 95,
            evidence: 1
          });
        }
      }

      // For system devices
      if (device !== 'iphone' && data.securityEvents) {
        if (data.securityEvents.failedLogins > 5) {
          risks.push({
            device,
            severity: 'HIGH',
            title: 'Multiple Failed Logins',
            description: `${data.securityEvents.failedLogins} failed login attempts`,
            confidence: 100,
            evidence: data.securityEvents.failedLogins
          });
        }
      }
    });

    // Sort by severity
    const severityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
    return risks.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]).slice(0, 5);
  }

  generateRecommendations(risks) {
    const recommendations = [];

    risks.slice(0, 3).forEach(risk => {
      recommendations.push({
        device: risk.device,
        title: `[${risk.device.toUpperCase()}] ${risk.title}`,
        priority: risk.severity === 'CRITICAL' ? 'P1' : risk.severity === 'HIGH' ? 'P2' : 'P3',
        evidence: risk.evidence,
        confidence: risk.confidence
      });
    });

    // Add system-level recommendations
    if (recommendations.length < 5) {
      recommendations.push({
        device: 'system',
        title: 'Review cross-device security posture',
        priority: 'P3',
        evidence: 1,
        confidence: 90
      });
    }

    return recommendations.slice(0, 5);
  }

  generateLessonsLearned() {
    const lessons = [];

    // Load lessons from nightly state if available
    const lessonsPath = path.join(this.devicesStateDir, 'nightly-state', 'lessons.json');
    if (fs.existsSync(lessonsPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(lessonsPath, 'utf8'));
        if (Array.isArray(data)) {
          lessons.push(...data.slice(0, 3));
        }
      } catch (e) {
        // Continue without lessons
      }
    }

    // Add multi-device specific lessons
    lessons.push({
      type: 'Multi-Device Insight',
      description: 'Cross-device monitoring enabled for unified security posture'
    });

    return lessons.slice(0, 4);
  }

  generateHTML(overallScore, threatLevel, deviceScores, changes, risks, recommendations, lessons) {
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

    const deviceNames = Object.keys(deviceScores);
    const totalChanges = Object.values(changes).reduce((sum, d) => sum + (d.hasChanges ? 1 : 0), 0);

    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Multi-Device Security Brief - ${new Date().toISOString().split('T')[0]}</title>
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
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
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
    .device-label { font-size: 10px; opacity: 0.7; margin-top: 2px; }
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
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
    .device-name { font-weight: bold; color: #1f2937; margin-bottom: 4px; }
    .device-score { font-size: 20px; font-weight: bold; color: #3b82f6; }
    .device-status { font-size: 11px; color: #6b7280; margin-top: 4px; }
    .risk {
      background: #fef2f2;
      border-left: 4px solid #f97316;
      padding: 12px;
      margin-bottom: 8px;
      border-radius: 4px;
    }
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
    .confidence-badge {
      display: inline-block;
      background: #dbeafe;
      color: #0c4a6e;
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
    .lesson-item {
      background: #ecfdf5;
      border-left: 3px solid #10b981;
      padding: 12px;
      margin-bottom: 8px;
      border-radius: 4px;
    }
    .lesson-type {
      font-size: 10px;
      font-weight: bold;
      color: #047857;
      margin-bottom: 4px;
    }
    .lesson-desc { font-size: 13px; color: #1f2937; }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
    }
    .full-width { grid-column: 1/-1; }
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
          <div class="header-title">Multi-Device Security Brief</div>
          <div style="font-size: 12px; opacity: 0.8; margin-top: 4px;">
            ${deviceNames.join(' + ')} | ${new Date().toISOString().split('T')[0]}
          </div>
        </div>
        <div class="threat-badge">${threatLabels[threatLevel]}</div>
      </div>
      <div class="score-grid">
        <div class="score-card">
          <div class="score-value">${overallScore}</div>
          <div class="score-label">OVERALL SCORE</div>
        </div>
        ${deviceNames.map(device => `
          <div class="score-card">
            <div class="score-value">${deviceScores[device] || '—'}</div>
            <div class="score-label">${device.toUpperCase()}</div>
            <div class="device-label">Score</div>
          </div>
        `).join('')}
      </div>
    </div>

    <div class="content">
      <div class="grid">
        <div>
          <div class="section">
            <div class="section-title">Device Security Status</div>
            <div class="device-grid">
              ${deviceNames.map(device => `
                <div class="device-box">
                  <div class="device-name">📱 ${device.charAt(0).toUpperCase() + device.slice(1)}</div>
                  <div class="device-score">${deviceScores[device] || '—'}/100</div>
                  <div class="device-status">
                    ${changes[device]?.hasChanges ? '✓ Changes detected' : '✓ No changes'}
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>

        <div>
          <div class="section">
            <div class="section-title">Summary Statistics</div>
            <div style="background: #f3f4f6; padding: 12px; border-radius: 4px; margin-bottom: 8px;">
              <div style="font-size: 13px; color: #6b7280; margin-bottom: 8px;">
                <strong>Devices Monitored:</strong> ${deviceNames.length}
              </div>
              <div style="font-size: 13px; color: #6b7280; margin-bottom: 8px;">
                <strong>Changes Detected:</strong> ${totalChanges}
              </div>
              <div style="font-size: 13px; color: #6b7280;">
                <strong>Active Risks:</strong> ${risks.length}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="section">
        <div class="section-title">Top Risks (${risks.length})</div>
        ${risks.length === 0
          ? '<div style="color: #6b7280; font-size: 13px;">✓ No critical risks detected</div>'
          : risks.map(risk => `
              <div class="risk ${risk.severity.toLowerCase()}">
                <span class="risk-device">${risk.device.toUpperCase()}</span>
                <span style="font-weight: bold;">${risk.title}</span>
                <div class="risk-meta">
                  ${risk.description} |
                  Confidence: <span class="confidence-badge">${risk.confidence}%</span>
                </div>
              </div>
            `).join('')
        }
      </div>

      <div class="section">
        <div class="section-title">Recommendations (${recommendations.length})</div>
        ${recommendations.map(rec => `
          <div class="recommendation">
            <div class="rec-title">${rec.title}</div>
            <div class="rec-meta">
              <div>Priority: <span class="rec-badge priority-${rec.priority.toLowerCase()}">${rec.priority}</span></div>
              <div>Confidence: <span style="font-weight: bold;">${rec.confidence}%</span></div>
              <div>Evidence: ${rec.evidence} signals</div>
            </div>
          </div>
        `).join('')}
      </div>

      <div class="section">
        <div class="section-title">Lessons Learned (${lessons.length})</div>
        ${lessons.map(lesson => `
          <div class="lesson-item">
            <div class="lesson-type">${lesson.type || 'Finding'}</div>
            <div class="lesson-desc">${lesson.description || lesson}</div>
          </div>
        `).join('')}
      </div>
    </div>
  </div>
</body>
</html>`;

    return html;
  }

  generateBrief() {
    const today = new Date().toISOString().split('T')[0];
    const deviceNames = ['desktop', 'laptop', 'iphone'];

    // Load device scores from briefs
    const deviceScores = {};
    deviceNames.forEach(device => {
      const brief = this.loadDeviceBrief(device);
      const score = this.extractScoreFromBrief(brief);
      deviceScores[device] = score;
    });

    // Calculate overall score
    const overallScore = this.calculateOverallScore(deviceScores);
    const threatLevel = this.determineThreatLevel(overallScore);

    // Generate cross-device analysis
    const changes = this.generateChangesReport(deviceNames);
    const risks = this.generateCrossDeviceRisks(deviceNames);
    const recommendations = this.generateRecommendations(risks);
    const lessons = this.generateLessonsLearned();

    // Generate HTML
    const html = this.generateHTML(overallScore, threatLevel, deviceScores, changes, risks, recommendations, lessons);

    // Save to local file
    const localFilename = `multi-device-security-brief-${today}.html`;
    fs.writeFileSync(localFilename, html);

    // Archive to reports
    const archivedFilename = path.join(this.reportsDir, `${today}.html`);
    fs.writeFileSync(archivedFilename, html);

    // Output summary
    console.log(`✓ Multi-Device Security Brief generated`);
    console.log(`  File: ${localFilename}`);
    console.log(`  Overall Score: ${overallScore}/100`);
    console.log(`  Threat Level: ${threatLevel}`);
    console.log(`  Desktop Score: ${deviceScores.desktop || 'N/A'}/100`);
    console.log(`  Laptop Score: ${deviceScores.laptop || 'N/A'}/100`);
    console.log(`  iPhone Score: ${deviceScores.iphone || 'N/A'}/100`);
    console.log(`  Top Risks: ${risks.length}`);
    console.log(`  Recommendations: ${recommendations.length}`);
  }
}

// Execute
const briefer = new MultiDeviceSecurityBrief();
briefer.generateBrief();

export { MultiDeviceSecurityBrief };
