#!/usr/bin/env node
/**
 * export-home-soc-reports.js
 *
 * Projects sanitized Home SOC status from the PRIVATE repo (mcp-cyber-tools)
 * into the PUBLIC repo (home-soc-reports), then commits and pushes.
 *
 * Reads the newest of each artifact type, emits exactly three files, refuses to
 * write anything that still carries an identifier.
 *
 *   node export-home-soc-reports.js              generate, commit, push
 *   node export-home-soc-reports.js --no-push    generate + commit, no push
 *   node export-home-soc-reports.js --dry-run    print to stdout, write nothing
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');

const SRC = __dirname;
const DEST = path.resolve(SRC, '..', 'home-soc-reports');
const BRANCH = 'main';
const STALE_HOURS = 48;

const DRY_RUN = process.argv.includes('--dry-run');
const NO_PUSH = process.argv.includes('--no-push');

// ---------------------------------------------------------------- utilities

function log(msg) { console.log(msg); }
function fail(msg) { console.error(`\n[ABORT] ${msg}\n`); process.exit(1); }

/** Newest file matching a predicate, searched one level deep under SRC. */
function newestFile(dir, predicate) {
  const full = path.join(SRC, dir);
  if (!fs.existsSync(full)) return null;
  const hits = fs.readdirSync(full)
    .filter(predicate)
    .map(name => {
      const p = path.join(full, name);
      return { path: p, name, mtime: fs.statSync(p).mtimeMs };
    })
    .sort((a, b) => b.mtime - a.mtime);
  return hits[0] || null;
}

function readJson(file) {
  try {
    // Strip a UTF-8 BOM: PowerShell's Set-Content -Encoding utf8 writes one and
    // JSON.parse rejects it. Collector files are routinely touched from PowerShell.
    return JSON.parse(fs.readFileSync(file, 'utf-8').replace(/^﻿/, ''));
  } catch (e) { fail(`Cannot parse ${file}: ${e.message}`); }
}

function hoursSince(iso) {
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return null;
  return (Date.now() - t) / 36e5;
}

// ------------------------------------------------------------ sanitization

const PUBLIC_RESOLVERS = new Set([
  '8.8.8.8', '8.8.4.4', '1.1.1.1', '1.0.0.1',
  '9.9.9.9', '149.112.112.112', '208.67.222.222', '208.67.220.220',
]);

function isPrivateIp(ip) {
  const o = ip.split('.').map(Number);
  if (o.length !== 4 || o.some(n => Number.isNaN(n))) return false;
  return o[0] === 10
    || (o[0] === 172 && o[1] >= 16 && o[1] <= 31)
    || (o[0] === 192 && o[1] === 168);
}

/** DNS resolvers -> a class name, never the addresses themselves. */
function classifyDns(servers) {
  const list = servers.filter(Boolean);
  if (list.length === 0) return 'unknown';
  if (list.every(isPrivateIp)) return 'local_resolver';
  if (list.every(ip => PUBLIC_RESOLVERS.has(ip))) return 'public_resolver';
  if (list.some(ip => PUBLIC_RESOLVERS.has(ip))) return 'mixed_resolver';
  return 'isp_default';
}

/** Port number -> service class. Never publish the number. */
function classifyPort(port) {
  switch (port) {
    case 22:   return 'remote-shell';
    case 23:   return 'unencrypted-remote-login';
    case 21:   return 'unencrypted-file-transfer';
    case 3389: return 'remote-desktop';
    case 445:
    case 139:  return 'file-sharing';
    case 554:
    case 8554: return 'video-stream';
    case 1883:
    case 8883: return 'message-broker';
    case 80:
    case 443:
    case 8000:
    case 8080:
    case 8443: return 'web-ui';
    case 53:   return 'dns-service';
    default:   return 'vendor-service';
  }
}

/** Service classes that mean "someone can log in over the network". */
const REMOTE_ACCESS = new Set([
  'remote-shell', 'unencrypted-remote-login', 'remote-desktop',
]);

