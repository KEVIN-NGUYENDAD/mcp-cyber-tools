import express from 'express';
import cors from 'cors';
import fs from 'fs';
import crypto from 'crypto';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Determine state directory - use __dirname as primary source
// web/server.js is in PROJECT_ROOT/web/, so ../state gets to PROJECT_ROOT/state
const PRIMARY_STATE_DIR = path.join(__dirname, '..', 'state');
const possibleDirs = [
  process.env.STATE_DIR,
  PRIMARY_STATE_DIR,
  '/var/task/state', // Render deployed
];

let STATE_DIR = '';
for (const dir of possibleDirs) {
  if (dir && fs.existsSync(dir)) {
    STATE_DIR = dir;
    break;
  }
}

if (!STATE_DIR) {
  console.warn('[SERVER] No state directory found - API will return empty data');
  STATE_DIR = PRIMARY_STATE_DIR;
}

// ============================================================================
// EXP-02 — XÁC THỰC CHO /api
// ============================================================================
//
// `app.use(cors())` không giới hạn nguồn + không có lớp xác thực nào = mọi
// trang web bất kỳ đọc được `/api/state/assets.json`. Danh sách allowlist bên
// dưới chưa từng là một lớp bảo vệ: nó chỉ liệt kê *chính xác* những tệp nhạy
// cảm nào được phép lấy.
//
// Quy tắc fail-closed: không có `API_KEY` thì `/api` **từ chối**, chứ không mở.
// Một biến môi trường bị quên phải đọc ra là "chưa cấu hình", không được đọc ra
// là "không cần khoá" — đó đúng là kiểu mặc-định-xanh mà repo này cấm.
const API_KEY = process.env.API_KEY || '';
// Được gắn bằng `app.use('/api', ...)`, nên `req.path` ở trong middleware là
// phần SAU tiền tố: `/health`, không phải `/api/health`.
const PUBLIC_PATHS = new Set(['/health']); // Render health check gọi đường này

if (!API_KEY) {
  console.warn('[SECURITY] Chưa đặt API_KEY — mọi route /api sẽ trả 503. '
    + 'Đặt API_KEY trong môi trường (Render: Environment) rồi deploy lại.');
}

function requireApiKey(req, res, next) {
  if (PUBLIC_PATHS.has(req.path)) return next();

  if (!API_KEY) {
    return res.status(503).json({
      error: 'API chưa được cấu hình xác thực',
      detail: 'Biến môi trường API_KEY chưa đặt. API từ chối phục vụ thay vì mở công khai.'
    });
  }

  const presented = req.get('x-api-key') || (req.get('authorization') || '').replace(/^Bearer\s+/i, '');
  if (!presented || !safeEqual(presented, API_KEY)) {
    console.warn('[SECURITY] Từ chối %s %s (thiếu hoặc sai API key)', req.method, req.path);
    return res.status(401).json({ error: 'Thiếu hoặc sai API key', header: 'x-api-key' });
  }
  return next();
}

// So sánh theo thời gian hằng: `===` trên chuỗi thoát sớm ở ký tự lệch đầu tiên
// và rò rỉ độ dài tiền tố khớp qua thời gian phản hồi.
function safeEqual(a, b) {
  const bufA = Buffer.from(String(a));
  const bufB = Buffer.from(String(b));
  if (bufA.length !== bufB.length) return false;
  return crypto.timingSafeEqual(bufA, bufB);
}

// Middleware
// CORS đóng mặc định: chỉ những origin được khai trong ALLOWED_ORIGINS mới qua.
// Không khai thì không origin nào qua — trang tĩnh cùng gốc vẫn gọi được vì
// same-origin không đi qua CORS.
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '')
  .split(',').map(s => s.trim()).filter(Boolean);
app.use(cors({
  origin: ALLOWED_ORIGINS.length ? ALLOWED_ORIGINS : false,
  credentials: false
}));
app.use(express.json());
app.use('/api', requireApiKey);
app.use(express.static(path.join(__dirname)));

console.log('[SERVER] SentinelOps Web Server starting...');
console.log('[SERVER] State directory:', STATE_DIR);
console.log('[SERVER] Serving from:', __dirname);
console.log('[SERVER] Node environment:', process.env.NODE_ENV || 'development');

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function sendStateFile(filename, res) {
  const allowedFiles = [
    'assets.json',
    'shadow_assets.json',
    'incidents.json',
    'risk_score.json',
    'system_health.json',
    'defender_status.json',
    'firewall_status.json',
    'notification_history.json',
    'waap_status.json',
    'domain_status.json',
    'priority_queue.json',
    'asset_changes.json',
    'service_changes.json',
    'crypto_inventory.json',
    'patch_queue.json',
    'crypto_health.json',
    'asset_aging.json',
    'pipeline_summary.json',
    'hunting_persistence.json',
    'hunting_lateral_movement.json',
    'hunting_credential_dumping.json',
    'hunting_suspicious_processes.json',
    'timeline.json',
    'alert_queue.json',
    'sensor_coverage.json'
  ];

  if (!allowedFiles.includes(filename)) {
    return res.status(403).json({ error: 'File not allowed' });
  }

  const filepath = path.join(STATE_DIR, filename);

  try {
    if (!fs.existsSync(filepath)) {
      return res.status(404).json({ error: 'File not found', file: filename });
    }
    const data = JSON.parse(fs.readFileSync(filepath, 'utf8'));
    const stat = fs.statSync(filepath);
    data._source_timestamp = stat.mtime.toISOString();
    data._fetched_at = new Date().toISOString();
    res.json(data);
  } catch (error) {
    console.error(`[ERROR] Reading ${filename}:`, error.message);
    res.status(500).json({ error: 'Failed to read file', details: error.message });
  }
}

