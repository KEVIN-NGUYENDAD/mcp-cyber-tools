const TelegramBot = require('node-telegram-bot-api');
const fs = require('fs');
const path = require('path');

class TelegramCommandCenter {
  constructor() {
    this.token = process.env.TELEGRAM_BOT_TOKEN;
    this.chatId = process.env.TELEGRAM_CHAT_ID;
    this.bot = new TelegramBot(this.token, { polling: false });
    this.setupHandlers();
  }

  setupHandlers() {
    // Command handlers
    this.bot.onText(/\/start/, (msg) => this.handleStart(msg));
    this.bot.onText(/\/status/, (msg) => this.handleStatus(msg));
    this.bot.onText(/\/open/, (msg) => this.handleOpen(msg));
    this.bot.onText(/\/executive/, (msg) => this.handleExecutive(msg));
    this.bot.onText(/\/analytics/, (msg) => this.handleAnalytics(msg));
    this.bot.onText(/\/incidents/, (msg) => this.handleIncidents(msg));

    // Callback handlers for inline buttons
    this.bot.on('callback_query', (query) => this.handleCallbackQuery(query));
  }

  async handleStart(msg) {
    const welcome = `
🛡️ *SentinelOps Command Center*

Mobile SOC Console for Real-Time Threat Monitoring

Available Commands:
• /status - System status overview
• /open - List all open incidents
• /executive - Executive dashboard
• /incidents - All incidents by severity

Use inline buttons on alerts to:
📋 View incident details
📚 Read threat runbook
🔍 Validate evidence
✅ Record approval
❌ Close incident
    `.trim();

    await this.bot.sendMessage(msg.chat.id, welcome, { parse_mode: 'Markdown' });
  }

  async handleStatus(msg) {
    try {
      const stateDir = path.join(process.cwd(), 'state');

      let riskScore = { overall_score: 0 };
      let assets = { total_assets: 0 };
      let incidents = { total_incidents: 0, critical: 0, high: 0 };
      let pipeline = { status: 'unknown' };

      // Read risk score
      if (fs.existsSync(path.join(stateDir, 'risk_score.json'))) {
        riskScore = JSON.parse(fs.readFileSync(path.join(stateDir, 'risk_score.json'), 'utf8'));
      }

      // Read assets
      if (fs.existsSync(path.join(stateDir, 'assets.json'))) {
        assets = JSON.parse(fs.readFileSync(path.join(stateDir, 'assets.json'), 'utf8'));
      }

      // Read incidents
      if (fs.existsSync(path.join(stateDir, 'incidents.json'))) {
        incidents = JSON.parse(fs.readFileSync(path.join(stateDir, 'incidents.json'), 'utf8'));
      }

      // Read pipeline status
      if (fs.existsSync(path.join(stateDir, 'pipeline_results.json'))) {
        const pipelineData = JSON.parse(fs.readFileSync(path.join(stateDir, 'pipeline_results.json'), 'utf8'));
        pipeline = pipelineData.summary || pipelineData;
      }

      const criticalCount = incidents.by_severity?.CRITICAL || 0;
      const highCount = incidents.by_severity?.HIGH || 0;

      const statusMsg = `
🛡 *SENTINELOPS STATUS*

*Risk Assessment*
🎯 Overall Score: ${riskScore.overall_score}/100 ${this.getRiskEmoji(riskScore.overall_score)}

*Assets & Threats*
🖥️ Devices: ${assets.total_assets}
⚠️ Incidents: ${incidents.total_incidents}
🔴 Critical: ${criticalCount}
🟠 High: ${highCount}

*Pipeline Health*
${pipeline.status === 'success' ? '✅' : '⚠️'} Last Run: ${pipeline.timestamp || 'Unknown'}

*Threat Hunting*
🎯 Patterns: 21 Detection Stages Active
🔍 Status: Monitoring
      `.trim();

      await this.bot.sendMessage(msg.chat.id, statusMsg, { parse_mode: 'Markdown' });
    } catch (error) {
      console.error('Error in handleStatus:', error);
      await this.bot.sendMessage(msg.chat.id, '❌ Error retrieving status');
    }
  }

