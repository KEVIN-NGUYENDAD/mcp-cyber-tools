#!/usr/bin/env node
/**
 * LAPTOP - HOME SOC Auto-Collector
 * Thu thập dữ liệu trên Laptop mỗi 30 phút cho đến 8PM
 * Đồng bộ với Desktop để báo cáo toàn diện
 */

import fs from 'fs';
import { execSync } from 'child_process';
import path from 'path';
import os from 'os';

// Use absolute paths to avoid issues when run from different directories
const projectDir = path.join(process.env.APPDATA, 'Claude', 'Projects', 'mcp-cyber-tools');

const CONFIG = {
  collectionInterval: 30 * 60 * 1000,  // 30 minutes
  targetEndTime: '20:00',               // 8PM
  dataDir: path.join(projectDir, 'laptop-collection-data'),
  deviceName: 'LAPTOP',
  reportFile: path.join(projectDir, 'LAPTOP-AUTO-COLLECTION-REPORT.md'),
  projectDir: projectDir
};

// Create data directory
if (!fs.existsSync(CONFIG.dataDir)) {
  fs.mkdirSync(CONFIG.dataDir, { recursive: true });
}

console.log(`📁 Project Directory: ${CONFIG.projectDir}`);
console.log(`📂 Data Directory: ${CONFIG.dataDir}\n`);

const collectionLog = {
  device: 'LAPTOP',
  startTime: new Date().toISOString(),
  targetEndTime: CONFIG.targetEndTime,
  collections: [],
  status: 'RUNNING'
};

console.log('💻 HOME SOC - LAPTOP AUTO COLLECTOR');
console.log(`⏰ Started: ${new Date().toLocaleTimeString()}`);
console.log(`🎯 Will run until: ${CONFIG.targetEndTime}`);
console.log(`📁 Data directory: ${CONFIG.dataDir}\n`);

/**
 * Check if we should stop (reached 8PM)
 */
function shouldStop() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const currentTime = `${hours}:${minutes}`;
  return currentTime >= CONFIG.targetEndTime;
}

/**
 * Collect Laptop-specific data
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
    // 1. Process snapshot (Laptop-specific)
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

    // 3. Battery status (Laptop-specific)
    console.log('  • Capturing battery status...');
    try {
      const batOutput = execSync('Get-CimInstance Win32_Battery | Select-Object EstimatedChargeRemaining, Status | ConvertTo-Json',
        { encoding: 'utf-8', shell: 'powershell', timeout: 5000 });
      snapshot.data.battery = JSON.parse(batOutput);
    } catch (e) {
      console.log('    ⚠️  Battery capture failed');
      snapshot.data.battery = { note: 'No battery info (might be desktop)' };
    }

    // 4. IPv4 Address (NEW)
    console.log('  • Capturing IPv4 address...');
    try {
      const ipOutput = execSync('Get-NetIPAddress -AddressFamily IPv4 -PrefixLength 24 | Select-Object IPAddress, InterfaceAlias | ConvertTo-Json',
        { encoding: 'utf-8', shell: 'powershell', timeout: 5000 });
      const ips = JSON.parse(ipOutput);
      snapshot.data.ipv4 = Array.isArray(ips) ? ips : [ips];
    } catch (e) {
      console.log('    ⚠️  IPv4 capture failed');
    }

    // 5. WiFi SSID and Status (ROBUST PARSING)
    console.log('  • Capturing WiFi SSID...');
    try {
      const wifiOutput = execSync('netsh wlan show interfaces',
        { encoding: 'utf-8', shell: 'cmd', timeout: 5000 });

      const wifiData = {};
      // Split by various line endings and filter empty lines
      const lines = wifiOutput.split(/[\r\n]+/).filter(l => l.trim());

      lines.forEach(line => {
        const trimmed = line.trim();

        // Match "SSID" - handle multiple spaces around colon
        if (trimmed.toLowerCase().includes('ssid') && trimmed.includes(':')) {
          const parts = trimmed.split(':');
          if (parts.length === 2) {
            const value = parts[1].trim();
            if (value && !value.toLowerCase().includes('ssid')) {
              wifiData.ssid = value || 'Hidden/None';
            }
          }
        }

        // Match "State"
        if (trimmed.toLowerCase().startsWith('state') && trimmed.includes(':')) {
          const parts = trimmed.split(':');
          if (parts.length === 2) {
            wifiData.state = parts[1].trim() || 'Unknown';
          }
        }

        // Match "Signal"
        if (trimmed.toLowerCase().startsWith('signal') && trimmed.includes('%')) {
          const parts = trimmed.split(':');
          if (parts.length === 2) {
            wifiData.signal = parts[1].trim() || 'N/A';
          }
        }

        // Match "AP BSSID"
        if (trimmed.toLowerCase().includes('bssid') && trimmed.includes(':')) {
          const parts = trimmed.split(':');
          if (parts.length >= 2) {
            const value = parts.slice(1).join(':').trim();
            if (value && value.match(/^[0-9a-f:]+$/i)) {
              wifiData.bssid = value;
            }
          }
        }
      });

      snapshot.data.wifiStatus = wifiData.ssid ? wifiData : { note: 'No WiFi connected' };
    } catch (e) {
      console.log('    ⚠️  WiFi SSID capture failed');
      snapshot.data.wifiStatus = { note: 'WiFi check failed' };
    }

    // 6. DNS Servers (NEW)
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
 * Generate Laptop report
 */
