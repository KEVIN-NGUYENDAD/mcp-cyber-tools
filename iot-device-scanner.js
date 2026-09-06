#!/usr/bin/env node
/**
 * IoT / Camera / Router Device Scanner for HOME SOC
 * Discovers devices on the local network and classifies them by MAC vendor
 * and by which service ports respond.
 */

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

const projectDir = path.join(process.env.APPDATA, 'Claude', 'Projects', 'mcp-cyber-tools');

const CONFIG = {
  dataDir: path.join(projectDir, 'network-scan-data'),
  projectDir,
  portTimeoutMs: 400
};

if (!fs.existsSync(CONFIG.dataDir)) {
  fs.mkdirSync(CONFIG.dataDir, { recursive: true });
}

// MAC OUI prefix -> vendor / device type.
const OUI_MAP = {
  '48-bd-ce': { vendor: 'ARRIS / CommScope', type: 'Router / Gateway' },
  'ec-71-db': { vendor: 'Reolink', type: 'IP Camera' },
  '1c-bf-ce': { vendor: 'Shenzhen Ecom', type: 'IoT Device' },
  '1c-d6-be': { vendor: 'Amazon Technologies', type: 'Smart Speaker / IoT' },
  '9c-b1-50': { vendor: 'Intel', type: 'Computer (Laptop/Desktop)' },
  '00-17-88': { vendor: 'Philips Hue', type: 'Smart Lighting' },
  'b8-27-eb': { vendor: 'Raspberry Pi', type: 'Single-board Computer' },
  'dc-a6-32': { vendor: 'Raspberry Pi', type: 'Single-board Computer' },
  '00-1a-11': { vendor: 'Google', type: 'Chromecast / Nest' },
  'f4-f5-d8': { vendor: 'Google', type: 'Chromecast / Nest' },
  '18-b4-30': { vendor: 'Nest Labs', type: 'Thermostat / Camera' },
  '54-2a-1b': { vendor: 'TP-Link', type: 'Router / Smart Plug' },
  'a4-cf-12': { vendor: 'Espressif (ESP32)', type: 'DIY IoT Device' },
  // Apple devices (private/randomized MACs)
  '3a-45-17': { vendor: 'Apple', type: 'iPhone / iPad (Private MAC)' },
  '1e-37-1e': { vendor: 'Apple', type: 'iPhone / iPad (Private MAC)' },
  '20-91-df': { vendor: 'Apple', type: 'iPhone / iPad (Private MAC)' },
  '9e-53-d4': { vendor: 'Apple', type: 'iPhone / iPad (Private MAC)' },
  // Samsung devices
  '70-3a-95': { vendor: 'Samsung Electronics', type: 'Smartphone / Tablet' },
  'c0-bd-d9': { vendor: 'Samsung Electronics', type: 'Smartphone / Tablet' },
  '88-ae-dd': { vendor: 'Samsung Electronics', type: 'Smart TV / Device' },
  '34-e6-d7': { vendor: 'Samsung', type: 'Device' }
};

// Ports that reveal what a device actually is.
const PROBE_PORTS = [
  { port: 80,   service: 'HTTP (Web UI)' },
  { port: 443,  service: 'HTTPS (Web UI)' },
  { port: 554,  service: 'RTSP (Camera Stream)' },
  { port: 8000, service: 'HTTP Alt (Camera/NVR)' },
  { port: 8080, service: 'HTTP Alt (Admin)' },
  { port: 8554, service: 'RTSP Alt (Camera)' },
  { port: 9000, service: 'Reolink / NVR' },
  { port: 22,   service: 'SSH' },
  { port: 23,   service: 'Telnet' },
  { port: 445,  service: 'SMB File Share' },
  { port: 1883, service: 'MQTT (IoT Broker)' },
  { port: 5000, service: 'UPnP / Media' }
];

// Ports that should never be open on a home IoT device.
const RISKY_PORTS = {
  23: 'CRITICAL - Telnet sends credentials in plaintext',
  445: 'HIGH - SMB file sharing exposed',
  22: 'MEDIUM - SSH open, verify it is intentional',
  1883: 'MEDIUM - MQTT broker without TLS'
};

/**
 * Read the ARP table and return real LAN hosts.
 * Broadcast (ff-ff-...) and multicast (01-00-5e-...) entries are dropped.
 */
