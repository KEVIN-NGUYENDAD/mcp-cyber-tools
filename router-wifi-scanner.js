#!/usr/bin/env node
/**
 * ROUTER/WiFi - HOME SOC Scanner
 * Quét Router & WiFi mỗi 30 phút khi Router active
 * Push lên GitHub tự động
 */

import fs from 'fs';
import { execSync } from 'child_process';
import path from 'path';
import net from 'net';

const projectDir = path.join(process.env.APPDATA, 'Claude', 'Projects', 'mcp-cyber-tools');

const CONFIG = {
  collectionInterval: 30 * 60 * 1000,
  dataDir: path.join(projectDir, 'router-wifi-data'),
  routerIP: '192.168.0.1',
  deviceName: 'ROUTER',
  projectDir: projectDir,
  ports: [80, 443, 554, 8000, 8080, 8554, 9000, 22, 23, 445, 1883, 5000]
};

if (!fs.existsSync(CONFIG.dataDir)) {
  fs.mkdirSync(CONFIG.dataDir, { recursive: true });
}

console.log(`📁 Project Directory: ${CONFIG.projectDir}`);
console.log(`📂 Data Directory: ${CONFIG.dataDir}\n`);

const collectionLog = {
  device: CONFIG.deviceName,
  startTime: new Date().toISOString(),
  collections: [],
  status: 'RUNNING'
};

console.log('🔐 HOME SOC - ROUTER/WiFi SCANNER');
console.log(`⏰ Started: ${new Date().toLocaleTimeString()}`);
console.log(`🔄 Scanning every 30 minutes when Router is active`);
console.log(`📁 Data directory: ${CONFIG.dataDir}\n`);

/**
 * Check if router is reachable
 */
function isRouterActive() {
  try {
    execSync(`ping -n 1 ${CONFIG.routerIP}`, { stdio: 'pipe', timeout: 3000 });
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Get ARP table
 */
function getARPTable() {
  try {
    const arpOutput = execSync('arp -a', { encoding: 'utf-8', shell: 'cmd', timeout: 5000 });
    const devices = [];
    const lines = arpOutput.split('\n');

    lines.forEach(line => {
      const match = line.match(/(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f:-]+)/i);
      if (match) {
        devices.push({
          ip: match[1],
          mac: match[2].toUpperCase()
        });
      }
    });

    return devices;
  } catch (e) {
    return [];
  }
}

/**
 * Probe port
 */
function probePort(host, port, timeout = 2000) {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    const timer = setTimeout(() => {
      socket.destroy();
      resolve(false);
    }, timeout);

    socket.connect(port, host, () => {
      clearTimeout(timer);
      socket.destroy();
      resolve(true);
    });

    socket.on('error', () => {
      clearTimeout(timer);
      resolve(false);
    });
  });
}

/**
 * Scan network devices
 */
async function scanNetwork(iterationNum) {
  const timestamp = new Date().toISOString();
  console.log(`\n📊 [Scan #${iterationNum}] ${new Date().toLocaleTimeString()}`);

  // Check if router is active
  console.log('  • Checking Router connection...');
  if (!isRouterActive()) {
    console.log('  ⚠️  Router not active - using last scan result');
    return false;
  }

  console.log('  ✅ Router is active');

  const snapshot = {
    timestamp,
    device: CONFIG.deviceName,
    iteration: iterationNum,
    data: {
      devices: [],
      risks: []
    }
  };

  // Get ARP table
  console.log('  • Scanning ARP table...');
  const devices = getARPTable();
  console.log(`    Found ${devices.length} devices`);

  // Probe each device
  for (const device of devices) {
    if (device.ip === CONFIG.routerIP) continue;

    console.log(`  • Probing ${device.ip}...`);
    const deviceInfo = {
      ip: device.ip,
      mac: device.mac,
      openPorts: []
    };

    for (const port of CONFIG.ports) {
      const isOpen = await probePort(device.ip, port);
      if (isOpen) {
        deviceInfo.openPorts.push(port);
      }
    }

    snapshot.data.devices.push(deviceInfo);

    // Check for risky ports
    if (deviceInfo.openPorts.includes(23)) {
      snapshot.data.risks.push({
        ip: device.ip,
        port: 23,
        severity: 'CRITICAL',
        service: 'Telnet (unencrypted)',
        recommendation: 'Disable immediately'
      });
    }
  }

  snapshot.data.summary = {
    devicesFound: devices.length,
    risksFound: snapshot.data.risks.length,
    timestamp: timestamp
  };

  collectionLog.collections.push({
    iteration: iterationNum,
    timestamp,
    status: 'OK',
    devicesFound: devices.length
  });

  // Save snapshot
  const snapshotFile = path.join(CONFIG.dataDir, `scan-${iterationNum}.json`);
  fs.writeFileSync(snapshotFile, JSON.stringify(snapshot, null, 2));

  // Save latest for 8PM bulletin
  fs.writeFileSync(path.join(CONFIG.dataDir, 'LATEST.json'), JSON.stringify(snapshot, null, 2));

  console.log(`  ✅ Saved to ${path.basename(snapshotFile)}`);
  return true;
}

/**
 * Auto-push to GitHub
 */
function autoPushToGitHub() {
  try {
    console.log('  📤 Pushing to GitHub...');
    execSync('git add router-wifi-data/', { cwd: CONFIG.projectDir, stdio: 'pipe' });
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    execSync(`git commit -m "data: Router/WiFi scan - ${timestamp}"`, {
      cwd: CONFIG.projectDir,
      stdio: 'pipe'
    });
    execSync('git push origin learning-factory-v2', {
      cwd: CONFIG.projectDir,
      stdio: 'pipe'
    });
    console.log('  ✅ Pushed to GitHub');
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Main scanning loop
 */
async function main() {
  let iteration = 1;

  // First scan
  await scanNetwork(iteration++);
  autoPushToGitHub();

  // Scheduled scans every 30 minutes
  const interval = setInterval(async () => {
    await scanNetwork(iteration++);
    autoPushToGitHub();
  }, CONFIG.collectionInterval);

  // Graceful shutdown
  process.on('SIGINT', () => {
    console.log('\n\n⏹️  Stopping scanner...');
    clearInterval(interval);

    collectionLog.status = 'STOPPED';
    collectionLog.endTime = new Date().toISOString();

    const logFilePath = path.join(CONFIG.projectDir, 'router-wifi-scan-log.json');
    fs.writeFileSync(logFilePath, JSON.stringify(collectionLog, null, 2));

    console.log('\n✅ Scanner stopped');
    console.log(`📊 Scans: ${collectionLog.collections.length}`);
    console.log(`📁 Data: ${CONFIG.dataDir}`);

    process.exit(0);
  });
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
