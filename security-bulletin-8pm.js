#!/usr/bin/env node
/**
 * HOME SOC - Security Bulletin Email (8PM Daily)
 * Tóm tắt tất cả dữ liệu từ laptop + router/wifi
 * Gửi security bulletin email
 */

import fs from 'fs';
import path from 'path';
import nodemailer from 'nodemailer';

const projectDir = path.join(process.env.APPDATA, 'Claude', 'Projects', 'mcp-cyber-tools');

const CONFIG = {
  projectDir: projectDir,
  laptopDataDir: path.join(projectDir, 'laptop-collection-data'),
  routerDataDir: path.join(projectDir, 'router-wifi-data'),
  bulletinDir: path.join(projectDir, 'security-bulletins'),
  emailUser: process.env.EMAIL_USER || 'tamngankevin@gmail.com',
  emailPass: process.env.GMAIL_APP_PASSWORD
};

if (!fs.existsSync(CONFIG.bulletinDir)) {
  fs.mkdirSync(CONFIG.bulletinDir, { recursive: true });
}

/**
 * Get latest snapshot
 */
function getLatestSnapshot(dataDir) {
  try {
    const latestPath = path.join(dataDir, 'LATEST.json');
    if (fs.existsSync(latestPath)) {
      return JSON.parse(fs.readFileSync(latestPath, 'utf-8'));
    }
  } catch (e) {
    console.log(`  ⚠️  Could not read latest snapshot from ${dataDir}`);
  }
  return null;
}

/**
 * Format security bulletin
 */
function formatBulletin(laptopData, routerData) {
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
  const timeStr = now.toLocaleTimeString();

  let html = `
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0;">
    <h1 style="margin: 0; font-size: 28px;">🔒 HOME SOC</h1>
    <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">Security Bulletin</p>
  </div>

  <div style="background: #f8f9fa; padding: 20px; border-left: 5px solid #667eea;">
    <p style="margin: 0; color: #666; font-size: 12px;">
      📅 ${dateStr} • ⏰ ${timeStr}
    </p>
  </div>

  <div style="padding: 20px; background: white;">
`;

  // Laptop Status
  if (laptopData) {
    html += `
    <h2 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; font-size: 16px;">💻 Laptop Status</h2>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
      <tr style="background: #f0f0f0;">
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Device</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">${laptopData.device || 'Unknown'}</td>
      </tr>
      <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Last Update</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">${new Date(laptopData.timestamp).toLocaleTimeString()}</td>
      </tr>
`;

    if (laptopData.data?.battery) {
      const batLevel = laptopData.data.battery.EstimatedChargeRemaining || 'N/A';
      html += `
      <tr style="background: #f0f0f0;">
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Battery</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">${batLevel}%</td>
      </tr>
`;
    }

    if (laptopData.data?.wifiStatus?.ssid) {
      html += `
      <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>WiFi</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">${laptopData.data.wifiStatus.ssid}</td>
      </tr>
`;
    }

    if (laptopData.data?.memory) {
      html += `
      <tr style="background: #f0f0f0;">
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Memory Usage</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">${laptopData.data.memory.usagePercent}%</td>
      </tr>
`;
    }

    html += `</table>`;
  } else {
    html += `
    <h2 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; font-size: 16px;">💻 Laptop Status</h2>
    <p style="color: #999; font-size: 14px;">No data available</p>
`;
  }

  // Router/WiFi Status
  if (routerData) {
    html += `
    <h2 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; font-size: 16px; margin-top: 20px;">🔐 Network Status</h2>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
      <tr style="background: #f0f0f0;">
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Devices Found</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">${routerData.data?.summary?.devicesFound || 0}</td>
      </tr>
      <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Security Risks</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">
          <strong style="color: ${routerData.data?.summary?.risksFound > 0 ? '#dc3545' : '#28a745'};">
            ${routerData.data?.summary?.risksFound || 0}
          </strong>
        </td>
      </tr>
      <tr style="background: #f0f0f0;">
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Last Scan</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">${new Date(routerData.timestamp).toLocaleTimeString()}</td>
      </tr>
    </table>
`;

    if (routerData.data?.risks?.length > 0) {
      html += `
    <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
      <h3 style="margin: 0 0 10px 0; color: #856404; font-size: 14px;">⚠️ Security Risks Detected</h3>
      <ul style="margin: 0; padding-left: 20px; color: #856404; font-size: 13px;">
`;
      routerData.data.risks.forEach(risk => {
        html += `
        <li>${risk.ip}:${risk.port} - ${risk.service} (${risk.severity})</li>
`;
      });
      html += `
      </ul>
    </div>
`;
    } else {
      html += `
    <div style="background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
      <p style="margin: 0; color: #155724; font-size: 13px;">✅ <strong>No security risks detected</strong></p>
    </div>
`;
    }
  } else {
    html += `
    <h2 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; font-size: 16px; margin-top: 20px;">🔐 Network Status</h2>
    <p style="color: #999; font-size: 14px;">No data available</p>
`;
  }

  // Recommendations
  html += `
    <h2 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; font-size: 16px; margin-top: 20px;">💡 Recommendations</h2>
    <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #555; line-height: 1.6;">
      <li>Review latest scan results on GitHub</li>
      <li>Monitor device changes weekly</li>
      <li>Keep firmware updated</li>
      <li>Disable unnecessary services</li>
    </ul>
  </div>

  <div style="background: #f8f9fa; padding: 15px; border-top: 1px solid #ddd; font-size: 12px; color: #666; text-align: center;">
    <p style="margin: 0;">
      🔗 <a href="https://github.com/KEVIN-NGUYENDAD/mcp-cyber-tools" style="color: #667eea; text-decoration: none;">View on GitHub</a>
    </p>
    <p style="margin: 5px 0 0 0;">
      Auto-generated by HOME SOC • Learning Factory v2
    </p>
  </div>
</div>
`;

  return html;
}

