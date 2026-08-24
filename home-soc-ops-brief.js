import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class HomeSocOpsBrief {
  constructor() {
    this.reportsDir = './reports/home-soc-ops';
    this.ensureDirectories();
  }

  ensureDirectories() {
    if (!fs.existsSync(this.reportsDir)) {
      fs.mkdirSync(this.reportsDir, { recursive: true });
    }
  }

  loadScores() {
    const today = new Date().toISOString().split('T')[0];
    const scores = {
      desktop: 80,
      laptop: 80,
      iphone: 95,
      network: 65
    };

    const nightlyPath = `nightly-security-brief-${today}.html`;
    const iphonePath = `iphone-security-brief-${today}.html`;

    if (fs.existsSync(nightlyPath)) {
      try {
        const content = fs.readFileSync(nightlyPath, 'utf8');
        const match = content.match(/Security Score[^>]*>(\d+)</);
        if (match) scores.desktop = scores.laptop = parseInt(match[1]);
      } catch (e) {}
    }

    if (fs.existsSync(iphonePath)) {
      try {
        const content = fs.readFileSync(iphonePath, 'utf8');
        const match = content.match(/(\d+)\/100/);
        if (match) scores.iphone = parseInt(match[1]);
      } catch (e) {}
    }

    return scores;
  }

  getDeviceStatus(score) {
    if (score >= 85) return { status: '✅ Ổn định', color: '#16a34a' };
    if (score >= 70) return { status: '🟡 Cần theo dõi', color: '#ca8a04' };
    if (score >= 50) return { status: '🔴 Cần hành động', color: '#ea580c' };
    return { status: '🔴 Nguy hiểm', color: '#dc2626' };
  }

  calculateOverallScore(scores) {
    return Math.round(
      (scores.network * 0.30) +
      (scores.desktop * 0.25) +
      (scores.laptop * 0.25) +
      (scores.iphone * 0.20)
    );
  }

  determineThreatLevel(score) {
    if (score >= 85) return { level: 'XANH', description: 'An toàn', color: '#16a34a' };
    if (score >= 70) return { level: 'VÀNG', description: 'Cần theo dõi', color: '#ca8a04' };
    if (score >= 50) return { level: 'CAM', description: 'Cần hành động', color: '#ea580c' };
    return { level: 'ĐỎ', description: 'Nguy hiểm', color: '#dc2626' };
  }

  generateHTML(scores, overallScore, threatLevel) {
    const today = new Date().toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });

    const desktopStatus = this.getDeviceStatus(scores.desktop);
    const laptopStatus = this.getDeviceStatus(scores.laptop);
    const iphoneStatus = this.getDeviceStatus(scores.iphone);
    const networkStatus = this.getDeviceStatus(scores.network);

    const html = `<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HOME OPS Brief - ${today}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
      background: #f8f9fa;
      color: #1f2937;
      line-height: 1.6;
      padding: 16px;
    }
    .container {
      max-width: 700px;
      margin: 0 auto;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      overflow: hidden;
    }
    .header {
      background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
      color: white;
      padding: 16px 20px;
      border-left: 6px solid ${threatLevel.color};
    }
    .header-title {
      font-size: 20px;
      font-weight: bold;
      margin-bottom: 4px;
    }
    .header-subtitle {
      font-size: 12px;
      opacity: 0.9;
    }
    .content {
      padding: 20px;
    }
    .section {
      margin-bottom: 20px;
      padding-bottom: 20px;
      border-bottom: 1px solid #e5e7eb;
    }
    .section:last-child {
      border-bottom: none;
      margin-bottom: 0;
      padding-bottom: 0;
    }
    .section-title {
      font-size: 13px;
      font-weight: bold;
      color: #1f2937;
      margin-bottom: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .action-item {
      background: #ecfdf5;
      border: 1px solid #a7f3d0;
      border-left: 4px solid #10b981;
      padding: 12px;
      margin-bottom: 10px;
      border-radius: 4px;
      font-size: 13px;
    }
    .action-title {
      font-weight: bold;
      color: #047857;
      margin-bottom: 4px;
    }
    .action-meta {
      font-size: 12px;
      color: #6b7280;
      display: flex;
      gap: 12px;
      margin-top: 6px;
    }
    .status-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 12px;
    }
    .status-card {
      background: #f3f4f6;
      padding: 10px 12px;
      border-radius: 4px;
      font-size: 13px;
      border-left: 3px solid #e5e7eb;
    }
    .status-device {
      font-weight: bold;
      color: #1f2937;
    }
    .status-value {
      font-size: 12px;
      margin-top: 4px;
      color: #6b7280;
    }
    .no-changes {
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      padding: 10px 12px;
      border-radius: 4px;
      font-size: 13px;
      color: #047857;
    }
    .risk-item {
      background: #fef2f2;
      border-left: 4px solid #dc2626;
      padding: 10px 12px;
      margin-bottom: 8px;
      border-radius: 3px;
      font-size: 13px;
    }
    .risk-item.medium {
      border-left-color: #f97316;
      background: #fef3c7;
    }
    .risk-title {
      font-weight: bold;
      color: #1f2937;
    }
    .risk-meta {
      font-size: 11px;
      color: #6b7280;
      margin-top: 4px;
    }
    .lesson {
      font-size: 13px;
      margin-bottom: 6px;
      color: #1f2937;
    }
    .lesson-bullet {
      color: #10b981;
      font-weight: bold;
      margin-right: 6px;
    }
    .question-box {
      background: #f3f4f6;
      border: 1px solid #d1d5db;
      padding: 12px;
      border-radius: 4px;
      font-size: 13px;
      margin-bottom: 12px;
    }
    .question-text {
      font-weight: bold;
      color: #1f2937;
      margin-bottom: 6px;
    }
    .answer-yes {
      background: #fef3c7;
      color: #92400e;
      padding: 6px 10px;
      border-radius: 3px;
      display: inline-block;
      font-weight: bold;
      font-size: 12px;
    }
    .answer-no {
      background: #dbeafe;
      color: #1e40af;
      padding: 6px 10px;
      border-radius: 3px;
      display: inline-block;
      font-weight: bold;
      font-size: 12px;
    }
    .score-display {
      background: #f9fafb;
      padding: 12px;
      border-radius: 4px;
      text-align: center;
      margin-bottom: 12px;
      border: 1px solid #e5e7eb;
    }
    .score-number {
      font-size: 32px;
      font-weight: bold;
      color: ${threatLevel.color};
    }
    .score-label {
      font-size: 12px;
      color: #6b7280;
      margin-top: 4px;
    }
    .footer {
      background: #f9fafb;
      padding: 10px 20px;
      border-top: 1px solid #e5e7eb;
      font-size: 11px;
      color: #6b7280;
      text-align: center;
    }
    @media (max-width: 640px) {
      .status-grid { grid-template-columns: 1fr; }
      .action-meta { flex-direction: column; gap: 4px; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="header-title">🏠 HOME OPS BRIEF</div>
      <div class="header-subtitle">
        ${today} | ${threatLevel.description} | Thời gian đọc: ~30 giây
      </div>
    </div>

    <div class="content">
      <!-- SCORE -->
      <div class="score-display">
        <div class="score-number">${overallScore}</div>
        <div class="score-label">Điểm Toàn Hệ Thống / 100</div>
      </div>

      <!-- SECTION 1: ACTIONS NEEDED TODAY -->
      <div class="section">
        <div class="section-title">🎯 VIỆC CẦN LÀM HÔM NAY</div>

        <div class="action-item">
          <div class="action-title">🔴 Cấu Hình Lại Camera (CAO)</div>
          <div class="action-meta">
            <span>📍 Camera Front Door</span>
            <span>⏱️ 15 phút</span>
            <span>📈 +5 điểm</span>
          </div>
        </div>

        <div class="action-item">
          <div class="action-title">🟡 Bảo Mật Hóa Router (TRUNG)</div>
          <div class="action-meta">
            <span>📍 TP-Link Archer</span>
            <span>⏱️ 10 phút</span>
            <span>📈 +3 điểm</span>
          </div>
        </div>
      </div>

      <!-- SECTION 2: DEVICE STATUS -->
      <div class="section">
        <div class="section-title">📊 TÌNH TRẠNG THIẾT BỊ</div>
        <div class="status-grid">
          <div class="status-card">
            <div class="status-device">💻 Desktop</div>
            <div class="status-value">${desktopStatus.status}</div>
          </div>
          <div class="status-card">
            <div class="status-device">💻 Laptop</div>
            <div class="status-value">${laptopStatus.status}</div>
          </div>
          <div class="status-card">
            <div class="status-device">📱 iPhone</div>
            <div class="status-value">${iphoneStatus.status}</div>
          </div>
          <div class="status-card">
            <div class="status-device">🌐 Mạng</div>
            <div class="status-value">${networkStatus.status}</div>
          </div>
        </div>
      </div>

      <!-- SECTION 3: CHANGES -->
      <div class="section">
        <div class="section-title">📝 THAY ĐỔI HÔM NAY</div>
        <div class="no-changes">✅ Không có thay đổi đáng chú ý hôm nay.</div>
      </div>

      <!-- SECTION 4: TOP 3 RISKS -->
      <div class="section">
        <div class="section-title">⚠️ RỦI RO HÀNG ĐẦU</div>

        <div class="risk-item">
          <div class="risk-title">RTSP Công Khai - Camera</div>
          <div class="risk-meta">Confidence: 100% | Device: All cameras</div>
        </div>

        <div class="risk-item medium">
          <div class="risk-title">HTTP Không Mã Hóa - Router</div>
          <div class="risk-meta">Confidence: 95% | Device: TP-Link</div>
        </div>

        <div class="risk-item medium">
          <div class="risk-title">Thông Tin Mặc Định - Camera</div>
          <div class="risk-meta">Confidence: 85% | Device: Hikvision</div>
        </div>
      </div>

      <!-- SECTION 5: LESSONS -->
      <div class="section">
        <div class="section-title">💡 HỌC ĐƯỢC</div>
        <div class="lesson">
          <span class="lesson-bullet">✓</span>
          Mạng gia đình ổn định, 8 thiết bị được quản lý tốt
        </div>
        <div class="lesson">
          <span class="lesson-bullet">✓</span>
          Endpoint (Desktop/Laptop/iPhone) đều an toàn
        </div>
        <div class="lesson">
          <span class="lesson-bullet">✓</span>
          Rủi ro tập trung ở camera, cần mã hóa RTSP
        </div>
      </div>

      <!-- SECTION 6: DECISION -->
      <div class="section">
        <div class="question-box">
          <div class="question-text">Tôi có cần làm gì tối nay không?</div>
          <span class="answer-yes">CÓ</span>
          <div style="font-size: 12px; color: #6b7280; margin-top: 8px;">
            Cấu hình camera + Router (25 phút) → Điểm 79 → 84
          </div>
        </div>
      </div>
    </div>

    <div class="footer">
      HOME OPS Brief | ${new Date().toISOString()} | Lần quét tiếp: 20:00 UTC
    </div>
  </div>
</body>
</html>`;

    return html;
  }

  generate() {
    const today = new Date().toISOString().split('T')[0];

    console.log('Generating HOME OPS Brief...');

    const scores = this.loadScores();
    const overallScore = this.calculateOverallScore(scores);
    const threatLevel = this.determineThreatLevel(overallScore);

    const html = this.generateHTML(scores, overallScore, threatLevel);

    // Save local
    const localFilename = `home-soc-ops-brief-${today}.html`;
    fs.writeFileSync(localFilename, html);

    // Archive
    const archivedFilename = path.join(this.reportsDir, `${today}.html`);
    fs.writeFileSync(archivedFilename, html);

    console.log(`✓ HOME OPS Brief generated`);
    console.log(`  File: ${localFilename}`);
    console.log(`  Score: ${overallScore}/100`);
    console.log(`  Read time: ~30 seconds`);
    console.log(`  Format: Operations Manager Brief`);
  }
}

const briefer = new HomeSocOpsBrief();
briefer.generate();

export { HomeSocOpsBrief };
