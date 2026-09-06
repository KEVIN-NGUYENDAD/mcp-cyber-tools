#!/usr/bin/env node
/**
 * Email Report Sender - Gửi báo cáo 8PM qua email
 * Gửi COMPREHENSIVE-REPORT-8PM.md đến tamngankevin@gmail.com
 */

import fs from 'fs';
import nodemailer from 'nodemailer';

const config = {
  recipientEmail: 'tamngankevin@gmail.com',
  reportFile: 'COMPREHENSIVE-REPORT-8PM.md',
  subject: '📋 HOME SOC - Báo Cáo Toàn Diện 8PM'
};

console.log('📧 EMAIL REPORT SENDER\n');

// Check if report file exists
if (!fs.existsSync(config.reportFile)) {
  console.log(`❌ Report file not found: ${config.reportFile}`);
  console.log('⚠️  Email will not be sent');
  process.exit(1);
}

console.log(`✅ Found report: ${config.reportFile}`);
console.log(`📧 Email recipient: ${config.recipientEmail}\n`);

// Read report content
const reportContent = fs.readFileSync(config.reportFile, 'utf-8');
const reportSize = Math.round(fs.statSync(config.reportFile).size / 1024);

console.log(`📊 Report size: ${reportSize} KB`);
console.log(`📄 Content length: ${reportContent.length} characters\n`);

// Option 1: Try using Gmail SMTP (requires app password)
async function sendViaGmail() {
  console.log('🔄 Attempting to send via Gmail SMTP...\n');

  // Note: This requires an app-specific password in Gmail
  // For security, this should use environment variables in production

  const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: 'tamngankevin@gmail.com',
      // In production: use app-specific password or OAuth2
      // For now, we'll skip actual sending and show the content instead
      pass: process.env.GMAIL_APP_PASSWORD || 'app-password-here'
    }
  });

  try {
    const mailOptions = {
      from: 'tamngankevin@gmail.com',
      to: config.recipientEmail,
      subject: config.subject,
      text: `Báo cáo HOME SOC toàn diện được tạo tại ${new Date().toLocaleString('vi-VN')}\n\nXem chi tiết dưới đây hoặc tại:\nC:\\Users\\tamng\\AppData\\Roaming\\Claude\\Projects\\mcp-cyber-tools\\${config.reportFile}`,
      html: `<h2>📋 HOME SOC - Báo Cáo Toàn Diện</h2>
             <p>Báo cáo được tạo lúc: <strong>${new Date().toLocaleString('vi-VN')}</strong></p>
             <p>Tải file đầy đủ từ:</p>
             <code>C:\\Users\\tamng\\AppData\\Roaming\\Claude\\Projects\\mcp-cyber-tools\\${config.reportFile}</code>
             <hr>
             <pre>${reportContent.substring(0, 2000)}...</pre>
             <p><em>Xem file đầy đủ để có chi tiết hoàn chỉnh</em></p>`,
      attachments: [
        {
          filename: config.reportFile,
          content: reportContent
        }
      ]
    };

    const info = await transporter.sendMail(mailOptions);
    console.log('✅ EMAIL SENT SUCCESSFULLY!');
    console.log(`📧 Message ID: ${info.messageId}`);
    return true;

  } catch (error) {
    console.log('⚠️  Gmail SMTP failed (expected without app password)');
    console.log(`Error: ${error.message}\n`);
    return false;
  }
}

// Option 2: Using Windows built-in email
function sendViaWindows() {
  console.log('🔄 Sending via Windows Mail...\n');

  try {
    const { execSync } = require('child_process');

    // Create mailto link
    const mailtoUrl = encodeURI(`mailto:tamngankevin@gmail.com?subject=${config.subject}&body=See%20attachment`);

    // Open default email client
    execSync(`start ${mailtoUrl}`);

    console.log('✅ Windows Mail opened');
    console.log(`📧 To: ${config.recipientEmail}`);
    console.log(`📋 Subject: ${config.subject}`);
    console.log(`📎 Attachment: ${config.reportFile}\n`);
    console.log('💡 Please attach the report file and send manually');

    return true;

  } catch (error) {
    console.log('⚠️  Windows Mail failed');
    return false;
  }
}

// Option 3: Display report content (fallback)
async function displayReportFallback() {
  console.log('📋 REPORT CONTENT (First 1000 characters):\n');
  console.log('─'.repeat(70));
  console.log(reportContent.substring(0, 1000));
  console.log('─'.repeat(70));
  console.log(`\n...full report saved to: ${config.reportFile}\n`);

  console.log('💡 HOW TO EMAIL THIS REPORT:\n');
  console.log('1️⃣  Open Gmail (gmail.com)');
  console.log('2️⃣  Click Compose');
  console.log('3️⃣  Attach file: C:\\Users\\tamng\\AppData\\Roaming\\Claude\\Projects\\mcp-cyber-tools\\COMPREHENSIVE-REPORT-8PM.md');
  console.log('4️⃣  Subject: 📋 HOME SOC - Báo Cáo Toàn Diện 8PM');
  console.log('5️⃣  Send to: tamngankevin@gmail.com');
  console.log('6️⃣  Send!\n');

  return true;
}

// Main
async function main() {
  console.log('🔄 Attempting email send...\n');

  // Try Gmail first (will fail without app password, which is expected)
  let sent = await sendViaGmail();

  if (!sent) {
    // Try Windows Mail
    sent = sendViaWindows();
  }

  if (!sent) {
    // Fallback: show instructions
    await displayReportFallback();
  }

  console.log('═'.repeat(70));
  console.log('📧 EMAIL REPORT PROCESS COMPLETE');
  console.log('═'.repeat(70));
  console.log(`\n✅ Report file ready: ${config.reportFile}`);
  console.log(`📍 Location: C:\\Users\\tamng\\AppData\\Roaming\\Claude\\Projects\\mcp-cyber-tools\\`);
  console.log(`\n💡 You can manually send this file to yourself at any time.`);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