// ============================================================================
// API ROUTES - Data endpoints
// ============================================================================

// Generic state file endpoint - uses helper function
app.get('/api/state/:filename', (req, res) => {
  sendStateFile(req.params.filename, res);
});

// Convenience routes - shortcuts for common endpoints
console.log('[ROUTES] Registering convenience routes...');
app.get('/api/assets', (req, res) => {
  console.log('[ROUTE] /api/assets called');
  sendStateFile('assets.json', res);
});
app.get('/api/incidents', (req, res) => {
  console.log('[ROUTE] /api/incidents called');
  sendStateFile('incidents.json', res);
});
app.get('/api/risk', (req, res) => {
  console.log('[ROUTE] /api/risk called');
  sendStateFile('risk_score.json', res);
});
app.get('/api/history', (req, res) => {
  console.log('[ROUTE] /api/history called');
  sendStateFile('notification_history.json', res);
});
app.get('/api/defender', (req, res) => {
  console.log('[ROUTE] /api/defender called');
  sendStateFile('defender_status.json', res);
});
app.get('/api/firewall', (req, res) => {
  console.log('[ROUTE] /api/firewall called');
  sendStateFile('firewall_status.json', res);
});
app.get('/api/waap', (req, res) => {
  console.log('[ROUTE] /api/waap called');
  sendStateFile('waap_status.json', res);
});
app.get('/api/domain', (req, res) => {
  console.log('[ROUTE] /api/domain called');
  sendStateFile('domain_status.json', res);
});
app.get('/api/aging', (req, res) => {
  console.log('[ROUTE] /api/aging called');
  sendStateFile('asset_aging.json', res);
});
console.log('[ROUTES] Convenience routes registered');

// Health check endpoint
app.get('/api/health', (req, res) => {
  // Duong nay CONG KHAI (health check cua Render goi no), nen no khong duoc
  // khai duong dan he thong hay so luong tep trang thai — do la trinh sat ha
  // tang mien phi cho nguoi chua co khoa.
  res.json({
    status: 'operational',
    timestamp: new Date().toISOString()
  });
});

// Overall status endpoint
app.get('/api/status', (req, res) => {
  try {
    const assetsPath = path.join(STATE_DIR, 'assets.json');
    const incidentsPath = path.join(STATE_DIR, 'incidents.json');
    const riskPath = path.join(STATE_DIR, 'risk_score.json');

    let assets = { total_assets: 0 };
    let incidents = { total_incidents: 0 };
    let risk = { overall_score: 0 };

    if (fs.existsSync(assetsPath)) {
      assets = JSON.parse(fs.readFileSync(assetsPath, 'utf8'));
    }
    if (fs.existsSync(incidentsPath)) {
      incidents = JSON.parse(fs.readFileSync(incidentsPath, 'utf8'));
    }
    if (fs.existsSync(riskPath)) {
      risk = JSON.parse(fs.readFileSync(riskPath, 'utf8'));
    }

    res.json({
      operational: true,
      timestamp: new Date().toISOString(),
      metrics: {
        assets_monitored: assets.total_assets || 0,
        open_incidents: incidents.total_incidents || 0,
        overall_risk: risk.overall_score || 0,
        risk_level: risk.risk_level || getThreatLevel(risk.overall_score || 0),
        // threat_level kept as an alias for older clients
        threat_level: risk.risk_level || getThreatLevel(risk.overall_score || 0)
      }
    });
  } catch (error) {
    console.error('[ERROR] Getting status:', error.message);
    res.status(500).json({ error: 'Failed to get status', operational: false });
  }
});


// ============================================================================
// DAILY BRIEF ROUTES
// ============================================================================

const BRIEF_DIR = path.join(__dirname, '..', 'daily_brief');
const BRIEF_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

