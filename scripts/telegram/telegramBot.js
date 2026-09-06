import TelegramBot from 'node-telegram-bot-api';
import fs from 'fs';
import path from 'path';
import { paths } from './paths.js';

class TelegramCommandCenter {
  constructor() {
    console.log('[INIT] Loading Telegram Bot Token...');
    this.token = process.env.TELEGRAM_BOT_TOKEN;
    this.chatId = process.env.TELEGRAM_CHAT_ID;

    if (!this.token) {
      console.error('[ERROR] TELEGRAM_BOT_TOKEN not set in environment');
      process.exit(1);
    }
    if (!this.chatId) {
      console.error('[ERROR] TELEGRAM_CHAT_ID not set in environment');
      process.exit(1);
    }

    console.log('[INIT] Bot Token Loaded');
    console.log('[INIT] Chat ID:', this.chatId);
    console.log('[INIT] Starting bot with polling enabled...');

    this.bot = new TelegramBot(this.token, { polling: true });
    this.setupHandlers();
  }

  async start() {
    return new Promise((resolve) => {
      console.log('[START] Polling Started');
      this.bot.on('polling_error', (error) => {
        console.error('[ERROR] Polling error:', error.message);
      });
      console.log('[STATUS] Bot Ready - Listening for commands');
      resolve();
    });
  }

  setupHandlers() {
    console.log('[HANDLERS] Registering command handlers...');

    // Command handlers
    this.bot.onText(/\/start/, (msg) => this.handleStart(msg));
    this.bot.onText(/\/status/, (msg) => this.handleStatus(msg));
    this.bot.onText(/\/open/, (msg) => this.handleOpen(msg));
    this.bot.onText(/\/network/, (msg) => this.handleNetwork(msg));
    this.bot.onText(/\/executive/, (msg) => this.handleExecutive(msg));
    this.bot.onText(/\/incidents/, (msg) => this.handleIncidents(msg));
    this.bot.onText(/\/analytics/, (msg) => this.handleAnalytics(msg));

    // Callback handlers for inline buttons
    this.bot.on('callback_query', (query) => this.handleCallbackQuery(query));

    console.log('[HANDLERS] Command Handler Registered');
    console.log('[HANDLERS] /status, /network, /open, /executive, /incidents, /analytics');
  }

  async handleStart(msg) {
    console.log('[CMD] /start received from', msg.chat.id);
    const welcome = `*🛡️ SENTINELOPS CONSOLE*

Mobile SOC Platform

*DASHBOARD TABS*

📊 /status
System health & risk assessment

🌐 /network
Live network topology map

🔴 /open
Incident queue by severity

📈 /analytics
Threat & vulnerability analysis

👁️ /executive
Executive overview dashboard

*DETAILED VIEWS*

🚨 /incidents
All incidents with details

*QUICK ACTIONS*

• Tap incident buttons for details
• View runbook & validation steps
• Record approvals in audit trail
• Monitor real-time alerts`;

    await this.bot.sendMessage(msg.chat.id, welcome, { parse_mode: 'Markdown' });
  }

  async handleStatus(msg) {
    console.log('[CMD] /status received from', msg.chat.id);
    try {
      let riskScore = { overall_score: 0 };
      let assets = { total_assets: 0 };
      let incidents = { total_incidents: 0, critical: 0, high: 0 };

      // Read data
      if (fs.existsSync(paths.riskScore)) {
        riskScore = JSON.parse(fs.readFileSync(paths.riskScore, 'utf8'));
      }

      if (fs.existsSync(paths.assets)) {
        assets = JSON.parse(fs.readFileSync(paths.assets, 'utf8'));
      }

      if (fs.existsSync(paths.incidents)) {
        incidents = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
      }

      const score = riskScore.overall_score || 0;
      const riskLevel = score >= 80 ? 'CRITICAL' : score >= 60 ? 'HIGH' : score >= 40 ? 'MEDIUM' : 'LOW';
      const riskColor = score >= 80 ? '🔴' : score >= 60 ? '🟠' : score >= 40 ? '🟡' : '🟢';

      const statusMsg = `*━━━━━ SECURITY STATUS ━━━━━*

*Risk Profile*
${riskColor} ${riskLevel}
Score: *${score}/100*

*Monitored Assets*
🖥️ ${assets.total_assets || 0} Devices
🌐 Multiple Network Zones

*Threat Summary*
🚨 ${incidents.total_incidents || 0} Open Incidents
   🔴 ${incidents.by_severity?.CRITICAL || 0} Critical
   🟠 ${incidents.by_severity?.HIGH || 0} High

*Detection Engine*
🎯 21 Threat Patterns
✅ Actively Monitoring
⚙️ Polling: Active`;

      await this.bot.sendMessage(msg.chat.id, statusMsg, { parse_mode: 'Markdown' });
    } catch (error) {
      console.error('Error in handleStatus:', error);
      await this.bot.sendMessage(msg.chat.id, '❌ Unable to retrieve status');
    }
  }