  async handleOpen(msg) {
    try {
      const incidentsPath = path.join(process.cwd(), 'state', 'incidents.json');

      if (!fs.existsSync(incidentsPath)) {
        await this.bot.sendMessage(msg.chat.id, 'No incident data found');
        return;
      }

      const incidents = JSON.parse(fs.readFileSync(incidentsPath, 'utf8'));

      const critical = incidents.incidents?.filter(i => i.severity === 'CRITICAL') || [];
      const high = incidents.incidents?.filter(i => i.severity === 'HIGH') || [];
      const medium = incidents.incidents?.filter(i => i.severity === 'MEDIUM') || [];
      const low = incidents.incidents?.filter(i => i.severity === 'LOW') || [];

      let openList = `*Open Incidents by Severity*\n\n`;

      if (critical.length > 0) {
        openList += `🔴 *CRITICAL (${critical.length})*\n`;
        critical.slice(0, 5).forEach(inc => {
          openList += `• ${inc.id}: ${inc.threat_name}\n`;
        });
        openList += '\n';
      }

      if (high.length > 0) {
        openList += `🟠 *HIGH (${high.length})*\n`;
        high.slice(0, 5).forEach(inc => {
          openList += `• ${inc.id}: ${inc.threat_name}\n`;
        });
        openList += '\n';
      }

      if (medium.length > 0) {
        openList += `🟡 *MEDIUM (${medium.length})*\n`;
        medium.slice(0, 5).forEach(inc => {
          openList += `• ${inc.id}: ${inc.threat_name}\n`;
        });
      }

      if (low.length > 0) {
        openList += `🟢 *LOW (${low.length})*\n`;
        low.slice(0, 3).forEach(inc => {
          openList += `• ${inc.id}: ${inc.threat_name}\n`;
        });
      }

      await this.bot.sendMessage(msg.chat.id, openList, { parse_mode: 'Markdown' });
    } catch (error) {
      console.error('Error in handleOpen:', error);
      await this.bot.sendMessage(msg.chat.id, '❌ Error retrieving incidents');
    }
  }

  async handleExecutive(msg) {
    try {
      const stateDir = path.join(process.cwd(), 'state');

      let metrics = {
        assets: 0,
        incidents: 0,
        critical: 0,
        high: 0,
        risk: 0,
        waap: 0,
        domain: 'unknown',
        pipeline: 'unknown'
      };

      // Read all metrics
      if (fs.existsSync(path.join(stateDir, 'assets.json'))) {
        const assets = JSON.parse(fs.readFileSync(path.join(stateDir, 'assets.json'), 'utf8'));
        metrics.assets = assets.total_assets || 0;
      }

      if (fs.existsSync(path.join(stateDir, 'incidents.json'))) {
        const incidents = JSON.parse(fs.readFileSync(path.join(stateDir, 'incidents.json'), 'utf8'));
        metrics.incidents = incidents.total_incidents || 0;
        metrics.critical = incidents.by_severity?.CRITICAL || 0;
        metrics.high = incidents.by_severity?.HIGH || 0;
      }

      if (fs.existsSync(path.join(stateDir, 'risk_score.json'))) {
        const risk = JSON.parse(fs.readFileSync(path.join(stateDir, 'risk_score.json'), 'utf8'));
        metrics.risk = risk.overall_score || 0;
      }

      if (fs.existsSync(path.join(stateDir, 'waap_status.json'))) {
        const waap = JSON.parse(fs.readFileSync(path.join(stateDir, 'waap_status.json'), 'utf8'));
        metrics.waap = waap.health_score || 0;
      }

      if (fs.existsSync(path.join(stateDir, 'domain_status.json'))) {
        const domain = JSON.parse(fs.readFileSync(path.join(stateDir, 'domain_status.json'), 'utf8'));
        metrics.domain = domain.dns_health || 'unknown';
      }

      if (fs.existsSync(path.join(stateDir, 'pipeline_results.json'))) {
        const pipeline = JSON.parse(fs.readFileSync(path.join(stateDir, 'pipeline_results.json'), 'utf8'));
        metrics.pipeline = pipeline.summary?.status || 'unknown';
      }

      const execMsg = `
*EXECUTIVE DASHBOARD*

📊 *Asset Inventory*
${metrics.assets} Devices Monitored

🚨 *Threat Landscape*
${metrics.incidents} Open Incidents
🔴 ${metrics.critical} Critical
🟠 ${metrics.high} High Severity

🎯 *Risk Assessment*
${metrics.risk}/100 (${this.getRiskLevel(metrics.risk)})

🔒 *Web Application Protection*
Score: ${metrics.waap}/100

🌐 *Domain Health*
DNS: ${metrics.domain}

⚙️ *Pipeline Status*
${metrics.pipeline === 'success' ? '✅ Healthy' : '⚠️ Check Required'}
      `.trim();

      await this.bot.sendMessage(msg.chat.id, execMsg, { parse_mode: 'Markdown' });
    } catch (error) {
      console.error('Error in handleExecutive:', error);
      await this.bot.sendMessage(msg.chat.id, '❌ Error retrieving dashboard');
    }
  }