/** deviceType/vendor -> generic label + category. Vendor is discarded. */
function classifyDevice(deviceType) {
  const t = (deviceType || '').toLowerCase();
  if (t.includes('router') || t.includes('gateway')) return { label: 'Gateway', category: 'network', prefix: 'gateway' };
  if (t.includes('camera') || t.includes('nvr'))     return { label: 'Camera', category: 'iot', prefix: 'camera' };
  if (t.includes('printer'))                         return { label: 'Printer', category: 'iot', prefix: 'printer' };
  if (t.includes('tv') || t.includes('media'))       return { label: 'Media Device', category: 'iot', prefix: 'media' };
  if (t.includes('speaker') || t.includes('echo'))   return { label: 'Smart Speaker', category: 'iot', prefix: 'speaker' };
  if (t.includes('phone') || t.includes('mobile'))   return { label: 'Mobile Device', category: 'mobile', prefix: 'mobile' };
  if (t.includes('laptop') || t.includes('desktop') || t.includes('computer') || t.includes('pc'))
    return { label: 'Computer', category: 'computer', prefix: 'computer' };
  return { label: 'Unidentified Device', category: 'unknown', prefix: 'device' };
}

// -------------------------------------------------------------- leak guard

const VENDOR_WORDS = [
  'arris', 'commscope', 'reolink', 'shenzhen', 'netgear', 'tp-link', 'tplink',
  'ubiquiti', 'hikvision', 'dahua', 'linksys', 'asus', 'eero', 'cox', 'xfinity',
  'comcast', 'spectrum', 'att', 'verizon', 'google nest', 'wyze', 'ring',
];

const LEAK_PATTERNS = [
  { name: 'MAC address',       re: /\b[0-9a-f]{2}([-:])[0-9a-f]{2}(?:\1[0-9a-f]{2}){4}\b/i },
  { name: 'IPv4 address',      re: /\b(?:\d{1,3}\.){3}\d{1,3}\b/ },
  { name: 'IPv6 address',      re: /\b(?:[0-9a-f]{1,4}:){3,}[0-9a-f]{0,4}\b/i },
  { name: 'credential keyword', re: /\b(pass(word|wd)|token|secret|api[_-]?key|bearer|credential)\b\s*[:=]/i },
  { name: 'private key block', re: /-----BEGIN [A-Z ]*PRIVATE KEY-----/ },
];

/**
 * Refuse to publish anything carrying an identifier. Runs over the exact bytes
 * that would be written. Any hit aborts the whole export — nothing is written,
 * nothing is pushed.
 */
function assertClean(filename, content, extraForbidden = []) {
  for (const { name, re } of LEAK_PATTERNS) {
    const m = content.match(re);
    if (m) fail(`${filename} would leak a ${name}: "${m[0]}"\nExport aborted. No files written, nothing pushed.`);
  }
  // Whole-word match only: "ring" must not fire on "monitoring".
  for (const word of [...VENDOR_WORDS, ...extraForbidden.map(s => s.toLowerCase())]) {
    if (!word) continue;
    const escaped = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    if (new RegExp(`(?<![\\w-])${escaped}(?![\\w-])`, 'i').test(content)) {
      fail(`${filename} would leak the identifier "${word}".\nExport aborted. No files written, nothing pushed.`);
    }
  }
}

// ----------------------------------------------------------- load artifacts

log('Reading Home SOC artifacts...\n');

const scanFile = newestFile('network-scan-data', n => /^network-scan-.*\.json$/.test(n));
if (!scanFile) fail('No network-scan-*.json found under network-scan-data/. Run the network scanner first.');

const hostFile = newestFile('laptop-collection-data', n => /\.json$/.test(n));
const baseFile = newestFile('baseline', n => /^BASELINE-.*\.json$/.test(n));

// Optional: security-watch outputs, when that collector has run.
const watchState = fs.existsSync(path.join(SRC, 'state.json'))
  ? readJson(path.join(SRC, 'state.json')) : null;
const watchBase = fs.existsSync(path.join(SRC, 'baseline.json'))
  ? readJson(path.join(SRC, 'baseline.json')) : null;

const scan = readJson(scanFile.path);
const host = hostFile ? readJson(hostFile.path) : null;

log(`  scan      ${scanFile.name}  (${scan.devices?.length ?? 0} devices)`);
log(`  host      ${hostFile ? hostFile.name : '— none —'}`);
log(`  baseline  ${baseFile ? baseFile.name : '— none —'}`);
log(`  watch     ${watchState ? 'state.json present' : '— none —'}\n`);