// List available briefs - one entry per date, newest first
app.get('/api/daily-brief/list', (req, res) => {
  try {
    if (!fs.existsSync(BRIEF_DIR)) {
      return res.json({ total: 0, briefs: [] });
    }

    const byDate = new Map();
    for (const file of fs.readdirSync(BRIEF_DIR)) {
      const match = file.match(/^(\d{4}-\d{2}-\d{2})\.(json|html)$/);
      if (!match) continue; // skips latest.html and anything unexpected

      const [, date, ext] = match;
      const entry = byDate.get(date) || { date, has_json: false, has_html: false, modified: null };
      entry[ext === 'json' ? 'has_json' : 'has_html'] = true;

      const mtime = fs.statSync(path.join(BRIEF_DIR, file)).mtime.toISOString();
      if (!entry.modified || mtime > entry.modified) entry.modified = mtime;

      byDate.set(date, entry);
    }

    const briefs = [...byDate.values()].sort((a, b) => b.date.localeCompare(a.date));
    res.json({ total: briefs.length, briefs, latest: briefs[0]?.date || null });
  } catch (error) {
    console.error('[ERROR] Listing briefs:', error.message);
    res.status(500).json({ error: 'Failed to list briefs', details: error.message });
  }
});

// Fetch one brief by date - JSON by default, ?format=html for the rendered page
app.get('/api/daily-brief/:date', (req, res) => {
  const { date } = req.params;

  if (!BRIEF_DATE_RE.test(date)) {
    return res.status(400).json({ error: 'Invalid date format, expected YYYY-MM-DD', date });
  }

  const wantsHtml = req.query.format === 'html';
  const filepath = path.join(BRIEF_DIR, `${date}.${wantsHtml ? 'html' : 'json'}`);

  try {
    if (!fs.existsSync(filepath)) {
      return res.status(404).json({ error: 'Brief not found', date, format: wantsHtml ? 'html' : 'json' });
    }

    if (wantsHtml) {
      return res.type('html').send(fs.readFileSync(filepath, 'utf8'));
    }

    const data = JSON.parse(fs.readFileSync(filepath, 'utf8'));
    data._source_timestamp = fs.statSync(filepath).mtime.toISOString();
    res.json(data);
  } catch (error) {
    console.error(`[ERROR] Reading brief ${date}:`, error.message);
    res.status(500).json({ error: 'Failed to read brief', details: error.message });
  }
});

// ============================================================================
// ROUTES KẾ THỪA TỪ web-server.js (AQ-007 / AQ-030)
// ============================================================================
//
// Render chạy `web-server.js` suốt sáu vòng audit. Những URL dưới đây là URL
// mà server đó phục vụ và người ta đã mở — chúng nằm trong `render.yaml`, có
// thể đang nằm trong bookmark hay một tin nhắn Telegram cũ.
//
// Đổi điểm vào mà bỏ chúng thì sửa xong một lỗi truth và tạo ra một lỗi khác:
// liên kết từng chạy nay 404. Nên giữ, và giữ ở đây, cạnh nhau, có nhãn — chứ
// không giữ bằng cách để nguyên server thứ hai.

app.get('/latest', (req, res) => {
  const filepath = path.join(BRIEF_DIR, 'latest.html');
  if (!fs.existsSync(filepath)) {
    return res.status(404).type('html').send(
      '<h1>404 - Chưa có bản tin</h1><p>Chưa có daily brief nào được sinh ra.</p>');
  }
  res.sendFile(filepath);
});

app.get('/brief/:date', (req, res) => {
  const { date } = req.params;
  if (!BRIEF_DATE_RE.test(date)) {
    return res.status(400).type('html').send(
      '<h1>400 - Sai định dạng ngày</h1><p>Dùng YYYY-MM-DD.</p>');
  }
  const filepath = path.join(BRIEF_DIR, `${date}.html`);
  if (!fs.existsSync(filepath)) {
    return res.status(404).type('html').send(
      `<h1>404 - Không có bản tin</h1><p>Không có bản tin cho ngày ${date}.</p>`);
  }
  res.sendFile(filepath);
});

// `render.yaml` định tuyến `/health`; API mới đặt nó ở `/api/health`. Health
// check của nền tảng gọi đường cũ, nên đường cũ phải sống.
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'sentinelops-soc',
    entrypoint: 'web/server.js',
    timestamp: new Date().toISOString(),
  });
});

// ============================================================================
// STATIC ROUTES
// ============================================================================

// Serve index.html for root
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Fallback for single-page app routing
app.get('*', (req, res) => {
  if (!req.path.startsWith('/api/')) {
    res.sendFile(path.join(__dirname, 'index.html'));
  } else {
    res.status(404).json({ error: 'API endpoint not found', path: req.path });
  }
});

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// Fallback only - risk_score.json is risk-ascending and publishes risk_level
// directly (including the severity floor), so prefer that field when present.
function getThreatLevel(score) {
  if (score >= 80) return 'CRITICAL';
  if (score >= 60) return 'HIGH';
  if (score >= 40) return 'MEDIUM';
  return 'LOW';
}

// ============================================================================
// START SERVER
// ============================================================================

app.listen(PORT, () => {
  console.log(`[SERVER] SentinelOps Web Server listening on port ${PORT}`);
  console.log(`[SERVER] Access at: http://localhost:${PORT}`);
  console.log(`[SERVER] Data API: http://localhost:${PORT}/api/state/`);
  console.log(`[SERVER] Health check: http://localhost:${PORT}/api/health`);
});

export default app;