/**
 * Send security bulletin email
 */
async function sendBulletin() {
  console.log('📧 HOME SOC - SECURITY BULLETIN (8PM)');
  console.log(`⏰ Time: ${new Date().toLocaleTimeString()}\n`);

  // Get latest data
  console.log('📂 Reading latest data...');
  const laptopData = getLatestSnapshot(CONFIG.laptopDataDir);
  const routerData = getLatestSnapshot(CONFIG.routerDataDir);

  if (!laptopData && !routerData) {
    console.log('❌ No data available - skipping email');
    return false;
  }

  console.log(`  ✅ Laptop data: ${laptopData ? 'YES' : 'NO'}`);
  console.log(`  ✅ Router data: ${routerData ? 'YES' : 'NO'}`);

  // Format bulletin
  console.log('📝 Formatting bulletin...');
  const bulletinHtml = formatBulletin(laptopData, routerData);

  // Send email
  console.log('📤 Sending email...');
  try {
    const transporter = nodemailer.createTransport({
      service: 'gmail',
      auth: {
        user: CONFIG.emailUser,
        pass: CONFIG.emailPass
      }
    });

    const dateStr = new Date().toLocaleDateString();
    const mailOptions = {
      from: CONFIG.emailUser,
      to: CONFIG.emailUser,
      subject: `🔒 HOME SOC - Security Bulletin - ${dateStr}`,
      html: bulletinHtml
    };

    const info = await transporter.sendMail(mailOptions);
    console.log(`✅ Email sent! Message ID: ${info.messageId}\n`);

    // Save bulletin to file
    const bulletinFile = path.join(CONFIG.bulletinDir, `bulletin-${new Date().toISOString().split('T')[0]}.html`);
    fs.writeFileSync(bulletinFile, bulletinHtml);
    console.log(`📄 Saved to: ${bulletinFile}`);

    return true;
  } catch (error) {
    console.log(`❌ Email send failed: ${error.message}`);
    console.log('   Make sure EMAIL_USER and GMAIL_APP_PASSWORD are set');
    return false;
  }
}

/**
 * Auto-push to GitHub
 */
function autoPushToGitHub() {
  try {
    console.log('\n📤 Pushing to GitHub...');
    const cwd = CONFIG.projectDir;
    execSync('git add security-bulletins/', { cwd, stdio: 'pipe' });
    const timestamp = new Date().toISOString();
    execSync(`git commit -m "data: Security bulletin - ${timestamp}"`, {
      cwd,
      stdio: 'pipe'
    });
    execSync('git push origin learning-factory-v2', {
      cwd,
      stdio: 'pipe'
    });
    console.log('✅ Pushed to GitHub\n');
    return true;
  } catch (error) {
    return false;
  }
}

// Run bulletin
sendBulletin()
  .then(success => {
    if (success) {
      // Push to GitHub
      try {
        const { execSync } = require('child_process');
        autoPushToGitHub();
      } catch (e) {
        console.log('⚠️  GitHub push failed (optional)');
      }
    }
    process.exit(success ? 0 : 1);
  })
  .catch(err => {
    console.error('❌ Fatal error:', err);
    process.exit(1);
  });
