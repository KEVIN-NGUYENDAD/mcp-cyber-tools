#!/usr/bin/env node

/**
 * NETWORK COLLECTOR - Lightweight continuous monitoring
 *
 * Runs frequently to collect:
 * - ARP table snapshots
 * - Device presence
 * - Camera presence
 * - Change detection
 *
 * Stores in JSON history files.
 * Reports generated ONCE at 8PM from accumulated evidence.
 *
 * NO expensive nmap scans during collection.
 * NO full discovery runs.
 * Only ARP and basic presence checks.
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class NetworkCollector {
  constructor() {
    this.stateDir = './reports/home-soc-state';
    this.ensureDirectories();
  }

  ensureDirectories() {
    if (!fs.existsSync(this.stateDir)) {
      fs.mkdirSync(this.stateDir, { recursive: true });
    }
  }

  getARPTable() {
    const devices = [];
    try {
      const output = execSync('arp -a', { encoding: 'utf-8' });
      const lines = output.split('\n');

      for (const line of lines) {
        const match = line.match(/\((\d+\.\d+\.\d+\.\d+)\).*?([0-9a-f:]+)/i);
        if (match) {
          devices.push({
            ip: match[1],
            mac: match[2].toLowerCase(),
            timestamp: new Date().toISOString()
          });
        }
      }
    } catch (error) {
      // ARP not available, return empty
    }

    return devices;
  }

  checkCameraPresence() {
    // Check if known camera IPs respond to ping
    const cameraIPs = [
      '192.168.1.100',
      '192.168.1.101',
      '192.168.1.102'
    ];

    const cameras = [];
    for (const ip of cameraIPs) {
      try {
        execSync(`ping -c 1 -W 1 ${ip}`, { stdio: 'ignore' });
        cameras.push({
          ip,
          status: 'online',
          lastSeen: new Date().toISOString()
        });
      } catch {
        cameras.push({
          ip,
          status: 'offline',
          lastSeen: new Date().toISOString()
        });
      }
    }

    return cameras;
  }

  loadDeviceHistory() {
    const historyPath = path.join(this.stateDir, 'device-history.json');

    if (fs.existsSync(historyPath)) {
      try {
        return JSON.parse(fs.readFileSync(historyPath, 'utf8'));
      } catch (e) {
        return { devices: [], timeline: [] };
      }
    }

    return { devices: [], timeline: [] };
  }

  saveDeviceHistory(history) {
    const historyPath = path.join(this.stateDir, 'device-history.json');
    fs.writeFileSync(historyPath, JSON.stringify(history, null, 2));
  }

  detectChanges(currentDevices, previousHistory) {
    const changes = [];
    const timestamp = new Date().toISOString();

    // Map current devices by IP
    const currentByIP = {};
    currentDevices.forEach(d => {
      currentByIP[d.ip] = d;
    });

    // Map previous devices by IP
    const previousByIP = {};
    if (previousHistory.devices && previousHistory.devices.length > 0) {
      previousHistory.devices.forEach(d => {
        previousByIP[d.ip] = d;
      });
    }

    // Detect new devices
    Object.entries(currentByIP).forEach(([ip, device]) => {
      if (!previousByIP[ip]) {
        changes.push({
          type: 'new-device',
          ip,
          mac: device.mac,
          timestamp,
          severity: 'info'
        });
      }
    });

    // Detect offline devices (in previous but not current)
    Object.entries(previousByIP).forEach(([ip, device]) => {
      if (!currentByIP[ip]) {
        changes.push({
          type: 'device-offline',
          ip,
          mac: device.mac,
          timestamp,
          severity: 'warning'
        });
      }
    });

    return changes;
  }

  updateChangesLog(newChanges) {
    const changesPath = path.join(this.stateDir, 'changes.json');
    let history = { changes: [] };

    if (fs.existsSync(changesPath)) {
      try {
        history = JSON.parse(fs.readFileSync(changesPath, 'utf8'));
      } catch (e) {
        history = { changes: [] };
      }
    }

    // Add new changes, keep last 1000
    history.changes = [...history.changes, ...newChanges].slice(-1000);
    history.lastUpdated = new Date().toISOString();

    fs.writeFileSync(changesPath, JSON.stringify(history, null, 2));
  }

  updateNetworkHistory(devices) {
    const networkPath = path.join(this.stateDir, 'network-history.json');
    let history = { snapshots: [] };

    if (fs.existsSync(networkPath)) {
      try {
        history = JSON.parse(fs.readFileSync(networkPath, 'utf8'));
      } catch (e) {
        history = { snapshots: [] };
      }
    }

    // Add snapshot (keep last 1000 snapshots = ~16 days at 1 per hour)
    const snapshot = {
      timestamp: new Date().toISOString(),
      deviceCount: devices.length,
      devices: devices.map(d => ({ ip: d.ip, mac: d.mac }))
    };

    history.snapshots = [...history.snapshots, snapshot].slice(-1000);
    history.lastUpdated = new Date().toISOString();
    history.averageDevices = Math.round(
      history.snapshots.reduce((sum, s) => sum + s.deviceCount, 0) / history.snapshots.length
    );

    fs.writeFileSync(networkPath, JSON.stringify(history, null, 2));
  }

  collect() {
    console.log('📡 Network Collector - Lightweight Collection');
    console.log('=============================================\n');

    const timestamp = new Date().toISOString();

    // 1. Get current ARP table
    console.log('📋 Reading ARP table...');
    const currentDevices = this.getARPTable();
    console.log(`   Found: ${currentDevices.length} devices`);

    // 2. Load previous history
    const previousHistory = this.loadDeviceHistory();
    console.log(`   Previous: ${previousHistory.devices?.length || 0} devices`);

    // 3. Detect changes
    const changes = this.detectChanges(currentDevices, previousHistory);
    if (changes.length > 0) {
      console.log(`   Changes: ${changes.length}`);
      changes.forEach(c => {
        console.log(`     - ${c.type}: ${c.ip}`);
      });
    }

    // 4. Check camera presence
    console.log('\n📹 Checking camera presence...');
    const cameras = this.checkCameraPresence();
    const onlineCameras = cameras.filter(c => c.status === 'online').length;
    console.log(`   Online: ${onlineCameras}/${cameras.length}`);

    // 5. Update device history
    const newHistory = {
      devices: currentDevices,
      cameraStatus: cameras,
      lastCollected: timestamp,
      timeline: [
        ...(previousHistory.timeline || []),
        {
          timestamp,
          deviceCount: currentDevices.length,
          changes: changes.length
        }
      ].slice(-100) // Keep last 100 entries
    };
    this.saveDeviceHistory(newHistory);

    // 6. Update changes log
    if (changes.length > 0) {
      this.updateChangesLog(changes);
    }

    // 7. Update network history
    this.updateNetworkHistory(currentDevices);

    console.log('\n✅ Collection complete');
    console.log(`   Stored to:
   - device-history.json (current devices + camera status)
   - changes.json (change log)
   - network-history.json (historical snapshots)
   - Timestamp: ${timestamp}`);

    return {
      devices: currentDevices,
      changes,
      cameras,
      timestamp
    };
  }
}

// Execute
const collector = new NetworkCollector();
try {
  collector.collect();
} catch (err) {
  console.error('❌ Collection failed:', err.message);
  process.exit(1);
}

export { NetworkCollector };