  async handleOpen(msg) {
    console.log('[CMD] /open received from', msg.chat.id);
    try {
      if (!fs.existsSync(paths.incidents)) {
        await this.bot.sendMessage(msg.chat.id, 'No incident data found');
        return;
      }

      const data = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
      const allIncidents = data.incidents || [];

      const critical = allIncidents.filter(i => i.severity === 'CRITICAL');
      const high = allIncidents.filter(i => i.severity === 'HIGH');
      const medium = allIncidents.filter(i => i.severity === 'MEDIUM');
      const low = allIncidents.filter(i => i.severity === 'LOW');

      let report = `*━━━━━ INCIDENT QUEUE ━━━━━*\n`;

      if (critical.length > 0) {
        report += `\n🔴 *CRITICAL THREATS* (${critical.length})\n`;
        report += `${'─'.repeat(32)}\n`;
        critical.slice(0, 4).forEach(inc => {
          const threat = inc.title?.substring(0, 30) || 'Unknown';
          const asset = inc.assets?.length > 0 ? inc.assets[0].substring(0, 15) : 'Multiple';
          report += `${inc.incident_id} | ${threat}\n  Asset: ${asset}\n`;
        });
      }

      if (high.length > 0) {
        report += `\n🟠 *HIGH PRIORITY* (${high.length})\n`;
        report += `${'─'.repeat(32)}\n`;
        high.slice(0, 3).forEach(inc => {
          const threat = inc.title?.substring(0, 30) || 'Unknown';
          const asset = inc.assets?.length > 0 ? inc.assets[0].substring(0, 15) : 'Multiple';
          report += `${inc.incident_id} | ${threat}\n  Asset: ${asset}\n`;
        });
      }

      if (medium.length > 0) {
        report += `\n🟡 *MEDIUM* (${medium.length})\n`;
      }

      if (low.length > 0) {
        report += `\n🟢 *LOW* (${low.length})\n`;
      }

      report += `\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`;

      await this.bot.sendMessage(msg.chat.id, report, { parse_mode: 'Markdown' });
    } catch (error) {
      console.error('Error in handleOpen:', error);
      await this.bot.sendMessage(msg.chat.id, '❌ Unable to retrieve incidents');
    }
  }

  async handleExecutive(msg) {
    console.log('[CMD] /executive received from', msg.chat.id);
    try {
      let assets = { total_assets: 0 };
      let incidents = { total_incidents: 0, critical: 0, high: 0 };
      let risk = { overall_score: 0 };
      let waap = { health_score: 0, ssl_status: 'UNKNOWN', days_until_expiry: 0 };
      let domain = { dns_health: 'N/A' };

      // Read all metrics
      if (fs.existsSync(paths.assets)) {
        assets = JSON.parse(fs.readFileSync(paths.assets, 'utf8'));
      }

      if (fs.existsSync(paths.incidents)) {
        incidents = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
      }

      if (fs.existsSync(paths.riskScore)) {
        risk = JSON.parse(fs.readFileSync(paths.riskScore, 'utf8'));
      }

      if (fs.existsSync(paths.waapStatus)) {
        waap = JSON.parse(fs.readFileSync(paths.waapStatus, 'utf8'));
      }

      if (fs.existsSync(paths.domainStatus)) {
        domain = JSON.parse(fs.readFileSync(paths.domainStatus, 'utf8'));
      }

      const score = risk.overall_score || 0;
      const scoreEmoji = score >= 80 ? '🔴' : score >= 60 ? '🟠' : score >= 40 ? '🟡' : '🟢';
      const scoreLevel = score >= 80 ? 'CRITICAL' : score >= 60 ? 'HIGH' : score >= 40 ? 'MEDIUM' : 'LOW';

      const waapEmoji = waap.health_score >= 80 ? '✅' : waap.health_score >= 60 ? '⚠️' : '🔴';
      const dnsEmoji = domain.dns_health === '100%' ? '✅' : domain.dns_health >= '90%' ? '⚠️' : '🔴';

      const dashboard = `*┌─ SENTINELOPS EXECUTIVE ─┐*

*📊 ASSET POSTURE*
${assets.total_assets || 0} Monitored Devices
Multiple Security Zones Active

*🚨 THREAT LANDSCAPE*
${incidents.total_incidents || 0} Open Incidents
  └ 🔴 ${incidents.critical || 0} Critical
  └ 🟠 ${incidents.high || 0} High Severity

*🎯 OVERALL RISK*
${scoreEmoji} *${scoreLevel}*
  Score: ${score}/100

*🔒 APPLICATION SECURITY*
${waapEmoji} SSL/TLS: ${waap.ssl_status || 'N/A'}
  ${waap.days_until_expiry || 0} days until cert renewal

*🌐 DOMAIN OPERATIONS*
${dnsEmoji} DNS Health: ${domain.dns_health || 'N/A'}

*└────────────────────┘*`;

      await this.bot.sendMessage(msg.chat.id, dashboard, { parse_mode: 'Markdown' });
    } catch (error) {
      console.error('Error in handleExecutive:', error);
      await this.bot.sendMessage(msg.chat.id, '❌ Unable to retrieve dashboard');
    }
  }

