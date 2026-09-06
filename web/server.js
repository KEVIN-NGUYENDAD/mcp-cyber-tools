import express from 'express';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Determine state directory - try multiple locations
const possibleDirs = [
  process.env.STATE_DIR,
  path.join(process.cwd(), 'state'),
  path.join(__dirname, '..', 'state'),
  '/var/task/state', // Vercel serverless function
  './state'
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
  STATE_DIR = path.join(process.cwd(), 'state');
}

// Middleware
app.use(cors());
app.use(express.json());
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
    'crypto_inventory.json'
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
console.log('[ROUTES] Convenience routes registered');

// Health check endpoint
app.get('/api/health', (req, res) => {
  const stateDir = STATE_DIR;
  const files = fs.readdirSync(stateDir).filter(f => f.endsWith('.json'));

  res.json({
    status: 'operational',
    timestamp: new Date().toISOString(),
    state_files: files.length,
    state_directory: stateDir
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
        threat_level: getThreatLevel(risk.overall_score || 0)
      }
    });
  } catch (error) {
    console.error('[ERROR] Getting status:', error.message);
    res.status(500).json({ error: 'Failed to get status', operational: false });
  }
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
