#!/usr/bin/env node
/**
 * Startup Router Scan - Runs at boot, saves, and pushes to GitHub
 * Triggered by Windows Task Scheduler at system startup
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const projectDir = path.join(process.env.APPDATA, 'Claude', 'Projects', 'mcp-cyber-tools');

console.log('🚀 HOME SOC Startup Scan - Starting...');
console.log(`⏰ Time: ${new Date().toLocaleString()}`);
console.log(`📁 Project: ${projectDir}\n`);

try {
  // Step 1: Run IoT scanner
  console.log('🔍 Step 1: Scanning network devices...');
  execSync('node iot-device-scanner.js', {
    cwd: projectDir,
    stdio: 'inherit',
    timeout: 300000
  });

  // Step 2: Extract iPhone data from scan
  console.log('\n📱 Step 2: Extracting iPhone metrics...');

  try {
    const scanDir = path.join(projectDir, 'network-scan-data');
    const scanFiles = fs.readdirSync(scanDir).filter(f => f.endsWith('.json')).sort().reverse();

    if (scanFiles.length > 0) {
      const latestScan = JSON.parse(fs.readFileSync(path.join(scanDir, scanFiles[0]), 'utf-8'));

      // Find iPhone/iOS devices (Apple vendor)
      const iphoneDevices = latestScan.devices.filter(d =>
        d.vendor && (d.vendor.includes('Apple') || d.deviceType.includes('iPhone') || d.deviceType.includes('iPad'))
      );

      if (iphoneDevices.length > 0) {
        iphoneDevices.forEach((device, idx) => {
          const iphoneData = {
            timestamp: new Date().toISOString(),
            device_name: device.ip,
            mac_address: device.mac,
            vendor: device.vendor,
            device_type: device.deviceType,
            ip_address: device.ip,
            arp_type: device.arpType,
            identified: device.identified,
            open_ports: device.openPorts.length,
            security_risks: device.risks.length,
            source: 'automatic network scan'
          };

          const iphoneDir = path.join(projectDir, 'iphone-data');
          if (!fs.existsSync(iphoneDir)) fs.mkdirSync(iphoneDir, { recursive: true });

          const date = new Date().toISOString().split('T')[0];
          const iphoneFile = path.join(iphoneDir, `iphone-snapshot-${date}-${idx}.json`);
          fs.writeFileSync(iphoneFile, JSON.stringify(iphoneData, null, 2));

          console.log(`  ✅ Captured iPhone: ${device.ip} (${device.vendor})`);
        });
      } else {
        console.log('  ℹ️  No iPhone devices found on network');
      }
    }
  } catch (e) {
    console.log(`  ⚠️  Could not extract iPhone data: ${e.message}`);
  }

  // Step 3: Git operations
  console.log('\n📤 Step 3: Pushing to GitHub...');

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

  // Stage scan results
  execSync('git add network-scan-data/', { cwd: projectDir, stdio: 'pipe' });
  execSync('git add iphone-data/', { cwd: projectDir, stdio: 'pipe' });

  // Commit
  try {
    execSync(`git commit -m "data: Daily startup network scan - ${timestamp}"`, {
      cwd: projectDir,
      stdio: 'pipe'
    });
    console.log('  ✅ Committed scan results');
  } catch (e) {
    // No changes to commit - that's fine
    console.log('  ℹ️  No changes to commit');
  }

  // Push
  execSync('git push origin learning-factory-v2', {
    cwd: projectDir,
    stdio: 'pipe'
  });
  console.log('  ✅ Pushed to GitHub');

  console.log('\n✅ STARTUP SCAN COMPLETE');
  console.log(`📊 Network Results: ${path.join(projectDir, 'network-scan-data')}`);
  console.log(`📱 iPhone Results: ${path.join(projectDir, 'iphone-data')}`);
  console.log(`📦 Pushed: learning-factory-v2 branch`);

} catch (error) {
  console.error('\n❌ Error:', error.message);
  process.exit(1);
}