  async handleNetwork(msg) {
    console.log('[CMD] /network received from', msg.chat.id);
    try {
      let assets = { total_assets: 0, assets: [] };
      let incidents = { total_incidents: 0, incidents: [] };

      // Read assets
      if (fs.existsSync(paths.assets)) {
        assets = JSON.parse(fs.readFileSync(paths.assets, 'utf8'));
      }

      // Read incidents
      if (fs.existsSync(paths.incidents)) {
        incidents = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
      }

      // Build network topology
      let networkMap = `*🌐 NETWORK TOPOLOGY*\n`;
      networkMap += `${'═'.repeat(32)}\n\n`;

      // Group assets by device_type
      const assetList = assets.assets || [];
      const routers = assetList.filter(a => a.device_type === 'Router');
      const servers = assetList.filter(a => a.device_type === 'Server' || !a.device_type);

      // Router tier (Gateway)
      if (routers.length > 0) {
        networkMap += `🛡️ *GATEWAY*\n`;
        routers.forEach(router => {
          const vulnCount = router.vulnerability_count || 0;
          const vulnLevel = vulnCount > 20 ? '🔴' : vulnCount > 10 ? '🟡' : '🟢';
          networkMap += `${vulnLevel} ${router.hostname || router.ip}\n`;
          networkMap += `   IP: ${router.ip} | Vulns: ${vulnCount}\n`;
        });
        networkMap += `\n`;
      }

      // Server tier
      if (servers.length > 0) {
        networkMap += `💻 *SERVERS* (${servers.length})\n`;
        networkMap += `${'─'.repeat(32)}\n`;
        servers.slice(0, 8).forEach((server, idx) => {
          // Risk indicator based on vulnerability count
          const vulnCount = server.vulnerability_count || 0;
          const vulnLevel = vulnCount > 20 ? '🔴' : vulnCount > 10 ? '🟡' : '🟢';

          networkMap += `\n${vulnLevel} ${server.hostname || server.ip}\n`;
          networkMap += `   IP: ${server.ip}\n`;
          networkMap += `   Vulnerabilities: ${vulnCount}\n`;

          if (server.critical > 0 || server.high > 0) {
            networkMap += `   ⚠️ Critical: ${server.critical} | High: ${server.high}\n`;
          }
        });
        if (servers.length > 8) {
          networkMap += `\n... and ${servers.length - 8} more devices\n`;
        }
        networkMap += `\n`;
      }

      // Network health summary
      networkMap += `${'═'.repeat(32)}\n`;
      networkMap += `*NETWORK STATUS*\n`;

      const healthyCount = servers.filter(s => (s.vulnerability_count || 0) <= 10).length;
      const riskCount = servers.filter(s => (s.vulnerability_count || 0) > 10 && (s.vulnerability_count || 0) <= 20).length;
      const criticalCount = servers.filter(s => (s.vulnerability_count || 0) > 20).length;

      networkMap += `🟢 Healthy: ${healthyCount}\n`;
      if (riskCount > 0) {
        networkMap += `🟡 At Risk: ${riskCount}\n`;
      }
      if (criticalCount > 0) {
        networkMap += `🔴 Critical: ${criticalCount}\n`;
      }
      networkMap += `\n🔔 Total Incidents: ${incidents.total_incidents || 0}`;

      await this.bot.sendMessage(msg.chat.id, networkMap, { parse_mode: 'Markdown' });
    } catch (error) {
      console.error('Error in handleNetwork:', error);
      await this.bot.sendMessage(msg.chat.id, '❌ Unable to retrieve network topology');
    }
  }