// SSID must never appear in output; feed it to the leak guard explicitly.
const ssid = host?.data?.wifiStatus?.ssid || '';

// ------------------------------------------------------- build DEVICE-SUMMARY

const counters = {};
const devices = [];
let remoteAccessFindings = [];

for (const d of (scan.devices || [])) {
  const cls = classifyDevice(d.deviceType);
  counters[cls.prefix] = (counters[cls.prefix] || 0) + 1;
  const id = `${cls.prefix}-${String(counters[cls.prefix]).padStart(2, '0')}`;

  const services = [...new Set((d.openPorts || []).map(p => classifyPort(p.port)))].sort();
  const exposed = services.filter(s => REMOTE_ACCESS.has(s));
  if (exposed.length) {
    remoteAccessFindings.push({ id, label: cls.label, services: exposed });
  }

  devices.push({
    id,
    label: cls.label,
    category: cls.category,
    link: 'lan',
    status: 'online',
    identified: Boolean(d.identified),
    services,
    open_service_count: (d.openPorts || []).length,
    risk_count: (d.risks || []).length,
  });
}

const deviceSummary = {
  schema_version: '1.0',
  generated_at: new Date().toISOString(),
  source_scan_at: scan.timestamp || null,
  sanitized: true,
  totals: {
    devices_total: devices.length,
    devices_identified: devices.filter(d => d.identified).length,
    devices_unidentified: devices.filter(d => !d.identified).length,
    total_risks: scan.totalRisks ?? devices.reduce((n, d) => n + d.risk_count, 0),
  },
  devices,
};

// ----------------------------------------------------------- build BASELINE

/** Report a control honestly: unknown when no collector produced it. */
function control(state, extra = {}) {
  return { state, changed_since_baseline: false, ...extra };
}

const dnsServers = (host?.data?.dns || [])
  .flatMap(i => i.ServerAddresses || []);
const dnsClass = classifyDns(dnsServers);

const dnsBaseline = watchBase?.dns ? classifyDns(String(watchBase.dns).split(/[,\s]+/)) : null;

const controls = {
  dns: control(dnsClass === 'unknown' ? 'unknown' : 'observed', {
    provider_class: dnsClass,
    changed_since_baseline: dnsBaseline ? dnsBaseline !== dnsClass : false,
  }),
  firewall: watchState
    ? control(watchState.fw === true ? 'enabled' : watchState.fw === false ? 'disabled' : 'unknown', {
        changed_since_baseline: watchBase ? watchState.fw !== watchBase.fw : false,
      })
    : control('unknown'),
  defender: watchState
    ? control(watchState.def === true ? 'enabled' : watchState.def === false ? 'disabled' : 'unknown', {
        changed_since_baseline: watchBase ? watchState.def !== watchBase.def : false,
      })
    : control('unknown'),
  rdp: watchState
    ? control(watchState.rdp ? 'open' : 'closed', {
        changed_since_baseline: watchBase ? watchState.rdp !== watchBase.rdp : false,
      })
    : control('unknown'),
  ssh: watchState
    ? control(watchState.ssh ? 'open' : 'closed', {
        changed_since_baseline: watchBase ? watchState.ssh !== watchBase.ssh : false,
      })
    : control('unknown'),
  remote_access_services: control(
    remoteAccessFindings.length ? 'exposed_on_lan' : 'none_detected',
    { affected_device_count: remoteAccessFindings.length }
  ),
};

// Alerts are derived, never invented: a control that flipped, or a LAN-exposed
// remote-access service, is an alert. Nothing else is.
const alerts = [];

for (const [name, c] of Object.entries(controls)) {
  if (c.changed_since_baseline) {
    alerts.push({
      type: `${name.toUpperCase()}_CHANGED`,
      severity: 'CRITICAL',
      control: name,
      current_state: c.state,
      detected_at: new Date().toISOString(),
    });
  }
}

