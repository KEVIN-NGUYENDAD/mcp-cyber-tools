#!/usr/bin/env node
/**
 * LAPTOP/DESKTOP - HOME SOC Auto-Collector
 * Thu thập dữ liệu mỗi 30 phút khi máy hoạt động
 * Push lên GitHub tự động
 */

import fs from 'fs';
import { execSync } from 'child_process';
import path from 'path';
import os from 'os';

const projectDir = path.join(process.env.APPDATA, 'Claude', 'Projects', 'mcp-cyber-tools');

const CONFIG = {
  collectionInterval: 30 * 60 * 1000,
  dataDir: path.join(projectDir, 'laptop-collection-data'),
  deviceName: os.hostname(),
  reportFile: path.join(projectDir, 'LAPTOP-AUTO-COLLECTION-REPORT.md'),
  projectDir: projectDir
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

console.log('💻 HOME SOC - LAPTOP/DESKTOP AUTO COLLECTOR');
console.log(`⏰ Started: ${new Date().toLocaleTimeString()}`);
console.log(`🔄 Collecting every 30 minutes while running`);
console.log(`📁 Data directory: ${CONFIG.dataDir}\n`);

/**
 * Collect device metrics
 */
function collectData(iterationNum) {
  const timestamp = new Date().toISOString();
  console.log(`\n📊 [Collection #${iterationNum}] ${new Date().toLocaleTimeString()}`);

  const snapshot = {
    timestamp,
    device: CONFIG.deviceName,
    iteration: iterationNum,
    data: {}
  };

  try {
    // 1. Process snapshot
    console.log('  • Capturing processes...');
    try {
      const psOutput = execSync('Get-Process | Select-Object Name, ID, WorkingSet | ConvertTo-Json',
        { encoding: 'utf-8', shell: 'powershell', timeout: 5000 });
      snapshot.data.processes = JSON.parse(psOutput).slice(0, 20);
    } catch (e) {
      console.log('    ⚠️  Process capture failed');
    }

    // 2. Network connections
    console.log('  • Capturing network...');
    try {
      const netOutput = execSync('Get-NetTCPConnection -State Established | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort | ConvertTo-Json',
        { encoding: 'utf-8', shell: 'powershell', timeout: 5000 });
      snapshot.data.connections = JSON.parse(netOutput).slice(0, 15);
    } catch (e) {
      console.log('    ⚠️  Network capture failed');
    }

    // 3. Battery status
    console.log('  • Capturing battery status...');
    try {
      const batOutput = execSync('Get-CimInstance Win32_Battery | Select-Object EstimatedChargeRemaining, Status | ConvertTo-Json',
        { encoding: 'utf-8', shell: 'powershell', timeout: 5000 });
      snapshot.data.battery = JSON.parse(batOutput);
    } catch (e) {
      snapshot.data.battery = { note: 'No battery info (desktop)' };
    }

    // 4. IPv4 Address
    console.log('  • Capturing IPv4 address...');
    try {
      const ipOutput = execSync('Get-NetIPAddress -AddressFamily IPv4 -PrefixLength 24 | Select-Object IPAddress, InterfaceAlias | ConvertTo-Json',
        { encoding: 'utf-8', shell: 'powershell', timeout: 5000 });
      const ips = JSON.parse(ipOutput);
      snapshot.data.ipv4 = Array.isArray(ips) ? ips : [ips];
    } catch (e) {
      console.log('    ⚠️  IPv4 capture failed');
    }

    // 5. WiFi SSID
    console.log('  • Capturing WiFi SSID...');
    try {
      const wifiOutput = execSync('netsh wlan show interfaces',
        { encoding: 'utf-8', shell: 'cmd', timeout: 5000 });

      const wifiData = {};
      const lines = wifiOutput.split(/[\r\n]+/).filter(l => l.trim());

      lines.forEach(line => {
        const trimmed = line.trim();
        if (trimmed.toLowerCase().includes('ssid') && trimmed.includes(':')) {
          const parts = trimmed.split(':');
          if (parts.length === 2) {
            const value = parts[1].trim();
            if (value && !value.toLowerCase().includes('ssid')) {
              wifiData.ssid = value || 'Hidden/None';
            }
          }
        }
        if (trimmed.toLowerCase().startsWith('state') && trimmed.includes(':')) {
          const parts = trimmed.split(':');
          if (parts.length === 2) {
            wifiData.state = parts[1].trim() || 'Unknown';
          }
        }
      });

      snapshot.data.wifiStatus = wifiData.ssid ? wifiData : { note: 'No WiFi connected' };
    } catch (e) {
      console.log('    ⚠️  WiFi SSID capture failed');
      snapshot.data.wifiStatus = { note: 'WiFi check failed' };
    }

    // 6. DNS Servers
    console.log('  • Capturing DNS servers...');
    try {
      const dnsOutput = execSync('Get-DnsClientServerAddress -AddressFamily IPv4 | Select-Object ServerAddresses, InterfaceAlias | ConvertTo-Json',
        { encoding: 'utf-8', shell: 'powershell', timeout: 5000 });
      snapshot.data.dns = JSON.parse(dnsOutput);
    } catch (e) {
      console.log('    ⚠️  DNS capture failed');
    }

    // 7. System memory
    console.log('  • Capturing system metrics...');
    try {
      const memOutput = execSync('Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory | ConvertTo-Json',
        { encoding: 'utf-8', shell: 'powershell', timeout: 5000 });
      const mem = JSON.parse(memOutput);
      snapshot.data.memory = {
        total: mem.TotalVisibleMemorySize,
        free: mem.FreePhysicalMemory,
        usagePercent: Math.round(((mem.TotalVisibleMemorySize - mem.FreePhysicalMemory) / mem.TotalVisibleMemorySize) * 100)
      };
    } catch (e) {
      console.log('    ⚠️  System metrics failed');
    }

    // Save snapshot
    const snapshotFile = path.join(CONFIG.dataDir, `snapshot-${iterationNum}.json`);
    fs.writeFileSync(snapshotFile, JSON.stringify(snapshot, null, 2));

    collectionLog.collections.push({
      iteration: iterationNum,
      timestamp,
      file: snapshotFile,
      status: 'OK'
    });

    // Save latest snapshot for 8PM bulletin
    fs.writeFileSync(path.join(CONFIG.dataDir, 'LATEST.json'), JSON.stringify(snapshot, null, 2));

    console.log(`  ✅ Saved to ${path.basename(snapshotFile)}`);
    return true;
  } catch (error) {
    console.log(`  ❌ Collection failed: ${error.message}`);
    collectionLog.collections.push({
      iteration: iterationNum,
      timestamp,
      status: 'FAILED',
      error: error.message
    });
    return false;
  }
}

/**
 * Auto-push to GitHub
 */
function autoPushToGitHub() {
  try {
    console.log('  📤 Pushing to GitHub...');
    execSync('git add laptop-collection-data/', { cwd: CONFIG.projectDir, stdio: 'pipe' });
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    execSync(`git commit -m "data: Laptop collection - ${timestamp}"`, {
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
 * Main collection loop
 */
async function main() {
  let iteration = 1;

  // First collection
  collectData(iteration++);
  autoPushToGitHub();

  // Scheduled collections every 30 minutes
  const interval = setInterval(() => {
    collectData(iteration++);
    autoPushToGitHub();
  }, CONFIG.collectionInterval);

  // Graceful shutdown
  process.on('SIGINT', () => {
    console.log('\n\n⏹️  Stopping collection...');
    clearInterval(interval);

    collectionLog.status = 'STOPPED';
    collectionLog.endTime = new Date().toISOString();

    const logFilePath = path.join(CONFIG.projectDir, 'laptop-collection-log.json');
    fs.writeFileSync(logFilePath, JSON.stringify(collectionLog, null, 2));

    console.log('\n✅ Collection stopped');
    console.log(`📊 Collected: ${collectionLog.collections.length} snapshots`);
    console.log(`📁 Data: ${CONFIG.dataDir}`);

    process.exit(0);
  });
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