  async handleAnalytics(msg) {
    try {
      const stateDir = path.join(process.cwd(), 'state');

      let analytics = {
        vulnerabilities: 0,
        issues: 0,
        scannedAssets: 0,
        appSecurityScore: 0,
        incidents: 0,
        critical: 0,
        high: 0
      };

      // Read vulnerabilities from assets
      if (fs.existsSync(path.join(stateDir, 'assets.json'))) {
        const assets = JSON.parse(fs.readFileSync(path.join(stateDir, 'assets.json'), 'utf8'));
        const assetList = assets.assets || [];

        analytics.scannedAssets = assetList.length;

        // Sum all vulnerabilities
        assetList.forEach(asset => {
          analytics.vulnerabilities += asset.vulnerability_count || 0;
          analytics.issues += (asset.critical || 0) + (asset.high || 0) + (asset.medium || 0) + (asset.low || 0) + (asset.info || 0);
        });
      }

      // Read incidents for threat detection
      if (fs.existsSync(path.join(stateDir, 'incidents.json'))) {
        const incidents = JSON.parse(fs.readFileSync(path.join(stateDir, 'incidents.json'), 'utf8'));
        analytics.incidents = incidents.total_incidents || 0;
        analytics.critical = incidents.by_severity?.CRITICAL || 0;
        analytics.high = incidents.by_severity?.HIGH || 0;
      }

      // Read WAAP for application security score
      if (fs.existsSync(path.join(stateDir, 'waap_status.json'))) {
        const waap = JSON.parse(fs.readFileSync(path.join(stateDir, 'waap_status.json'), 'utf8'));
        // Calculate score: SSL valid (60pts) + security features (40pts)
        let score = 0;
        if (waap.security_summary?.ssl_valid) score += 60;
        if (waap.security_summary?.waf_active) score += 15;
        if (waap.security_summary?.cdn_active) score += 15;
        if (waap.security_summary?.protection_active) score += 10;
        analytics.appSecurityScore = score;
      }

      const analyticsMsg = `
📊 *SECURITY ANALYTICS*

*Vulnerability Assessment*
📈 ${analytics.vulnerabilities} Vulnerabilities Found
📋 ${analytics.issues} Issues Aggregated
🔍 Scan Coverage: ${analytics.scannedAssets} Assets

*Threat Detection*
🚨 ${analytics.incidents} Incidents Detected
🔴 ${analytics.critical} Critical
🟠 ${analytics.high} High Severity

*Application Security*
🔒 Score: ${analytics.appSecurityScore}/100
${analytics.appSecurityScore >= 80 ? '✅ Strong Security Posture' : analytics.appSecurityScore >= 60 ? '⚠️ Adequate Protection' : '❌ Enhanced Protection Needed'}
      `.trim();

      await this.bot.sendMessage(msg.chat.id, analyticsMsg, { parse_mode: 'Markdown' });
    } catch (error) {
      console.error('Error in handleAnalytics:', error);
      await this.bot.sendMessage(msg.chat.id, '❌ Error retrieving analytics');
    }
  }