for (const f of remoteAccessFindings) {
  const critical = f.services.includes('unencrypted-remote-login');
  alerts.push({
    type: 'REMOTE_ACCESS_SERVICE_ON_LAN',
    severity: critical ? 'CRITICAL' : 'WARNING',
    device_id: f.id,
    device_label: f.label,
    services: f.services,
    detected_at: scan.timestamp || new Date().toISOString(),
  });
}

const unknownControls = Object.values(controls).filter(c => c.state === 'unknown').length;
const riskLevel = alerts.some(a => a.severity === 'CRITICAL') ? 'RED'
  : alerts.length > 0 ? 'YELLOW'
  : 'GREEN';

const scanAgeH = scan.timestamp ? hoursSince(scan.timestamp) : null;

const baselineOut = {
  schema_version: '1.0',
  baseline_id: baseFile ? `BL-${baseFile.name.replace(/^BASELINE-|\.json$/g, '')}` : 'BL-UNSET',
  generated_at: new Date().toISOString(),
  source_scan_at: scan.timestamp || null,
  data_age_hours: scanAgeH === null ? null : Number(scanAgeH.toFixed(1)),
  stale: scanAgeH !== null && scanAgeH > STALE_HOURS,
  sanitized: true,
  coverage: {
    controls_reported: Object.keys(controls).length,
    controls_unknown: unknownControls,
    note: unknownControls
      ? 'Controls marked unknown have no collector output. security-watch.js has not produced state.json.'
      : 'All controls reported by a collector.',
  },
  controls,
  alerts,
  risk_level: riskLevel,
};

// ------------------------------------------------------------- publish identity
//
// OPEN-001. A commit cannot contain its own SHA — the SHA is derived from the
// content, so embedding it is circular. Instead each publish carries a
// deterministic fingerprint of the data it reports. The bulletin resolves the
// real commit SHA from the GitHub API and displays both, so a reader can tell
// which publish they are looking at rather than trusting a timestamp.
//
// Computed over the source data, never over the output that carries it, so the
// value is stable and self-consistent.

const publishId = crypto.createHash('sha256').update(JSON.stringify({
  source_scan_at: scan.timestamp || null,
  controls,
  devices,
  alerts,
})).digest('hex').slice(0, 16);

deviceSummary.publish_id = publishId;
baselineOut.publish_id = publishId;

// ------------------------------------------------------------- build AUDIT MD

const auditDate = (scan.timestamp || new Date().toISOString()).slice(0, 10);

function controlRow(label, c) {
  const marks = {
    enabled: 'OK', disabled: 'ATTENTION', closed: 'OK', open: 'ATTENTION',
    observed: 'OK', none_detected: 'OK', exposed_on_lan: 'REVIEW', unknown: 'NO DATA',
  };
  const detail = c.provider_class ? ` (${c.provider_class})` : '';
  return `| ${label} | ${c.state}${detail} | ${marks[c.state] || '—'} |`;
}

const auditMd = `# Router Security Audit — Latest

**Audit date:** ${auditDate}
**Scope:** Home gateway, WiFi, and LAN device inventory
**Sanitized:** yes — no addresses, hardware identifiers, vendors, or model/firmware strings
**Generated by:** export-home-soc-reports.js
**Publish ID:** \`${publishId}\`
**Generated at:** ${baselineOut.generated_at}
**Source scan at:** ${scan.timestamp || 'unknown'}

---

## Summary

**Risk level:** ${riskLevel}
**Devices seen:** ${deviceSummary.totals.devices_total} (${deviceSummary.totals.devices_unidentified} unidentified)
**Open alerts:** ${alerts.length}
${baselineOut.stale ? `\n> ⚠️ Scan data is ${baselineOut.data_age_hours}h old (threshold ${STALE_HOURS}h). The collector may have stopped.\n` : ''}
---

## Control state

| Control | State | Assessment |
|---|---|---|
${controlRow('DNS resolvers', controls.dns)}
${controlRow('Firewall', controls.firewall)}
${controlRow('Endpoint protection', controls.defender)}
${controlRow('Remote desktop', controls.rdp)}
${controlRow('Remote shell', controls.ssh)}
${controlRow('Remote-access services on LAN', controls.remote_access_services)}

${unknownControls ? `> ${unknownControls} control(s) report **NO DATA**. No collector has produced state for them — this is a coverage gap, not a clean result.\n` : ''}
---

## Device inventory

| ID | Type | Category | Services | Risks |
|---|---|---|---|---|
${devices.map(d =>
  `| ${d.id} | ${d.label} | ${d.category} | ${d.services.join(', ') || '—'} | ${d.risk_count} |`
).join('\n')}

Service names are classes, not port numbers. \`web-ui\` covers management interfaces,
\`video-stream\` covers camera streams, \`message-broker\` covers IoT messaging,
\`vendor-service\` covers proprietary services that could not be identified.

---

## Findings

${alerts.length === 0
  ? 'No alerts. No control changed since baseline, and no remote-access service was detected on the LAN.'
  : alerts.map(a => {
      if (a.type === 'REMOTE_ACCESS_SERVICE_ON_LAN') {
        return `- **${a.severity}** — ${a.device_label} (\`${a.device_id}\`) exposes ${a.services.join(', ')} on the local network.`;
      }
      return `- **${a.severity}** — control \`${a.control}\` changed since baseline; now \`${a.current_state}\`.`;
    }).join('\n')}