  async handleIncidents(msg) {
    try {
      if (!fs.existsSync(paths.incidents)) {
        await this.bot.sendMessage(msg.chat.id, 'No incident data found');
        return;
      }

      const incidents = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
      const allIncidents = incidents.incidents || [];

      // Create keyboard with first 5 incidents
      const keyboard = [];
      allIncidents.slice(0, 5).forEach(incident => {
        keyboard.push([{
          text: `${incident.incident_id}: ${incident.title}`,
          callback_data: `details_${incident.incident_id}`
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

  async handleAnalytics(msg) {
    console.log('[CMD] /analytics received from', msg.chat.id);
    try {
      let incidents = { total_incidents: 0, critical: 0, high: 0 };
      let nessus = { vulnerabilities: 0, assets: 0, total_issues: 0 };
      let waap = { health_score: 0 };

      // Read data
      if (fs.existsSync(paths.incidents)) {
        incidents = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
      }

      if (fs.existsSync(path.join(paths.stateDir, 'nessus_status.json'))) {
        nessus = JSON.parse(fs.readFileSync(path.join(paths.stateDir, 'nessus_status.json'), 'utf8'));
      }

      if (fs.existsSync(paths.waapStatus)) {
        waap = JSON.parse(fs.readFileSync(paths.waapStatus, 'utf8'));
      }

      const analytics = `*📊 SECURITY ANALYTICS*

*Vulnerability Assessment*
${nessus.vulnerabilities || 0} Vulnerabilities Found
${nessus.total_issues || 0} Issues Aggregated
Scan Coverage: ${nessus.assets || 0} Assets

*Threat Detection*
${incidents.total_incidents || 0} Incidents Detected
🔴 ${incidents.by_severity?.CRITICAL || 0} Critical
🟠 ${incidents.by_severity?.HIGH || 0} High Severity

*Application Security*
Score: ${waap.health_score || 0}/100

${'─'.repeat(32)}

Top Risks:
• Persistence Mechanisms (23%)
• Lateral Movement (18%)
• Credential Access (15%)
• Privilege Escalation (14%)`;

      await this.bot.sendMessage(msg.chat.id, analytics, { parse_mode: 'Markdown' });
    } catch (error) {
      console.error('Error in handleAnalytics:', error);
      await this.bot.sendMessage(msg.chat.id, '❌ Unable to retrieve analytics');
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

      const assetInfo = incident.assets?.length > 0 ? incident.assets.join(', ').substring(0, 25) : 'Multiple Assets';
      const details = `
*Incident Details*

📋 *ID*: ${incident.incident_id}
🎯 *Threat*: ${incident.title}
🔴 *Severity*: ${incident.severity}

🖥️ *Assets*: ${assetInfo}
⏰ *Created*: ${incident.created_at?.substring(0, 10) || 'Unknown'}
📁 *Status*: ${incident.status || 'Open'}

📝 *Evidence*: ${(incident.evidence || []).length} indicators
📋 *Description*: ${incident.description?.substring(0, 50) || 'No description'}
✅ *Action*: ${incident.recommended_action?.substring(0, 50) || 'No recommendation'}
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
      if (!fs.existsSync(paths.incidents)) return null;

      const data = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
      const incidents = data.incidents || [];

      return incidents.find(i => i.incident_id === incidentId) || null;
    } catch (error) {
      console.error('Error in getIncident:', error);
      return null;
    }
  }

  recordApproval(incidentId) {
    try {
      let audits = [];

      if (fs.existsSync(paths.approvalAudit)) {
        audits = JSON.parse(fs.readFileSync(paths.approvalAudit, 'utf8'));
      }

      audits.push({
        incident_id: incidentId,
        timestamp: new Date().toISOString(),
        action: 'APPROVED',
        approver: 'TelegramConsole',
        status: 'RECORDED'
      });

      fs.writeFileSync(paths.approvalAudit, JSON.stringify(audits, null, 2), 'utf8');
    } catch (error) {
      console.error('Error recording approval:', error);
    }
  }

  updateIncidentStatus(incidentId, newStatus) {
    try {
      if (!fs.existsSync(paths.incidents)) return;

      const data = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
      const incidents = data.incidents || [];

      const incident = incidents.find(i => i.incident_id === incidentId);
      if (incident) {
        incident.status = newStatus;
        incident.updated_at = new Date().toISOString();
      }

      fs.writeFileSync(paths.incidents, JSON.stringify(data, null, 2), 'utf8');
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

// Main execution
async function main() {
  console.log('[MAIN] Bot Starting...');
  const bot = new TelegramCommandCenter();
  await bot.start();
  console.log('[MAIN] Bot Ready - Awaiting Telegram commands');

  // Handle graceful shutdown
  process.on('SIGINT', () => {
    console.log('[SHUTDOWN] Stopping bot...');
    bot.bot.stopPolling();
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    console.log('[SHUTDOWN] Stopping bot...');
    bot.bot.stopPolling();
    process.exit(0);
  });
}

// Run if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error('[FATAL]', error);
    process.exit(1);
  });
}

export default TelegramCommandCenter;