  async handleIncidents(msg) {
    try {
      const incidentsPath = path.join(process.cwd(), 'state', 'incidents.json');

      if (!fs.existsSync(incidentsPath)) {
        await this.bot.sendMessage(msg.chat.id, 'No incident data found');
        return;
      }

      const incidents = JSON.parse(fs.readFileSync(incidentsPath, 'utf8'));
      const allIncidents = incidents.incidents || [];

      // Create keyboard with first 5 incidents
      const keyboard = [];
      allIncidents.slice(0, 5).forEach(incident => {
        keyboard.push([{
          text: `${incident.id}: ${incident.threat_name}`,
          callback_data: `details_${incident.id}`
        }]);
      });

      const options = {
        reply_markup: {
          inline_keyboard: keyboard
        },
        parse_mode: 'Markdown'
      };

      await this.bot.sendMessage(
        msg.chat.id,
        `*Recent Incidents* (${allIncidents.length} total)\n\nSelect to view details:`,
        options
      );
    } catch (error) {
      console.error('Error in handleIncidents:', error);
      await this.bot.sendMessage(msg.chat.id, '❌ Error retrieving incidents');
    }
  }

  async handleCallbackQuery(query) {
    const action = query.data.split('_')[0];
    const incidentId = query.data.split('_')[1];

    try {
      switch (action) {
        case 'details':
          await this.showIncidentDetails(query.message.chat.id, incidentId, query.id);
          break;
        case 'runbook':
          await this.showRunbook(query.message.chat.id, incidentId, query.id);
          break;
        case 'validate':
          await this.showValidation(query.message.chat.id, incidentId, query.id);
          break;
        case 'approve':
          await this.showApproval(query.message.chat.id, incidentId, query.id);
          break;
        case 'close':
          await this.closeIncident(query.message.chat.id, incidentId, query.id);
          break;
        default:
          await this.bot.answerCallbackQuery(query.id, 'Unknown action');
      }
    } catch (error) {
      console.error('Error in handleCallbackQuery:', error);
      await this.bot.answerCallbackQuery(query.id, '❌ Error processing action');
    }
  }

  async showIncidentDetails(chatId, incidentId, queryId) {
    try {
      const incident = await this.getIncident(incidentId);

      if (!incident) {
        await this.bot.answerCallbackQuery(queryId, 'Incident not found');
        return;
      }

      const details = `
*Incident Details*

📋 *ID*: ${incident.id}
🎯 *Threat*: ${incident.threat_name}
🔴 *Severity*: ${incident.severity}
📊 *Confidence*: ${incident.confidence || 'N/A'}%
💯 *Risk Score*: ${incident.risk_score || 'N/A'}/100

🖥️ *Host*: ${incident.host || 'Unknown'}
⏰ *Timestamp*: ${incident.timestamp || 'Unknown'}
📁 *Status*: ${incident.status || 'Open'}

📝 *Evidence*: ${(incident.evidence || []).length} indicators
✅ *Recommendation*: ${incident.recommendation || 'No recommendation'}
      `.trim();

      const keyboard = [
        [
          { text: '📚 Runbook', callback_data: `runbook_${incidentId}` },
          { text: '🔍 Validate', callback_data: `validate_${incidentId}` }
        ],
        [
          { text: '✅ Approve', callback_data: `approve_${incidentId}` },
          { text: '❌ Close', callback_data: `close_${incidentId}` }
        ]
      ];

      await this.bot.editMessageText(details, {
        chat_id: chatId,
        message_id: undefined,
        reply_markup: { inline_keyboard: keyboard },
        parse_mode: 'Markdown'
      });

      await this.bot.answerCallbackQuery(queryId);
    } catch (error) {
      console.error('Error in showIncidentDetails:', error);
      await this.bot.answerCallbackQuery(queryId, '❌ Error loading details');
    }
  }

  async showRunbook(chatId, incidentId, queryId) {
    try {
      const incident = await this.getIncident(incidentId);

      if (!incident) {
        await this.bot.answerCallbackQuery(queryId, 'Incident not found');
        return;
      }

      const runbook = `
*Threat Runbook*

📘 *Threat*: ${incident.threat_name}
🎯 *Category*: ${incident.threat_category || 'Unknown'}

*Investigation Steps:*
1. Review incident evidence
2. Check system logs
3. Verify process behavior
4. Cross-reference IOCs

*Validation Criteria:*
✓ Evidence present
✓ Timeline consistent
✓ Indicators confirmed
✓ Impact assessed

*Remediation Steps:*
1. Isolate affected system
2. Preserve forensic evidence
3. Block malicious indicators
4. Remove persistence mechanisms
5. Restore from clean backup
      `.trim();

      const keyboard = [
        [
          { text: '◀️ Back', callback_data: `details_${incidentId}` },
          { text: '🔍 Validate', callback_data: `validate_${incidentId}` }
        ],
        [
          { text: '✅ Approve', callback_data: `approve_${incidentId}` },
          { text: '❌ Close', callback_data: `close_${incidentId}` }
        ]
      ];

      await this.bot.editMessageText(runbook, {
        chat_id: chatId,
        message_id: undefined,
        reply_markup: { inline_keyboard: keyboard },
        parse_mode: 'Markdown'
      });

      await this.bot.answerCallbackQuery(queryId);
    } catch (error) {
      console.error('Error in showRunbook:', error);
      await this.bot.answerCallbackQuery(queryId, '❌ Error loading runbook');
    }
  }

