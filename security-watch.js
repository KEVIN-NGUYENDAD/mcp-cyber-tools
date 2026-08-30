#!/usr/bin/env node
/**
 * security-watch.js — endpoint control collector
 *
 * One-shot. Reads five Windows security controls, writes state.json, compares
 * against the approved baseline, and appends any change to alerts.json.
 *
 * No email. Delivery is handled downstream by export-home-soc-reports.js and
 * the Claude Scheduled bulletin. This script only produces data.
 *
 *   node security-watch.js                     collect + compare (needs a baseline)
 *   node security-watch.js --approve-baseline  approve the current state as baseline
 *   node security-watch.js --show              print current readings, write nothing
 *
 * Runs unattended: no stdin, no daemon loop, always exits. Task Scheduler owns
 * the cadence. No elevation required.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const BASELINE_FILE = path.join(__dirname, 'baseline.json');
const STATE_FILE = path.join(__dirname, 'state.json');
const ALERTS_FILE = path.join(__dirname, 'alerts.json');
const COOLDOWN_FILE = path.join(__dirname, 'cooldown.json');

const COOLDOWN_MS = 4 * 60 * 60 * 1000;
const MAX_ALERTS = 100;

const APPROVE = process.argv.includes('--approve-baseline');
const SHOW_ONLY = process.argv.includes('--show');

// ------------------------------------------------------------------- io

function readJson(file, fallback) {
  try {
    // Strip a UTF-8 BOM: PowerShell's Set-Content -Encoding utf8 writes one, and
    // JSON.parse rejects it. Without this a hand-edited baseline reads as absent.
    return JSON.parse(fs.readFileSync(file, 'utf-8').replace(/^﻿/, ''));
  } catch { return fallback; }
}

function writeJson(file, data) {
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
}

// --------------------------------------------------------------- detect
// Unchanged from the original. Each returns null when the query fails, so a
// broken probe is reported as unknown rather than silently as "safe".

function ps(command) {
  return execSync(`powershell -NoProfile -Command "${command}"`, {
    encoding: 'utf-8',
    stdio: ['pipe', 'pipe', 'pipe'],
  });
}

function getDNS() {
  try {
    const out = ps('Get-DnsClientServerAddress -AddressFamily IPv4 | Select-Object -ExpandProperty ServerAddresses | ConvertTo-Json');
    try {
      const json = JSON.parse(out);
      return Array.isArray(json) ? [...new Set(json)].join(', ') : String(json);
    } catch {
      return out.trim() || null;
    }
  } catch { return null; }
}

function getFirewall() {
  try {
    return ps('Get-NetFirewallProfile -Profile Public | Select-Object -ExpandProperty Enabled')
      .trim().toLowerCase() === 'true';
  } catch { return null; }
}

function getDefender() {
  try {
    return ps('Get-MpPreference | Select-Object -ExpandProperty DisableRealtimeMonitoring')
      .trim().toLowerCase() === 'false';
  } catch { return null; }
}

function portListening(port) {
  try {
    const out = ps(`if (Get-NetTCPConnection -LocalPort ${port} -State Listen -ErrorAction SilentlyContinue) { 'yes' } else { 'no' }`);
    return out.trim() === 'yes';
  } catch { return null; }
}

const getRDP = () => portListening(3389);
const getSSH = () => portListening(22);

function collect() {
  return {
    dns: getDNS(),
    fw: getFirewall(),
    def: getDefender(),
    rdp: getRDP(),
    ssh: getSSH(),
    collected_at: new Date().toISOString(),
  };
}

function render(s) {
  const b = v => v === null ? 'unknown' : v ? 'enabled' : 'disabled';
  const p = v => v === null ? 'unknown' : v ? 'OPEN' : 'closed';
  return [
    `  DNS      ${s.dns ?? 'unknown'}`,
    `  Firewall ${b(s.fw)}`,
    `  Defender ${b(s.def)}`,
    `  RDP      ${p(s.rdp)}`,
    `  SSH      ${p(s.ssh)}`,
  ].join('\n');
}

// ------------------------------------------------------------- cooldown

function onCooldown(key) {
  const cd = readJson(COOLDOWN_FILE, {});
  if (!cd[key]) return false;
  if (Date.now() - cd[key] < COOLDOWN_MS) return true;
  delete cd[key];
  writeJson(COOLDOWN_FILE, cd);
  return false;
}

function setCooldown(key) {
  const cd = readJson(COOLDOWN_FILE, {});
  cd[key] = Date.now();
  writeJson(COOLDOWN_FILE, cd);
}

// ------------------------------------------------------------------ run

const current = collect();

if (SHOW_ONLY) {
  console.log('Current readings:\n' + render(current));
  process.exit(0);
}

const baseline = readJson(BASELINE_FILE, null);

// Baseline is never created implicitly. Approving an insecure state as "normal"
// would blind every future comparison, so it stays an explicit human act.
if (!baseline) {
  if (!APPROVE) {
    console.log('No baseline found. Current readings:\n');
    console.log(render(current));
    console.log('\nIf these values are correct, approve them as the baseline:');
    console.log('  node security-watch.js --approve-baseline\n');
    process.exit(1);
  }
  writeJson(BASELINE_FILE, { ...current, approved_at: new Date().toISOString() });
  writeJson(STATE_FILE, current);
  console.log('Baseline approved:\n' + render(current));
  console.log(`\nWrote ${path.basename(BASELINE_FILE)}, ${path.basename(STATE_FILE)}`);
  process.exit(0);
}

if (APPROVE) {
  writeJson(BASELINE_FILE, { ...current, approved_at: new Date().toISOString() });
  console.log('Baseline re-approved:\n' + render(current));
}

writeJson(STATE_FILE, current);

// Five comparison rules, unchanged in meaning. A rule fires only on a real
// transition away from the approved value — never on an unknown reading.
const rules = [
  {
    key: 'DNS_CHANGE',
    fires: current.dns && baseline.dns && current.dns !== baseline.dns,
    severity: 'CRITICAL',
    control: 'dns',
    description: 'DNS resolvers changed since baseline',
  },
  {
    key: 'FIREWALL_DISABLED',
    fires: current.fw === false && baseline.fw === true,
    severity: 'CRITICAL',
    control: 'firewall',
    description: 'Windows Firewall was turned off',
  },
  {
    key: 'DEFENDER_DISABLED',
    fires: current.def === false && baseline.def === true,
    severity: 'CRITICAL',
    control: 'defender',
    description: 'Real-time protection was turned off',
  },
  {
    key: 'RDP_ENABLED',
    fires: current.rdp === true && baseline.rdp === false,
    severity: 'CRITICAL',
    control: 'rdp',
    description: 'Remote Desktop started listening',
  },
  {
    key: 'SSH_ENABLED',
    fires: current.ssh === true && baseline.ssh === false,
    severity: 'CRITICAL',
    control: 'ssh',
    description: 'SSH started listening',
  },
];

const history = readJson(ALERTS_FILE, { schema_version: '1.0', alerts: [] });
const fired = [];
const suppressed = [];

for (const r of rules) {
  if (!r.fires) continue;
  if (onCooldown(r.key)) { suppressed.push(r.key); continue; }

  fired.push({
    type: r.key,
    severity: r.severity,
    control: r.control,
    description: r.description,
    baseline_value: baseline[r.control],
    current_value: current[r.control],
    detected_at: current.collected_at,
  });
  setCooldown(r.key);
}

history.alerts = [...fired, ...history.alerts].slice(0, MAX_ALERTS);
history.updated_at = current.collected_at;
history.open_alert_count = fired.length;
writeJson(ALERTS_FILE, history);

console.log(render(current));
console.log(`\nWrote ${['state.json', 'alerts.json'].join(', ')}`);

if (fired.length) {
  console.log(`\n${fired.length} NEW ALERT(S):`);
  for (const a of fired) console.log(`  ${a.severity}  ${a.type} — ${a.description}`);
} else {
  console.log('\nNo change from baseline.');
}
if (suppressed.length) console.log(`Suppressed (4h cooldown): ${suppressed.join(', ')}`);
