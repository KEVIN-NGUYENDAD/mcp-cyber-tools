import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;
const DAILY_BRIEF_DIR = path.join(__dirname, 'daily_brief');

// Middleware
app.use(express.static('public'));
app.use(express.json());

// CORS headers
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  next();
});

// Routes

// Serve latest.html
app.get('/latest', (req, res) => {
  const filePath = path.join(DAILY_BRIEF_DIR, 'latest.html');
  if (fs.existsSync(filePath)) {
    res.sendFile(filePath);
  } else {
    res.status(404).send('<h1>404 - Latest Brief Not Found</h1><p>No daily brief generated yet.</p>');
  }
});

// Serve latest.html as default root
app.get('/', (req, res) => {
  const filePath = path.join(DAILY_BRIEF_DIR, 'latest.html');
  if (fs.existsSync(filePath)) {
    res.sendFile(filePath);
  } else {
    res.status(404).send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>SentinelOps Daily Brief</title>
        <style>
          body { font-family: Arial, sans-serif; text-align: center; padding: 40px; }
          h1 { color: #1f2937; }
          p { color: #6b7280; }
        </style>
      </head>
      <body>
        <h1>📊 SentinelOps Daily Brief</h1>
        <p>No daily brief generated yet.</p>
        <p>Check back later or contact your security team.</p>
      </body>
      </html>
    `);
  }
});

// Serve dated briefsby date (YYYY-MM-DD)
app.get('/brief/:date', (req, res) => {
  const date = req.params.date;
  // Validate date format
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return res.status(400).send('<h1>400 - Invalid Date Format</h1><p>Use YYYY-MM-DD format.</p>');
  }

  const filePath = path.join(DAILY_BRIEF_DIR, `${date}.html`);
  if (fs.existsSync(filePath)) {
    res.sendFile(filePath);
  } else {
    res.status(404).send(`<h1>404 - Brief Not Found</h1><p>No brief available for ${date}.</p>`);
  }
});

// List available briefs (JSON API)
app.get('/api/briefs', (req, res) => {
  try {
    const files = fs.readdirSync(DAILY_BRIEF_DIR)
      .filter(f => f.endsWith('.html'))
      .map(f => ({
        filename: f,
        url: f === 'latest.html' ? '/latest' : `/brief/${f.replace('.html', '')}`,
        date: f === 'latest.html' ? 'latest' : f.replace('.html', '')
      }))
      .sort((a, b) => {
        if (a.date === 'latest') return -1;
        if (b.date === 'latest') return 1;
        return b.date.localeCompare(a.date);
      });

    res.json({
      total: files.length,
      latest: files.find(f => f.date === 'latest') || null,
      recent: files.slice(0, 10)
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to list briefs', message: err.message });
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'sentinelops-daily-brief', timestamp: new Date().toISOString() });
});

// Redirect root to latest
app.get('/index.html', (req, res) => {
  res.redirect('/latest');
});

// 404 handler
app.use((req, res) => {
  res.status(404).send(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>404 - Not Found</title>
      <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 40px; background: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }
        h1 { color: #1f2937; }
        a { color: #3b82f6; text-decoration: none; }
        a:hover { text-decoration: underline; }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>404 - Page Not Found</h1>
        <p>The page you're looking for doesn't exist.</p>
        <p><a href="/">View Latest Daily Brief</a></p>
        <p><a href="/api/briefs">View Available Briefs (JSON)</a></p>
      </div>
    </body>
    </html>
  `);
});

// Start server
app.listen(PORT, () => {
  console.log(`[WEB-SERVER] SentinelOps Daily Brief server running at http://localhost:${PORT}`);
  console.log(`[WEB-SERVER] Routes:`);
  console.log(`  GET  /              → Latest brief`);
  console.log(`  GET  /latest        → Latest brief`);
  console.log(`  GET  /brief/YYYY-MM-DD → Specific date brief`);
  console.log(`  GET  /api/briefs    → List all briefs (JSON)`);
  console.log(`  GET  /health        → Health check`);
  console.log(`[WEB-SERVER] Daily Brief Directory: ${DAILY_BRIEF_DIR}`);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('[WEB-SERVER] Shutting down gracefully...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('[WEB-SERVER] SIGTERM received, shutting down...');
  process.exit(0);
});
