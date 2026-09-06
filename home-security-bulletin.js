#!/usr/bin/env node
const { execSync } = require('child_process');
const nodemailer = require('nodemailer');
const fs = require('fs');
const path = require('path');

const EMAIL = process.env.EMAIL_USER || 'tamngankevin@gmail.com';
const PASS = process.env.GMAIL_APP_PASSWORD;
const REPO_DIR = path.join(__dirname, 'repo-sync');
const REPO_URL = 'https://github.com/KEVIN-NGUYENDAD/mcp-cyber-tools.git';

if (!PASS) {
  console.error('❌ Set GMAIL_APP_PASSWORD environment variable');
  process.exit(1);
}

// Ensure repo directory exists
if (!fs.existsSync(REPO_DIR)) {
  fs.mkdirSync(REPO_DIR, { recursive: true });
}

// Git pull latest data
function pullLatestData() {
  try {
    if (fs.existsSync(path.join(REPO_DIR, '.git'))) {
      execSync('git pull origin learning-factory-v2', { cwd: REPO_DIR, stdio: 'pipe' });
    } else {
      execSync(`git clone --branch learning-factory-v2 ${REPO_URL} .`, { cwd: REPO_DIR, stdio: 'pipe' });
    }
    console.log('✅ Latest data pulled from GitHub');
    return true;
  } catch (e) {
    console.error('❌ Git pull failed:', e.message);
    return false;
  }
}

// Read latest security file
function readLatestFile(fileNames) {
  for (const fileName of fileNames) {
    const filePath = path.join(REPO_DIR, fileName);
    if (fs.existsSync(filePath)) {
      try {
        return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
      } catch (e) {
        console.log(`⚠️  Could not parse ${fileName}`);
      }
    }
  }
  return null;
}

// Check for critical alerts
function getCriticalAlerts(data) {
  const critical = ['DNS_CHANGE', 'FIREWALL_DISABLED', 'DEFENDER_DISABLED', 'RDP_ENABLED', 'SSH_ENABLED'];

  if (!data || !data.alerts) return [];

  return data.alerts.filter(a => critical.includes(a.type) && !a.alerted);
}

// Format bulletin
function formatBulletin(data, alerts) {
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  let alertsText = '';
  if (alerts.length === 0) {
    alertsText = '✅ No Security Events Detected';
  } else {
    alertsText = 'Alerts in the last 24 hours:\n';
    alerts.forEach(a => {
      const icon = a.severity === 'CRITICAL' ? '🔴' : '🟠';
      alertsText += `${icon} ${a.name} (${a.time})\n`;
    });
  }

  let riskLevel = 'GREEN';
  if (alerts.some(a => a.severity === 'CRITICAL')) riskLevel = 'RED';
  else if (alerts.length > 0) riskLevel = 'YELLOW';

  const bulletin = `🏠 HOME SECURITY BULLETIN

Date: ${dateStr}
Time: ${now.toLocaleTimeString()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY

Devices Monitored: ${data.devices || 'N/A'}
New Devices: ${data.newDevices || '0'}
Disconnected: ${data.disconnected || '0'}

SECURITY STATUS

Firewall: ${data.firewall ? '✅ ENABLED' : '❌ DISABLED'}
Defender: ${data.defender ? '✅ ENABLED' : '❌ DISABLED'}
DNS: ${data.dnsNormal ? '✅ NORMAL' : '⚠️ CHANGED'}
RDP: ${data.rdpClosed ? '✅ CLOSED' : '❌ OPEN'}
SSH: ${data.sshClosed ? '✅ CLOSED' : '❌ OPEN'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALERTS

${alertsText}

RISK ASSESSMENT

Status: ${riskLevel === 'RED' ? '🚨 HIGH' : riskLevel === 'YELLOW' ? '⚠️ MEDIUM' : '✅ LOW'}

RECOMMENDED ACTIONS

${alerts.length === 0 ?
  '1. Continue monitoring\n2. Schedule weekly security audit\n3. Review firewall rules' :
  '1. Review alerts immediately\n2. Verify device changes\n3. Check security logs\n4. Update baseline if changes are expected\n5. Contact support if issues persist'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Home Security Monitoring | 24/7 Protection
`;

  return bulletin;
}

// Send email
async function sendEmail(subject, text) {
  try {
    const mail = nodemailer.createTransport({
      service: 'gmail',
      auth: { user: EMAIL, pass: PASS }
    });

    await mail.sendMail({
      from: EMAIL,
      to: EMAIL,
      subject,
      text,
      priority: 'high'
    });

    return true;
  } catch (e) {
    console.error(`❌ Email failed: ${e.message}`);
    return false;
  }
}

// Check for critical alerts and send immediately
async function checkCriticalAlerts() {
  pullLatestData();

  const data = readLatestFile(['alerts.json', 'security-events.json']);
  if (!data) return;

  const critical = getCriticalAlerts(data);
  if (critical.length === 0) return;

  console.log(`🚨 ${critical.length} CRITICAL alert(s) detected!`);

  for (const alert of critical) {
    const text = `🚨 HOME SECURITY ALERT

EVENT: ${alert.name}
TIME: ${alert.time}
DEVICE: ${alert.device || 'N/A'}
SEVERITY: CRITICAL

DETAILS:
${alert.description}

ACTION REQUIRED:
${alert.action || 'Investigate immediately'}

DO NOT WAIT FOR DAILY BULLETIN
`;

    await sendEmail(`🚨 HOME SECURITY ALERT - ${alert.name}`, text);
    console.log(`✅ Alert sent: ${alert.name}`);
  }
}

// Generate daily bulletin (8 PM)
async function generateDailyBulletin() {
  const now = new Date();
  const hours = now.getHours();
  const minutes = now.getMinutes();

  // Check if it's 8 PM (20:00)
  if (hours !== 20 || minutes > 5) {
    return;
  }

  console.log('📊 Generating daily bulletin...');

  pullLatestData();

  const data = readLatestFile(['daily-security-report.json', 'security-report.json', 'devices.json']);
  const alerts = readLatestFile(['alerts.json', 'security-events.json'])?.alerts || [];

  const bulletin = formatBulletin(data || {}, alerts);

  const success = await sendEmail('🏠 HOME SECURITY BULLETIN', bulletin);

  if (success) {
    console.log('✅ Daily bulletin sent');
  }
}

// Main loop
async function start() {
  console.log(`
╔════════════════════════════════════════════════════════════╗
║  🏠 HOME SECURITY BULLETIN - REPORTER & ALERTER           ║
║                                                            ║
║  Reads: GitHub Security Data                             ║
║  Reports: Daily 8 PM Bulletin                            ║
║  Alerts: CRITICAL events immediately                     ║
╚════════════════════════════════════════════════════════════╝
`);

  // Check for critical alerts every 5 minutes
  setInterval(checkCriticalAlerts, 5 * 60 * 1000);

  // Generate daily bulletin at 8 PM
  setInterval(generateDailyBulletin, 60 * 1000);

  // Initial check
  await checkCriticalAlerts();
  await generateDailyBulletin();

  console.log('✅ Monitoring started. Press Ctrl+C to stop.\n');
}

start().catch(err => {
  console.error('❌ Error:', err.message);
  process.exit(1);
});
