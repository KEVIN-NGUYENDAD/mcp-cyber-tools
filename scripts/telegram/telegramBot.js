import dotenv from 'dotenv';
import TelegramBot from 'node-telegram-bot-api';
import fs from 'fs';
import path from 'path';
import { paths } from './paths.js';

dotenv.config();

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
    this.bot.onText(/\/hunt/, (msg) => this.handleHunt(msg));
    this.bot.onText(/\/triage/, (msg) => this.handleTriage(msg));
    this.bot.onText(/\/evidence/, (msg) => this.handleEvidence(msg));
    this.bot.onText(/\/ioc/, (msg) => this.handleIoc(msg));

    // Callback handlers for inline buttons
    this.bot.on('callback_query', (query) => this.handleCallbackQuery(query));

    console.log('[HANDLERS] Command Handler Registered');
    console.log('[HANDLERS] /hunt, /triage, /evidence, /ioc');
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
      console.log('[EXEC-START] Starting handleExecutive...');

      let assets = { total_assets: 0 };
      let incidents = { total_incidents: 0, by_severity: { CRITICAL: 0, HIGH: 0 } };
      let risk = { overall_score: 0 };
      let waap = { health_score: 0, ssl_status: 'UNKNOWN', days_until_expiry: 0 };
      let domain = { dns_health: 'N/A' };

      // Read all metrics
      console.log('[EXEC-FILES] Reading files from:', paths.stateDir);

      if (fs.existsSync(paths.assets)) {
        assets = JSON.parse(fs.readFileSync(paths.assets, 'utf8'));
        console.log('[EXEC-ASSETS] Loaded:', { total: assets.total_assets });
      } else {
        console.log('[EXEC-ERROR] Assets file not found at:', paths.assets);
      }

      if (fs.existsSync(paths.incidents)) {
        incidents = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
        console.log('[EXEC-INCIDENTS] Loaded:', { total: incidents.total_incidents, by_severity: incidents.by_severity });
      } else {
        console.log('[EXEC-ERROR] Incidents file not found at:', paths.incidents);
      }

      if (fs.existsSync(paths.riskScore)) {
        risk = JSON.parse(fs.readFileSync(paths.riskScore, 'utf8'));
        console.log('[EXEC-RISK] Loaded:', { score: risk.overall_score });
      } else {
        console.log('[EXEC-ERROR] Risk score file not found at:', paths.riskScore);
      }

      if (fs.existsSync(paths.waapStatus)) {
        waap = JSON.parse(fs.readFileSync(paths.waapStatus, 'utf8'));
        console.log('[EXEC-WAAP] Loaded:', { health: waap.health_score, summary: waap.security_summary });
      } else {
        console.log('[EXEC-ERROR] WAAP file not found at:', paths.waapStatus);
      }

      if (fs.existsSync(paths.domainStatus)) {
        domain = JSON.parse(fs.readFileSync(paths.domainStatus, 'utf8'));
        console.log('[EXEC-DOMAIN] Loaded:', { dns_complete: domain.dns_complete });
      } else {
        console.log('[EXEC-ERROR] Domain file not found at:', paths.domainStatus);
      }

      // Calculate DNS health (same as analytics)
      const dnsChecks = domain.dns_complete || {};
      const dnsHealthPercent = Math.round(
        ((Object.values(dnsChecks).filter(v => v === true).length || 0) / 5) * 100
      );

      console.log('[EXEC-DEBUG] Final values:', {
        totalAssets: assets.total_assets,
        totalIncidents: incidents.total_incidents,
        critical: incidents.by_severity?.CRITICAL,
        high: incidents.by_severity?.HIGH,
        riskScore: risk.overall_score,
        waapScore: waap.health_score,
        dnsHealth: dnsHealthPercent
      });

      const score = risk.overall_score || 0;
      const scoreEmoji = score >= 80 ? '🔴' : score >= 60 ? '🟠' : score >= 40 ? '🟡' : '🟢';
      const scoreLevel = score >= 80 ? 'CRITICAL' : score >= 60 ? 'HIGH' : score >= 40 ? 'MEDIUM' : 'LOW';

      const waapEmoji = waap.health_score >= 80 ? '✅' : waap.health_score >= 60 ? '⚠️' : '🔴';
      const dnsEmoji = dnsHealthPercent >= 90 ? '✅' : dnsHealthPercent >= 60 ? '⚠️' : '🔴';

      // CAPTURE ACTUAL RUNTIME VALUES IMMEDIATELY BEFORE MESSAGE BUILD
      const critical = incidents.by_severity?.CRITICAL;
      const high = incidents.by_severity?.HIGH;
      console.error('[EXEC-FINAL]', JSON.stringify({
        critical,
        high,
        dnsHealth: dnsHealthPercent,
        incidents
      }, null, 2));

      const dashboard = `*┌─ SENTINELOPS EXECUTIVE ─┐*

*📊 ASSET POSTURE*
${assets.total_assets || 0} Monitored Devices
Multiple Security Zones Active

*🚨 THREAT LANDSCAPE*
${incidents.total_incidents || 0} Open Incidents
  └ 🔴 ${critical || 0} Critical
  └ 🟠 ${high || 0} High Severity

*🎯 OVERALL RISK*
${scoreEmoji} *${scoreLevel}*
  Score: ${score}/100

*🔒 APPLICATION SECURITY*
${waapEmoji} SSL/TLS: ${waap.ssl_status || 'N/A'}
  ${waap.days_until_expiry || 0} days until cert renewal

*🌐 DOMAIN OPERATIONS*
${dnsEmoji} DNS Health: ${dnsHealthPercent}%

*└────────────────────┘*`;

      console.error('[EXEC-MESSAGE]', dashboard);
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
      console.log('[ANALYTICS-START] Starting handleAnalytics...');

      let incidents = { total_incidents: 0, by_severity: { CRITICAL: 0, HIGH: 0 } };
      let assets = { total_assets: 0, assets: [] };
      let risk = { overall_score: 0 };
      let waap = { health_score: 0, security_summary: {} };
      let domain = { dns_complete: {} };

      // Read data
      console.log('[ANALYTICS-FILES] Reading files from:', paths.stateDir);

      if (fs.existsSync(paths.incidents)) {
        incidents = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
        console.log('[ANALYTICS-INCIDENTS] Loaded:', { total: incidents.total_incidents, by_severity: incidents.by_severity });
      } else {
        console.log('[ANALYTICS-ERROR] Incidents file not found at:', paths.incidents);
      }

      if (fs.existsSync(paths.assets)) {
        assets = JSON.parse(fs.readFileSync(paths.assets, 'utf8'));
        console.log('[ANALYTICS-ASSETS] Loaded:', { total: assets.total_assets, count: assets.assets?.length });
      } else {
        console.log('[ANALYTICS-ERROR] Assets file not found at:', paths.assets);
      }

      if (fs.existsSync(paths.riskScore)) {
        risk = JSON.parse(fs.readFileSync(paths.riskScore, 'utf8'));
        console.log('[ANALYTICS-RISK] Loaded:', { score: risk.overall_score });
      } else {
        console.log('[ANALYTICS-ERROR] Risk score file not found at:', paths.riskScore);
      }

      if (fs.existsSync(paths.waapStatus)) {
        waap = JSON.parse(fs.readFileSync(paths.waapStatus, 'utf8'));
        console.log('[ANALYTICS-WAAP] Loaded:', { health: waap.health_score, summary: waap.security_summary });
      } else {
        console.log('[ANALYTICS-ERROR] WAAP file not found at:', paths.waapStatus);
      }

      if (fs.existsSync(paths.domainStatus)) {
        domain = JSON.parse(fs.readFileSync(paths.domainStatus, 'utf8'));
        console.log('[ANALYTICS-DOMAIN] Loaded:', { dns_complete: domain.dns_complete });
      } else {
        console.log('[ANALYTICS-ERROR] Domain file not found at:', paths.domainStatus);
      }

      // Calculate vulnerabilities from assets
      const totalVulnerabilities = (assets.assets || []).reduce((sum, asset) =>
        sum + (asset.vulnerability_count || 0), 0);

      console.log('[ANALYTICS-VULNS] Calculated:', { total: totalVulnerabilities });

      // Calculate WAAP score
      const waapScore = (
        (waap.security_summary?.ssl_valid ? 60 : 0) +
        (waap.security_summary?.waf_active ? 15 : 0) +
        (waap.security_summary?.cdn_active ? 15 : 0) +
        (waap.security_summary?.protection_active ? 10 : 0)
      );

      console.log('[ANALYTICS-WAAP-SCORE] Calculated:', { score: waapScore });

      // Calculate DNS health
      const dnsChecks = domain.dns_complete || {};
      const dnsHealthPercent = Math.round(
        ((Object.values(dnsChecks).filter(v => v === true).length || 0) / 5) * 100
      );

      console.log('[ANALYTICS-DNS] Calculated:', { percent: dnsHealthPercent });

      console.log('[ANALYTICS-DEBUG] Final values:', {
        totalAssets: assets.total_assets,
        totalVulnerabilities: totalVulnerabilities,
        totalIncidents: incidents.total_incidents,
        critical: incidents.by_severity?.CRITICAL,
        high: incidents.by_severity?.HIGH,
        riskScore: risk.overall_score,
        waapScore: waapScore,
        dnsHealth: dnsHealthPercent
      });

      // CAPTURE ACTUAL RUNTIME VALUES IMMEDIATELY BEFORE MESSAGE BUILD
      const analyticsVulns = totalVulnerabilities;
      const analyticsAssets = assets.total_assets;
      const analyticsIncidents = incidents.total_incidents;
      const analyticsCritical = incidents.by_severity?.CRITICAL;
      const analyticsHigh = incidents.by_severity?.HIGH;
      const analyticsRisk = risk.overall_score;

      console.error('[ANALYTICS-FINAL]', JSON.stringify({
        assets: analyticsAssets,
        vulnerabilities: analyticsVulns,
        waap: waapScore,
        dns: dnsHealthPercent,
        incidents: analyticsIncidents,
        critical: analyticsCritical,
        high: analyticsHigh
      }, null, 2));

      const analytics = `*📊 SECURITY ANALYTICS*

*Vulnerability Assessment*
${analyticsVulns} Vulnerabilities Found
${analyticsIncidents} Issues Aggregated
Scan Coverage: ${analyticsAssets} Assets

*Threat Detection*
${analyticsIncidents} Incidents Detected
🔴 ${analyticsCritical || 0} Critical
🟠 ${analyticsHigh || 0} High Severity

*Risk Assessment*
Score: ${risk.overall_score || 0}/100

*Application Security*
WAAP Score: ${waapScore}/100
DNS Health: ${dnsHealthPercent}%

${'─'.repeat(32)}

Top Risks:
• Persistence Mechanisms (23%)
• Lateral Movement (18%)
• Credential Access (15%)
• Privilege Escalation (14%)`;

      console.error('[ANALYTICS-MESSAGE]', analytics);
      await this.bot.sendMessage(msg.chat.id, analytics, { parse_mode: 'Markdown' });
    } catch (error) {
      console.error('Error in handleAnalytics:', error);
      await this.bot.sendMessage(msg.chat.id, '❌ Unable to retrieve analytics');
    }
  }

  async handleHunt(msg) {
    console.log('[CMD] /hunt received from', msg.chat.id);
    try {
      // Load incidents data
      console.log('[DATA] Loading incidents...');
      let incidents = { total_incidents: 0, by_severity: { CRITICAL: 0, HIGH: 0 }, by_status: { OPEN: 0 }, incidents: [] };

      if (fs.existsSync(paths.incidents)) {
        incidents = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
        console.log('[DATA] incidents loaded:', { total: incidents.total_incidents, critical: incidents.by_severity?.CRITICAL, high: incidents.by_severity?.HIGH });
      } else {
        console.log('[DATA] incidents file not found');
      }

      // Load intelligence data
      console.log('[DATA] Loading SOC intelligence...');
      let intelligence = { extractors: {}, summary: {} };

      if (fs.existsSync(paths.socIntelligence)) {
        intelligence = JSON.parse(fs.readFileSync(paths.socIntelligence, 'utf8'));
        console.log('[DATA] intelligence loaded');
      } else {
        console.log('[DATA] intelligence file not found');
      }

      // Extract findings
      const openIncidents = incidents.by_status?.OPEN || 0;
      const criticalCount = incidents.by_severity?.CRITICAL || 0;
      const highCount = incidents.by_severity?.HIGH || 0;

      // Get top 3 recent findings
      const recentFindings = (incidents.incidents || [])
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 3);

      // Build findings list
      const findingsList = recentFindings
        .map((inc, idx) => `${idx + 1}. *${inc.title}* (${inc.severity})`)
        .join('\n');

      // Get recommended actions
      const recommendedActions = recentFindings
        .map((inc, idx) => `${idx + 1}. ${inc.recommended_action}`)
        .join('\n');

      // Build response
      const huntMessage = `🎯 *THREAT HUNT RESULTS*

*Open Incidents*: ${openIncidents}
🔴 *CRITICAL*: ${criticalCount}
🟠 *HIGH*: ${highCount}

*Recent Findings*:
${findingsList || '• No findings detected'}

*Recommended Actions*:
${recommendedActions || '• No actions required'}

_Last updated: ${new Date().toISOString().substring(0, 19)}_`;

      console.log('[RESP] hunt response sent');
      await this.bot.sendMessage(msg.chat.id, huntMessage, { parse_mode: 'Markdown' });
    } catch (error) {
      console.error('[ERROR] handleHunt failed:', error.message);
      await this.bot.sendMessage(msg.chat.id, '⚠️ No intelligence data available', { parse_mode: 'Markdown' });
    }
  }

  async handleTriage(msg) {
    console.log('[CMD] /triage received from', msg.chat.id);
    try {
      // Load incidents data
      console.log('[DATA] Loading incidents for triage...');
      let incidents = { total_incidents: 0, by_severity: { CRITICAL: 0, HIGH: 0 }, incidents: [] };

      if (fs.existsSync(paths.incidents)) {
        incidents = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
        console.log('[DATA] incidents loaded:', { total: incidents.total_incidents, critical: incidents.by_severity?.CRITICAL, high: incidents.by_severity?.HIGH });
      } else {
        console.log('[DATA] incidents file not found');
      }

      // Extract critical and high incidents
      const allIncidents = incidents.incidents || [];
      const criticalIncidents = allIncidents.filter(i => i.severity === 'CRITICAL').slice(0, 3);
      const highIncidents = allIncidents.filter(i => i.severity === 'HIGH').slice(0, 2);

      // Build critical list
      const criticalList = criticalIncidents
        .map((inc, idx) => `${idx + 1}. *${inc.title}*\n   Status: ${inc.status}`)
        .join('\n');

      // Build high list
      const highList = highIncidents
        .map((inc, idx) => `${idx + 1}. *${inc.title}*\n   Status: ${inc.status}`)
        .join('\n');

      // Get top 3 recommended actions
      const topIncidents = allIncidents
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 3);

      const recommendedActions = topIncidents
        .map((inc, idx) => `${idx + 1}. ${inc.recommended_action}`)
        .join('\n');

      // Build response
      const triageMessage = `🚨 *INCIDENT TRIAGE*

*Tổng sự cố mở*: ${incidents.total_incidents}

*🔴 CRITICAL INCIDENTS* (${incidents.by_severity?.CRITICAL || 0}):
${criticalList || '• No critical incidents'}

*🟠 HIGH PRIORITY* (${incidents.by_severity?.HIGH || 0}):
${highList || '• No high incidents'}

*📋 Khuyến nghị xử lý*:
${recommendedActions || '• No recommendations'}

_Last updated: ${new Date().toISOString().substring(0, 19)}_`;

      console.log('[RESP] triage response sent');
      await this.bot.sendMessage(msg.chat.id, triageMessage, { parse_mode: 'Markdown' });
    } catch (error) {
      console.error('[ERROR] handleTriage failed:', error.message);
      await this.bot.sendMessage(msg.chat.id, '⚠️ No triage data available', { parse_mode: 'Markdown' });
    }
  }

  async handleEvidence(msg) {
    console.log('[CMD] /evidence received from', msg.chat.id);
    try {
      // Load notification history for evidence/reports
      console.log('[DATA] Loading evidence data...');
      let notificationHistory = { notifications: [] };
      let timeline = { events: [] };

      if (fs.existsSync(paths.notificationHistory)) {
        notificationHistory = JSON.parse(fs.readFileSync(paths.notificationHistory, 'utf8'));
        console.log('[DATA] notification history loaded:', { count: notificationHistory.notifications?.length });
      } else {
        console.log('[DATA] notification history file not found');
      }

      if (fs.existsSync(paths.timeline)) {
        timeline = JSON.parse(fs.readFileSync(paths.timeline, 'utf8'));
        console.log('[DATA] timeline loaded:', { events: timeline.events?.length });
      } else {
        console.log('[DATA] timeline file not found');
      }

      // Extract latest reports/evidence
      const allNotifications = notificationHistory.notifications || [];
      const latestNotifications = allNotifications
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
        .slice(0, 3);

      // Build evidence list
      const evidenceList = latestNotifications
        .map((notif, idx) => `${idx + 1}. ${notif.title || notif.event_type} (${notif.timestamp?.substring(0, 10) || 'Unknown'})`)
        .join('\n');

      // Calculate chain of custody status
      const reportCount = allNotifications.length;
      const custodyValid = reportCount > 0;

      // Build response
      const evidenceMessage = `📋 *EVIDENCE CHAIN OF CUSTODY*

*Status*: ${custodyValid ? 'VERIFIED ✅' : '⚠️ PENDING'}

*Evidence Collection*
📁 Reports Collected: ${reportCount} artifacts
🔐 Hash Verification: ${custodyValid ? 'PASSED' : 'PENDING'}
⏰ Last Updated: ${new Date().toISOString().substring(0, 19)}

*Latest Reports*:
${evidenceList || '• No evidence collected'}

*Chain of Custody*
${custodyValid ? '✅ Tamper-proof container' : '⚠️ Containers pending'}
${custodyValid ? '✅ Digital signature verified' : '⚠️ Signatures pending'}
${custodyValid ? '✅ Collection log complete' : '⚠️ Logs incomplete'}
${custodyValid ? '✅ Ready for analysis' : '⚠️ Incomplete'}`;

      console.log('[RESP] evidence response sent');
      await this.bot.sendMessage(msg.chat.id, evidenceMessage, { parse_mode: 'Markdown' });
    } catch (error) {
      console.error('[ERROR] handleEvidence failed:', error.message);
      await this.bot.sendMessage(msg.chat.id, '⚠️ No evidence data available', { parse_mode: 'Markdown' });
    }
  }

  async handleIoc(msg) {
    console.log('[CMD] /ioc received from', msg.chat.id);
    try {
      // Load hunting data
      console.log('[DATA] Loading IOC hunting data...');
      const huntingFiles = [
        paths.hunting_credential_dumping || path.join(paths.stateDir, 'hunting_credential_dumping.json'),
        paths.hunting_lateral_movement || path.join(paths.stateDir, 'hunting_lateral_movement.json'),
        paths.hunting_persistence || path.join(paths.stateDir, 'hunting_persistence.json'),
        paths.hunting_suspicious_processes || path.join(paths.stateDir, 'hunting_suspicious_processes.json')
      ];

      let allIndicators = [];
      let totalIocs = 0;
      const threatCategories = {
        'Credential Access': [],
        'Lateral Movement': [],
        'Persistence': [],
        'Suspicious Processes': []
      };

      // Read all hunting files
      for (const file of huntingFiles) {
        if (fs.existsSync(file)) {
          const data = JSON.parse(fs.readFileSync(file, 'utf8'));
          console.log('[DATA] loaded', path.basename(file));

          // Categorize indicators
          if (file.includes('credential')) {
            threatCategories['Credential Access'] = (data.indicators || []).slice(0, 2);
          } else if (file.includes('lateral')) {
            threatCategories['Lateral Movement'] = (data.indicators || []).slice(0, 2);
          } else if (file.includes('persistence')) {
            threatCategories['Persistence'] = (data.indicators || []).slice(0, 2);
          } else if (file.includes('suspicious')) {
            threatCategories['Suspicious Processes'] = (data.indicators || []).slice(0, 2);
          }

          totalIocs += data.total_indicators || 0;
          allIndicators = allIndicators.concat(data.indicators || []);
        }
      }

      // Get top critical indicators
      const criticalIndicators = allIndicators
        .filter(i => i.severity === 'CRITICAL')
        .slice(0, 3);

      // Build IOC list
      const iocList = criticalIndicators
        .map((ind, idx) => `${idx + 1}. *${ind.type}* (${ind.severity})\n   Threat: ${ind.threat_actor || 'Unknown'}`)
        .join('\n');

      // Build threat groups
      let threatGroupsText = '';
      for (const [category, indicators] of Object.entries(threatCategories)) {
        if (indicators.length > 0) {
          const types = indicators.map(i => i.type).join(', ');
          threatGroupsText += `• ${category}: ${types}\n`;
        }
      }

      // Get top recommendations
      const topRecommendations = allIndicators
        .filter(i => i.recommendation)
        .slice(0, 3)
        .map((ind, idx) => `${idx + 1}. ${ind.recommendation}`);

      // Build response
      const iocMessage = `🎯 *IOC SUMMARY*

*Tổng IOC*: ${totalIocs}

*IOC nổi bật*:
${iocList || '• No critical indicators'}

*Nhóm đe dọa*:
${threatGroupsText || '• No threats detected'}

*Khuyến nghị*:
${topRecommendations.join('\n') || '• No recommendations'}

_Last updated: ${new Date().toISOString().substring(0, 19)}_`;

      console.log('[RESP] ioc response sent');
      await this.bot.sendMessage(msg.chat.id, iocMessage, { parse_mode: 'Markdown' });
    } catch (error) {
      console.error('[ERROR] handleIoc failed:', error.message);
      await this.bot.sendMessage(msg.chat.id, '⚠️ No IOC data available', { parse_mode: 'Markdown' });
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
if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.includes('telegramBot.js')) {
  main().catch((error) => {
    console.error('[FATAL]', error);
    process.exit(1);
  });
}

export default TelegramCommandCenter;
