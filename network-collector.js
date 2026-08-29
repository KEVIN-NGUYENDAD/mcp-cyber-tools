#!/usr/bin/env node

/**
 * NETWORK COLLECTOR - Lightweight continuous monitoring
 *
 * Modes:
 * - Normal: Every 30 minutes (1800s) - full collection
 * - Fast Scan: Every 5 minutes (300s) - when suspicious activity detected
 *
 * Stores in JSON history files.
 * Reports generated ONCE at 8PM from accumulated evidence.
 * Alerts sent immediately on suspicious activity.
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

// Load config
let config = {
  paths: {
    stateDir: './reports/home-soc-state',
    logsDir: './logs'
  },
  network: {
    cameraIPs: ['192.168.1.100', '192.168.1.101', '192.168.1.102'],
    fastScanEnabled: false
  },
  alerts: {
    enabled: true,
    onNewDevice: true,
    onDeviceOffline: true
  },
  jsonManagement: {
    maxHistoryEntries: 100,
    archiveOldChanges: true,
    keepChangesForDays: 7
  },
  logging: {
    enabled: true,
    noRotation: true,
    singleFile: 'mcp-server.log'
  }
};

try {
  const configPath = path.join(__dirname, 'config.json');
  if (fs.existsSync(configPath)) {
    config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  }
} catch (e) {
  console.error('Warning: Failed to load config.json, using defaults');
}

class NetworkCollector {
  constructor() {
    this.stateDir = config.paths.stateDir;
    this.logsDir = config.paths.logsDir;
    this.cameraIPs = config.network.cameraIPs;
    this.ensureDirectories();
  }

  ensureDirectories() {
    if (!fs.existsSync(this.stateDir)) {
      fs.mkdirSync(this.stateDir, { recursive: true });
    }
    if (!fs.existsSync(this.logsDir)) {
      fs.mkdirSync(this.logsDir, { recursive: true });
    }
  }

  logMessage(level, message) {
    if (!config.logging.enabled) return;
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] ${level.toUpperCase()}: ${message}`;
    const logFile = path.join(this.logsDir, config.logging.singleFile || 'network-collector.log');
    try {
      fs.appendFileSync(logFile, logEntry + '\n');
    } catch (e) {
      // Silently fail
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
    const cameras = [];
    for (const ip of this.cameraIPs) {
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
          severity: 'warning'
        });
      }
    });

    // Detect offline devices
    Object.entries(previousByIP).forEach(([ip, device]) => {
      if (!currentByIP[ip]) {
        changes.push({
          type: 'device-offline',
          ip,
          mac: device.mac,
          timestamp,
          severity: 'info'
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

    // Add new changes, keep limited entries
    history.changes = [...history.changes, ...newChanges].slice(-config.jsonManagement.maxHistoryEntries);
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

    const snapshot = {
      timestamp: new Date().toISOString(),
      deviceCount: devices.length,
      devices: devices.map(d => ({ ip: d.ip, mac: d.mac }))
    };

    history.snapshots = [...history.snapshots, snapshot].slice(-config.jsonManagement.maxHistoryEntries);
    history.lastUpdated = new Date().toISOString();
    history.averageDevices = Math.round(
      history.snapshots.reduce((sum, s) => sum + s.deviceCount, 0) / history.snapshots.length
    );

    fs.writeFileSync(networkPath, JSON.stringify(history, null, 2));
  }

  createAlert(type, data) {
    if (!config.alerts.enabled) return;

    const alertsPath = path.join(this.stateDir, 'alerts.json');
    let alertsHistory = { alerts: [] };

    if (fs.existsSync(alertsPath)) {
      try {
        alertsHistory = JSON.parse(fs.readFileSync(alertsPath, 'utf8'));
      } catch (e) {
        alertsHistory = { alerts: [] };
      }
    }

    const alert = {
      id: `alert-${Date.now()}`,
      type,
      timestamp: new Date().toISOString(),
      severity: data.severity || 'medium',
      data,
      acknowledged: false
    };

    alertsHistory.alerts = [...alertsHistory.alerts, alert].slice(-config.alerts.maxAlerts);
    fs.writeFileSync(alertsPath, JSON.stringify(alertsHistory, null, 2));

    // Log alert
    this.logMessage('alert', `${type}: ${JSON.stringify(data)}`);

    // Output alert to console for immediate visibility
    console.log(`🚨 ALERT [${alert.severity.toUpperCase()}]: ${type}`);
    console.log(`   ${JSON.stringify(data)}`);

    return alert;
  }

  enableFastScan() {
    if (!config.network.fastScanEnabled) {
      config.network.fastScanEnabled = true;
      this.logMessage('info', 'Fast scan mode ENABLED');
      console.log('⚡ FAST SCAN MODE ACTIVATED (checking every 5 minutes)');
    }
  }

  disableFastScan() {
    if (config.network.fastScanEnabled) {
      config.network.fastScanEnabled = false;
      this.logMessage('info', 'Fast scan mode DISABLED');
      console.log('✓ Fast scan mode disabled, returning to normal schedule');
    }
  }

  collect(scanMode = 'normal') {
    const timestamp = new Date().toISOString();
    const modeLabel = scanMode === 'fast' ? '⚡ FAST' : '📡';

    console.log(`${modeLabel} Network Collector - ${scanMode === 'fast' ? 'Fast Scan' : 'Normal Collection'}`);
    console.log('=============================================\n');

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
      console.log(`   ⚠️  Changes detected: ${changes.length}`);
      changes.forEach(c => {
        console.log(`     - ${c.type}: ${c.ip}`);

        // Create alerts for new devices
        if (c.type === 'new-device' && config.alerts.onNewDevice) {
          this.createAlert('new-device-detected', {
            ip: c.ip,
            mac: c.mac,
            severity: 'high'
          });
          // Enable fast scan when suspicious device appears
          this.enableFastScan();
        }

        // Create alerts for offline devices
        if (c.type === 'device-offline' && config.alerts.onDeviceOffline) {
          this.createAlert('device-went-offline', {
            ip: c.ip,
            mac: c.mac,
            severity: 'medium'
          });
        }
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
      ].slice(-config.jsonManagement.maxHistoryEntries)
    };
    this.saveDeviceHistory(newHistory);

    // 6. Update changes log
    if (changes.length > 0) {
      this.updateChangesLog(changes);
    }

    // 7. Update network history
    this.updateNetworkHistory(currentDevices);

    console.log('\n✅ Collection complete');
    console.log(`   Stored to:`);
    console.log(`   - device-history.json`);
    console.log(`   - changes.json`);
    console.log(`   - network-history.json`);
    console.log(`   - alerts.json`);
    console.log(`   - Timestamp: ${timestamp}`);

    if (config.network.fastScanEnabled) {
      console.log(`\n   📊 Fast scan mode: ACTIVE`);
    }

    this.logMessage('info', `Collection (${scanMode}): ${currentDevices.length} devices, ${changes.length} changes`);

    return {
      devices: currentDevices,
      changes,
      cameras,
      timestamp,
      mode: scanMode
    };
  }
}

// Execute
const collector = new NetworkCollector();
try {
  const scanMode = process.argv[2] === 'fast' ? 'fast' : 'normal';
  collector.collect(scanMode);
} catch (err) {
  console.error('❌ Collection failed:', err.message);
  process.exit(1);
}

export { NetworkCollector };
