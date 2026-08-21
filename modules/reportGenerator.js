import fs from "fs";
import path from "path";

const REPORTS_DIR = "./reports";

function ensureReportsDir() {
  if (!fs.existsSync(REPORTS_DIR)) {
    fs.mkdirSync(REPORTS_DIR, { recursive: true });
  }
}

export function generateJsonReport(title, data, reportType = "general") {
  ensureReportsDir();
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const filename = `${REPORTS_DIR}/${reportType}_${timestamp}.json`;

  const report = {
    title,
    timestamp: new Date().toISOString(),
    type: reportType,
    data
  };

  fs.writeFileSync(filename, JSON.stringify(report, null, 2));
  return { success: true, path: filename };
}

export function generateHtmlReport(title, data, reportType = "general") {
  ensureReportsDir();
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const filename = `${REPORTS_DIR}/${reportType}_${timestamp}.html`;

  const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
    .info { background: #e7f3ff; padding: 10px; border-radius: 4px; margin: 10px 0; }
    .timestamp { color: #666; font-size: 0.9em; }
    pre { background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; margin: 15px 0; }
    th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
    th { background: #007bff; color: white; }
    tr:hover { background: #f5f5f5; }
  </style>
</head>
<body>
  <div class="container">
    <h1>${title}</h1>
    <div class="info">
      <p><strong>Type:</strong> ${reportType}</p>
      <p class="timestamp"><strong>Generated:</strong> ${new Date().toLocaleString()}</p>
    </div>
    <pre>${typeof data === 'string' ? data : JSON.stringify(data, null, 2)}</pre>
  </div>
</body>
</html>
  `;

  fs.writeFileSync(filename, htmlContent);
  return { success: true, path: filename };
}

export function generateAuditReport(title, categories, reportType = "audit") {
  ensureReportsDir();
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const filename = `${REPORTS_DIR}/${reportType}_${timestamp}.html`;

  const rows = Object.entries(categories)
    .map(([key, value]) => `<tr><td>${key}</td><td>${value.status}</td><td>${value.details}</td></tr>`)
    .join("");

  const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
    h1 { color: #333; border-bottom: 2px solid #dc3545; }
    .critical { background: #f8d7da; } .warning { background: #fff3cd; } .ok { background: #d4edda; }
    table { width: 100%; border-collapse: collapse; margin: 15px 0; }
    th, td { padding: 12px; text-align: left; border: 1px solid #ddd; }
    th { background: #343a40; color: white; }
  </style>
</head>
<body>
  <div class="container">
    <h1>${title}</h1>
    <p>Generated: ${new Date().toLocaleString()}</p>
    <table>
      <tr><th>Category</th><th>Status</th><th>Details</th></tr>
      ${rows}
    </table>
  </div>
</body>
</html>
  `;

  fs.writeFileSync(filename, htmlContent);
  return { success: true, path: filename };
}