---

## Recommended actions

**Weekly**
- Review the device inventory above for entries you do not recognise
- Confirm the unidentified device count has not grown

**Monthly**
- Check the gateway for firmware updates
- Re-verify the firewall profile is still hardened

**Annually**
- Rotate WiFi passwords
- Full firewall rule audit
- Check IoT devices for end-of-life status

${unknownControls ? `**Coverage gap**\n- Run \`security-watch.js\` so firewall, endpoint protection, remote desktop, and remote shell stop reporting NO DATA\n` : ''}
---

**Next review:** ${new Date(Date.now() + 7 * 864e5).toISOString().slice(0, 10)}
`;

// ---------------------------------------------------------------- leak gate

const outputs = [
  { name: 'DEVICE-SUMMARY.json', body: JSON.stringify(deviceSummary, null, 2) + '\n' },
  { name: 'BASELINE-LATEST.json', body: JSON.stringify(baselineOut, null, 2) + '\n' },
  { name: 'ROUTER-SECURITY-AUDIT-LATEST.md', body: auditMd },
];

log('Running leak guard...');
for (const o of outputs) {
  assertClean(o.name, o.body, [ssid]);
  log(`  ${o.name}  clean`);
}
log('');

// ------------------------------------------------------------------- write

if (DRY_RUN) {
  for (const o of outputs) {
    log(`\n${'='.repeat(70)}\n${o.name}\n${'='.repeat(70)}\n${o.body}`);
  }
  log('\n[dry-run] Nothing written, nothing pushed.');
  process.exit(0);
}

if (!fs.existsSync(DEST)) fail(`Destination repo not found: ${DEST}`);
if (!fs.existsSync(path.join(DEST, '.git'))) fail(`${DEST} is not a git repository. Run the one-time setup first.`);

for (const o of outputs) {
  fs.writeFileSync(path.join(DEST, o.name), o.body, 'utf-8');
  log(`Wrote ${o.name}`);
}

// -------------------------------------------------------------------- git

function git(args, opts = {}) {
  return execFileSync('git', args, { cwd: DEST, encoding: 'utf-8', ...opts }).trim();
}

log('\nPublishing...');

git(['add', '-f', ...outputs.map(o => o.name)]);

const staged = git(['diff', '--cached', '--name-only']);
if (!staged) {
  log('  No changes since last export. Nothing to commit.');
  process.exit(0);
}

git(['commit', '-m', `data: Home SOC status ${auditDate} (risk ${riskLevel}, ${alerts.length} alert${alerts.length === 1 ? '' : 's'})`]);
log(`  Committed: ${staged.split('\n').join(', ')}`);

if (NO_PUSH) {
  log('  --no-push set. Commit created locally, not pushed.');
  process.exit(0);
}

try {
  git(['push', 'origin', BRANCH], { stdio: 'pipe' });
  log(`  Pushed to origin/${BRANCH}`);
} catch (e) {
  fail(`Push failed: ${(e.stderr || e.message).toString().trim()}`);
}

log(`\nDone. Risk ${riskLevel}, ${alerts.length} alert(s), ${devices.length} device(s).`);