  async showValidation(chatId, incidentId, queryId) {
    try {
      const incident = await this.getIncident(incidentId);

      if (!incident) {
        await this.bot.answerCallbackQuery(queryId, 'Incident not found');
        return;
      }

      let evidenceList = '';
      if (incident.evidence && Array.isArray(incident.evidence)) {
        incident.evidence.slice(0, 5).forEach((ev, i) => {
          evidenceList += `${i + 1}. ${ev}\n`;
        });
      }

      const validation = `
*Evidence Validation*

🔍 *Evidence Collected*:
${evidenceList || 'No evidence'}

*True Positive Indicators:*
✓ Multiple evidence points
✓ Consistent detection method
✓ System impact confirmed
✓ Recommended action clear

*False Positive Filters:*
✗ Single indicator only
✗ Known false positive pattern
✗ System misconfiguration
✗ User testing activity

*Confidence Score*: ${incident.confidence || 0}%
      `.trim();

      const keyboard = [
        [
          { text: '◀️ Back', callback_data: `details_${incidentId}` },
          { text: '✅ Approve', callback_data: `approve_${incidentId}` }
        ],
        [
          { text: '❌ Close', callback_data: `close_${incidentId}` }
        ]
      ];

      await this.bot.editMessageText(validation, {
        chat_id: chatId,
        message_id: undefined,
        reply_markup: { inline_keyboard: keyboard },
        parse_mode: 'Markdown'
      });

      await this.bot.answerCallbackQuery(queryId);
    } catch (error) {
      console.error('Error in showValidation:', error);
      await this.bot.answerCallbackQuery(queryId, '❌ Error loading validation');
    }
  }

  async showApproval(chatId, incidentId, queryId) {
    try {
      const incident = await this.getIncident(incidentId);

      if (!incident) {
        await this.bot.answerCallbackQuery(queryId, 'Incident not found');
        return;
      }

      // Record approval in audit trail
      this.recordApproval(incidentId);

      const approval = `
✅ *APPROVAL RECORDED*

📋 *Incident*: ${incident.id}
🎯 *Threat*: ${incident.threat_name}
⏰ *Approved*: ${new Date().toISOString()}
👤 *Approver*: SentinelOps Console
🔐 *Audit Entry*: Created

*Status*: ${incident.status || 'Open'}
*Action*: Awaiting manual remediation by SOC team

⚠️ *Note*: No destructive actions will be executed automatically.
All remediation requires explicit human authorization.
      `.trim();

      const keyboard = [
        [
          { text: '📋 Details', callback_data: `details_${incidentId}` },
          { text: '❌ Close', callback_data: `close_${incidentId}` }
        ]
      ];

      await this.bot.editMessageText(approval, {
        chat_id: chatId,
        message_id: undefined,
        reply_markup: { inline_keyboard: keyboard },
        parse_mode: 'Markdown'
      });

      await this.bot.answerCallbackQuery(queryId, 'Approval recorded');
    } catch (error) {
      console.error('Error in showApproval:', error);
      await this.bot.answerCallbackQuery(queryId, '❌ Error recording approval');
    }
  }