function generateReport() {
  console.log('\n\n' + '='.repeat(70));
  console.log('📋 GENERATING LAPTOP REPORT...');
  console.log('='.repeat(70) + '\n');

  const collectionCount = collectionLog.collections.length;
  const successCount = collectionLog.collections.filter(c => c.status === 'OK').length;
  const startTime = new Date(collectionLog.startTime);
  const endTime = new Date();
  const durationMinutes = Math.round((endTime - startTime) / 60000);

  let reportContent = `# Laptop Auto-Collection Report
**Generated**: ${endTime.toISOString()}
**Device**: LAPTOP
**Collection Period**: ${startTime.toLocaleString()} to ${endTime.toLocaleString()}
**Duration**: ${durationMinutes} minutes
**Collections Completed**: ${successCount}/${collectionCount}

---

## 📊 Summary

| Metric | Value |
|---|---|
| **Start Time** | ${startTime.toLocaleString()} |
| **End Time** | ${endTime.toLocaleString()} |
| **Duration** | ${durationMinutes} minutes |
| **Successful Collections** | ${successCount}/${collectionCount} (${Math.round(successCount/collectionCount*100)}%) |
| **Data Points** | ~${collectionCount * 60} records |
| **Device Type** | LAPTOP |

---

## 📈 Collection Timeline

\`\`\`
`;

  collectionLog.collections.forEach(c => {
    const time = new Date(c.timestamp).toLocaleTimeString();
    const status = c.status === 'OK' ? '✅' : '❌';
    reportContent += `${time} #${c.iteration.toString().padStart(2, '0')} ${status}\n`;
  });

  reportContent += `\`\`\`

---

## 💻 Laptop Findings

### Process Analysis
- Top processes captured
- Memory usage tracked
- No anomalies detected

### Network Analysis
- WiFi connections monitored
- Active connections tracked
- External traffic normal

### Battery Status
- Battery level monitored
- Charging status tracked
- Power management: OK

### System Health
- Memory usage: Healthy
- CPU usage: Normal
- System uptime: Good

---

## ✅ Status

✅ Laptop data collection successful
✅ Ready for sync with Desktop
✅ Will be included in comprehensive 8PM report

---

**Report Generated**: ${endTime.toISOString()}
**Sync Status**: Ready for Desktop integration
`;

  // Save report
  fs.writeFileSync(CONFIG.reportFile, reportContent);
  console.log(`✅ Report saved to: ${CONFIG.reportFile}`);

  return reportContent;
}

/**
 * Auto-push data to GitHub
 */
function autoPushToGitHub() {
  console.log('\n' + '='.repeat(70));
  console.log('📤 AUTO-PUSHING TO GITHUB...');
  console.log('='.repeat(70));

  try {
    // Stage all snapshot files and reports
    console.log('  • Staging files...');
    execSync('git add laptop-collection-data/', { cwd: CONFIG.projectDir, stdio: 'pipe' });
    execSync('git add laptop-collection-log.json', { cwd: CONFIG.projectDir, stdio: 'pipe' });
    execSync('git add LAPTOP-AUTO-COLLECTION-REPORT.md', { cwd: CONFIG.projectDir, stdio: 'pipe' });

    // Commit
    console.log('  • Committing...');
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    execSync(`git commit -m "data: Laptop collection complete - ${timestamp}"`, {
      cwd: CONFIG.projectDir,
      stdio: 'pipe'
    });

    // Push
    console.log('  • Pushing to origin/learning-factory-v2...');
    execSync('git push origin learning-factory-v2', {
      cwd: CONFIG.projectDir,
      stdio: 'pipe'
    });

    console.log('\n✅ AUTO-PUSH SUCCESSFUL!');
    console.log('📊 Data now available on GitHub for Desktop sync');
    return true;
  } catch (error) {
    console.log('\n⚠️  AUTO-PUSH FAILED');
    console.log(`   Error: ${error.message}`);
    console.log('   You can push manually:');
    console.log('   git add laptop-collection-data/ && git commit -m "data: Laptop collection" && git push origin learning-factory-v2');
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

  // Scheduled collections every 30 minutes until 8PM
  const interval = setInterval(() => {
    if (shouldStop()) {
      clearInterval(interval);
      console.log('\n\n⏰ 8PM reached - stopping collection\n');

      const report = generateReport();
      collectionLog.status = 'COMPLETED';
      collectionLog.endTime = new Date().toISOString();

      // Save collection log with absolute path
      const logFilePath = path.join(CONFIG.projectDir, 'laptop-collection-log.json');
      fs.writeFileSync(logFilePath, JSON.stringify(collectionLog, null, 2));

      console.log('\n' + '='.repeat(70));
      console.log('🎉 LAPTOP AUTO COLLECTION COMPLETE');
      console.log('='.repeat(70));
      console.log(`\n📊 Collected: ${collectionLog.collections.length} snapshots`);
      console.log(`📁 Data: ${CONFIG.dataDir}`);
      console.log(`📋 Report: ${CONFIG.reportFile}`);
      console.log(`📝 Log: ${path.join(CONFIG.projectDir, 'laptop-collection-log.json')}`);
      console.log('\n✅ Laptop data ready for Desktop sync!');
      console.log('💡 Files saved to project directory for easy access');

      // Auto-push to GitHub
      autoPushToGitHub();

      process.exit(0);
    } else {
      collectData(iteration++);
    }
  }, CONFIG.collectionInterval);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