function discoverDevices() {
  const output = execSync('arp -a', { encoding: 'utf-8', timeout: 5000 });
  const devices = [];

  output.split('\n').forEach(line => {
    const match = line.match(/\s+([\d.]+)\s+([\da-f]{2}(?:-[\da-f]{2}){5})\s+(\w+)/i);
    if (!match) return;

    const [, ip, mac, type] = match;
    const macLower = mac.toLowerCase();

    if (macLower.startsWith('ff-ff') || macLower.startsWith('01-00-5e')) return;
    if (ip.endsWith('.255')) return;

    const oui = macLower.slice(0, 8);
    const known = OUI_MAP[oui];

    devices.push({
      ip,
      mac: macLower,
      arpType: type,
      vendor: known ? known.vendor : 'Unknown',
      deviceType: known ? known.type : 'Unidentified',
      identified: Boolean(known)
    });
  });

  return devices;
}

/**
 * Probe one TCP port using PowerShell's TcpClient with a short timeout.
 */
function isPortOpen(ip, port) {
  const ps = `$c=New-Object Net.Sockets.TcpClient;` +
    `$r=$c.BeginConnect('${ip}',${port},$null,$null);` +
    `$ok=$r.AsyncWaitHandle.WaitOne(${CONFIG.portTimeoutMs});` +
    `if($ok -and $c.Connected){'OPEN'}else{'CLOSED'};$c.Close()`;

  try {
    const out = execSync(`powershell -NoProfile -Command "${ps}"`, {
      encoding: 'utf-8',
      timeout: CONFIG.portTimeoutMs + 3000,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    return out.includes('OPEN');
  } catch (e) {
    return false;
  }
}

/**
 * Grab a service banner so the reported service is evidence, not a guess.
 * A port number only says what a service is *conventionally* on — several
 * IoT devices listen on 80 without speaking HTTP at all.
 */
function grabBanner(ip, port) {
  // Build the probe line in PowerShell itself. Escaping CRLF through
  // Node -> cmd -> PowerShell quoting is unreliable, so the script is
  // written to a temp .ps1 and run as a file instead.
  const rtspPorts = [554, 8554];
  const httpPorts = [80, 8080, 8000, 9000];

  let payloadExpr = null;
  if (rtspPorts.includes(port)) {
    payloadExpr = `'OPTIONS rtsp://${ip}:${port} RTSP/1.0' + $CRLF + 'CSeq: 1' + $CRLF + $CRLF`;
  } else if (httpPorts.includes(port)) {
    payloadExpr = `'HEAD / HTTP/1.0' + $CRLF + 'Host: ${ip}' + $CRLF + $CRLF`;
  }

  const script = [
    `$CRLF = [char]13 + [char]10`,
    `$c = New-Object Net.Sockets.TcpClient`,
    `$c.ReceiveTimeout = 3000`,
    `$c.SendTimeout = 3000`,
    `try {`,
    `  $c.Connect('${ip}', ${port})`,
    `  $s = $c.GetStream()`,
    payloadExpr
      ? `  $req = ${payloadExpr}
  $b = [Text.Encoding]::ASCII.GetBytes($req)
  $s.Write($b, 0, $b.Length)
  $s.Flush()`
      : '',
    `  Start-Sleep -Milliseconds 1200`,
    `  $buf = New-Object byte[] 512`,
    `  if ($s.DataAvailable) {`,
    `    $n = $s.Read($buf, 0, 512)`,
    `    [Text.Encoding]::ASCII.GetString($buf, 0, $n) -replace '[^\\x20-\\x7E]', '.'`,
    `  } else { '<silent>' }`,
    `  $c.Close()`,
    `} catch { '<error>' }`
  ].filter(Boolean).join('\n');

  const tmpFile = path.join(CONFIG.dataDir, `.probe-${port}.ps1`);

  try {
    fs.writeFileSync(tmpFile, script);
    const out = execSync(
      `powershell -NoProfile -ExecutionPolicy Bypass -File "${tmpFile}"`,
      { encoding: 'utf-8', timeout: 15000, stdio: ['pipe', 'pipe', 'pipe'] }
    ).trim();
    return out || '<silent>';
  } catch (e) {
    return '<error>';
  } finally {
    try { fs.unlinkSync(tmpFile); } catch (e) { /* already gone */ }
  }
}

/**
 * Classify a service from its actual banner. Falls back to "unverified"
 * rather than asserting the conventional service for the port number.
 */
function identifyService(port, banner, assumedService) {
  if (banner === '<silent>') return `Open, no banner (service unverified, NOT ${assumedService.split(' ')[0]})`;
  if (banner === '<error>') return 'Open, probe failed';

  if (/^RTSP\/1\.0/.test(banner)) {
    const server = banner.match(/Server:\s*([^\r\n.]+)/i);
    return `RTSP video stream${server ? ` — ${server[1].trim()}` : ''} [CONFIRMED]`;
  }
  if (/login:|username:|password:/i.test(banner)) {
    return 'Telnet login prompt [CONFIRMED]';
  }
  if (/^HTTP\/1\.[01]/.test(banner)) {
    const server = banner.match(/Server:\s*([^\r\n]+)/i);
    return `HTTP server${server ? ` — ${server[1].trim()}` : ''} [CONFIRMED]`;
  }
  if (/^SSH-/.test(banner)) return `SSH — ${banner.split('\n')[0].trim()} [CONFIRMED]`;

  return `Open, unrecognized banner: "${banner.slice(0, 40)}"`;
}

/**
 * Scan a device's probe ports and flag risky ones.
 */
function scanDevice(device) {
  const openPorts = [];
  const risks = [];

  PROBE_PORTS.forEach(({ port, service }) => {
    if (!isPortOpen(device.ip, port)) return;

    const banner = grabBanner(device.ip, port);
    const verified = identifyService(port, banner, service);
    openPorts.push({ port, assumedService: service, verifiedService: verified });

    // Only raise a risk when the banner actually confirms the dangerous service.
    if (RISKY_PORTS[port] && !verified.includes('service unverified')) {
      risks.push({ port, service: verified, warning: RISKY_PORTS[port] });
    }
  });

  // A device serving a confirmed RTSP stream is a camera, whatever its OUI said.
  const hasRtsp = openPorts.some(p => p.verifiedService.startsWith('RTSP'));
  const refinedType = hasRtsp && !device.deviceType.includes('Camera')
    ? 'IP Camera (RTSP detected)'
    : device.deviceType;

  return { ...device, deviceType: refinedType, openPorts, risks };
}

function main() {
  const startedAt = new Date();

  console.log('\n' + '='.repeat(70));
  console.log('🔍 HOME SOC - IoT / CAMERA / ROUTER SCANNER');
  console.log('='.repeat(70));
  console.log(`⏰ Started: ${startedAt.toLocaleTimeString()}`);
  console.log(`📁 Data directory: ${CONFIG.dataDir}\n`);

  console.log('• Discovering devices on local network...');
  const devices = discoverDevices();
  console.log(`  ✅ Found ${devices.length} devices\n`);

  console.log('• Scanning service ports (this takes a moment)...\n');
  const scanned = devices.map((device, i) => {
    console.log(`  [${i + 1}/${devices.length}] ${device.ip} (${device.vendor})`);
    const result = scanDevice(device);
    console.log(`      ${result.openPorts.length} open port(s), ${result.risks.length} risk(s)`);
    return result;
  });

  const snapshot = {
    timestamp: startedAt.toISOString(),
    scanType: 'IOT_NETWORK_SCAN',
    deviceCount: scanned.length,
    identifiedCount: scanned.filter(d => d.identified).length,
    totalRisks: scanned.reduce((sum, d) => sum + d.risks.length, 0),
    devices: scanned
  };

  const outFile = path.join(CONFIG.dataDir, `network-scan-${Date.now()}.json`);
  fs.writeFileSync(outFile, JSON.stringify(snapshot, null, 2));

  // Report
  console.log('\n' + '='.repeat(70));
  console.log('📊 DEVICE INVENTORY');
  console.log('='.repeat(70) + '\n');

  scanned.forEach(d => {
    console.log(`${d.ip.padEnd(16)} ${d.deviceType}`);
    console.log(`${''.padEnd(16)} Vendor: ${d.vendor} | MAC: ${d.mac}`);
    if (d.openPorts.length) {
      d.openPorts.forEach(p => {
        console.log(`${''.padEnd(16)} Port ${String(p.port).padEnd(5)} ${p.verifiedService}`);
      });
    } else {
      console.log(`${''.padEnd(16)} Open: none detected`);
    }
    console.log('');
  });

  const allRisks = scanned.filter(d => d.risks.length);
  console.log('='.repeat(70));
  console.log('🔒 SECURITY FINDINGS');
  console.log('='.repeat(70) + '\n');

  if (allRisks.length === 0) {
    console.log('✅ No risky ports found on any device\n');
  } else {
    allRisks.forEach(d => {
      console.log(`⚠️  ${d.ip} (${d.deviceType})`);
      d.risks.forEach(r => console.log(`    Port ${r.port}: ${r.warning}`));
      console.log('');
    });
  }

  console.log('='.repeat(70));
  console.log(`📊 Devices: ${snapshot.deviceCount} | Identified: ${snapshot.identifiedCount} | Risks: ${snapshot.totalRisks}`);
  console.log(`💾 Saved: ${path.basename(outFile)}`);
  console.log('='.repeat(70) + '\n');
}

main();