  async closeIncident(chatId, incidentId, queryId) {
    try {
      const incident = await this.getIncident(incidentId);

      if (!incident) {
        await this.bot.answerCallbackQuery(queryId, 'Incident not found');
        return;
      }

      // Update incident status
      this.updateIncidentStatus(incidentId, 'Closed');

      const closed = `
❌ *INCIDENT CLOSED*

📋 *Incident*: ${incident.id}
🎯 *Threat*: ${incident.threat_name}
⏰ *Closed*: ${new Date().toISOString()}
👤 *Closed By*: SentinelOps Console

*Previous Status*: ${incident.status || 'Open'}
*New Status*: Closed

*Archive*: Available for audit trail review
      `.trim();

      const keyboard = [
        [
          { text: '📋 Details', callback_data: `details_${incidentId}` }
        ]
      ];

      await this.bot.editMessageText(closed, {
        chat_id: chatId,
        message_id: undefined,
        reply_markup: { inline_keyboard: keyboard },
        parse_mode: 'Markdown'
      });

      await this.bot.answerCallbackQuery(queryId, 'Incident closed');
    } catch (error) {
      console.error('Error in closeIncident:', error);
      await this.bot.answerCallbackQuery(queryId, '❌ Error closing incident');
    }
  }

  async getIncident(incidentId) {
    try {
      const incidentsPath = path.join(process.cwd(), 'state', 'incidents.json');
      if (!fs.existsSync(incidentsPath)) return null;

      const data = JSON.parse(fs.readFileSync(incidentsPath, 'utf8'));
      const incidents = data.incidents || [];

      return incidents.find(i => i.id === incidentId) || null;
    } catch (error) {
      console.error('Error in getIncident:', error);
      return null;
    }
  }

  recordApproval(incidentId) {
    try {
      const auditPath = path.join(process.cwd(), 'state', 'approval_audit.json');
      let audits = [];

      if (fs.existsSync(auditPath)) {
        audits = JSON.parse(fs.readFileSync(auditPath, 'utf8'));
      }

      audits.push({
        incident_id: incidentId,
        timestamp: new Date().toISOString(),
        action: 'APPROVED',
        approver: 'TelegramConsole',
        status: 'RECORDED'
      });

      fs.writeFileSync(auditPath, JSON.stringify(audits, null, 2), 'utf8');
    } catch (error) {
      console.error('Error recording approval:', error);
    }
  }

  updateIncidentStatus(incidentId, newStatus) {
    try {
      const incidentsPath = path.join(process.cwd(), 'state', 'incidents.json');
      if (!fs.existsSync(incidentsPath)) return;

      const data = JSON.parse(fs.readFileSync(incidentsPath, 'utf8'));
      const incidents = data.incidents || [];

      const incident = incidents.find(i => i.id === incidentId);
      if (incident) {
        incident.status = newStatus;
        incident.updated_at = new Date().toISOString();
      }

      fs.writeFileSync(incidentsPath, JSON.stringify(data, null, 2), 'utf8');
    } catch (error) {
      console.error('Error updating incident status:', error);
    }
  }

  getRiskEmoji(score) {
    if (score >= 80) return '🔴';
    if (score >= 60) return '🟠';
    if (score >= 40) return '🟡';
    return '🟢';
  }

  getRiskLevel(score) {
    if (score >= 80) return 'CRITICAL';
    if (score >= 60) return 'HIGH';
    if (score >= 40) return 'MEDIUM';
    return 'LOW';
  }

  async sendAlertWithButtons(incident) {
    try {
      const alertText = `
🚨 *SECURITY ALERT*

📋 *Incident*: ${incident.id}
🎯 *Threat*: ${incident.threat_name}
🔴 *Severity*: ${incident.severity}
💯 *Risk*: ${incident.risk_score || 'N/A'}/100

🖥️ *Host*: ${incident.host || 'Unknown'}
⏰ *Time*: ${incident.timestamp || new Date().toISOString()}

*Select action:*
      `.trim();

      const keyboard = [
        [
          { text: '📋 Details', callback_data: `details_${incident.id}` },
          { text: '📚 Runbook', callback_data: `runbook_${incident.id}` }
        ],
        [
          { text: '🔍 Validate', callback_data: `validate_${incident.id}` },
          { text: '✅ Approve', callback_data: `approve_${incident.id}` }
        ],
        [
          { text: '❌ Close', callback_data: `close_${incident.id}` }
        ]
      ];

      const options = {
        chat_id: this.chatId,
        parse_mode: 'Markdown',
        reply_markup: {
          inline_keyboard: keyboard
        }
      };

      const result = await this.bot.sendMessage(this.chatId, alertText, options);
      return result;
    } catch (error) {
      console.error('Error sending alert with buttons:', error);
      throw error;
    }
  }

  getBot() {
    return this.bot;
  }
}

module.exports = TelegramCommandCenter;
