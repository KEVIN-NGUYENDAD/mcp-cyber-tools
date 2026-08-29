#!/usr/bin/env node

/**
 * COLLECTOR TELEMETRY
 *
 * Tracks Phase 1 collection performance and evidence quality.
 * Runs after each collection to record metrics.
 *
 * Metrics:
 * - Device count trends
 * - Camera availability
 * - Change event frequency
 * - Collection success/failure
 * - Evidence completeness
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class CollectorTelemetry {
  constructor() {
    this.stateDir = './reports/home-soc-state';
    this.telemetryDir = './reports/home-soc-state/telemetry';
    this.ensureDirectories();
  }

  ensureDirectories() {
    if (!fs.existsSync(this.telemetryDir)) {
      fs.mkdirSync(this.telemetryDir, { recursive: true });
    }
  }

  recordMetrics() {
    const timestamp = new Date().toISOString();
    const metrics = {
      timestamp,
      collection: this.getCollectionMetrics(),
      evidence: this.getEvidenceMetrics(),
      network: this.getNetworkMetrics(),
      cameras: this.getCameraMetrics()
    };

    return metrics;
  }

  getCollectionMetrics() {
    // How many collections have been run?
    const historyPath = path.join(this.stateDir, 'device-history.json');
    let timeline = [];

    if (fs.existsSync(historyPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
        timeline = data.timeline || [];
      } catch (e) {
        // Continue
      }
    }

    return {
      totalCollections: timeline.length,
      averageDevicesPerCollection: timeline.length > 0
        ? Math.round(timeline.reduce((sum, t) => sum + t.deviceCount, 0) / timeline.length)
        : 0,
      lastCollectionTime: timeline.length > 0 ? timeline[timeline.length - 1].timestamp : null
    };
  }

  getEvidenceMetrics() {
    // What evidence has been collected?
    const metrics = {
      deviceHistorySize: 0,
      networkHistorySize: 0,
      changesRecorded: 0,
      timespan: null
    };

    // Device history size
    const devicePath = path.join(this.stateDir, 'device-history.json');
    if (fs.existsSync(devicePath)) {
      metrics.deviceHistorySize = fs.statSync(devicePath).size;
    }

    // Network history size
    const networkPath = path.join(this.stateDir, 'network-history.json');
    if (fs.existsSync(networkPath)) {
      metrics.networkHistorySize = fs.statSync(networkPath).size;
    }

    // Changes recorded
    const changesPath = path.join(this.stateDir, 'changes.json');
    if (fs.existsSync(changesPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(changesPath, 'utf8'));
        metrics.changesRecorded = (data.changes || []).length;
      } catch (e) {
        // Continue
      }
    }

    return metrics;
  }

  getNetworkMetrics() {
    // Network stability metrics
    const networkPath = path.join(this.stateDir, 'network-history.json');
    const metrics = {
      totalSnapshots: 0,
      averageDeviceCount: 0,
      minDevices: null,
      maxDevices: null,
      stability: 'unknown'
    };

    if (fs.existsSync(networkPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(networkPath, 'utf8'));
        const snapshots = data.snapshots || [];

        if (snapshots.length > 0) {
          metrics.totalSnapshots = snapshots.length;
          metrics.averageDeviceCount = data.averageDevices || 0;

          const counts = snapshots.map(s => s.deviceCount);
          metrics.minDevices = Math.min(...counts);
          metrics.maxDevices = Math.max(...counts);

          // Stability: how much variance?
          const variance = counts.length > 1
            ? counts.reduce((sum, c) => sum + Math.pow(c - metrics.averageDeviceCount, 2), 0) / counts.length
            : 0;

          if (variance < 1) metrics.stability = 'very-stable';
          else if (variance < 5) metrics.stability = 'stable';
          else if (variance < 10) metrics.stability = 'variable';
          else metrics.stability = 'unstable';
        }
      } catch (e) {
        // Continue
      }
    }

    return metrics;
  }

  getCameraMetrics() {
    // Camera monitoring metrics
    const historyPath = path.join(this.stateDir, 'device-history.json');
    const metrics = {
      camerasMonitored: 0,
      onlineCount: 0,
      offlineCount: 0,
      offlinePercentage: 0,
      avgOnlinePercentage: 0
    };

    if (fs.existsSync(historyPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
        const cameras = data.cameraStatus || [];

        if (cameras.length > 0) {
          metrics.camerasMonitored = cameras.length;
          metrics.onlineCount = cameras.filter(c => c.status === 'online').length;
          metrics.offlineCount = cameras.filter(c => c.status === 'offline').length;
          metrics.offlinePercentage = Math.round(
            (metrics.offlineCount / cameras.length) * 100
          );
        }
      } catch (e) {
        // Continue
      }
    }

    return metrics;
  }

  appendTelemetry(metrics) {
    const telemetryPath = path.join(this.telemetryDir, 'collector-metrics.jsonl');

    // Append as JSON line (for streaming analysis)
    const line = JSON.stringify(metrics);
    fs.appendFileSync(telemetryPath, line + '\n');
  }

  generateDailySummary() {
    // Generate daily telemetry summary
    const today = new Date().toISOString().split('T')[0];
    const dailyPath = path.join(this.telemetryDir, `daily-${today}.json`);

    const metrics = this.recordMetrics();
    fs.writeFileSync(dailyPath, JSON.stringify(metrics, null, 2));

    return metrics;
  }

  displayMetrics() {
    const metrics = this.recordMetrics();

    console.log('\n📊 COLLECTOR TELEMETRY');
    console.log('=====================\n');

    console.log('📈 Collection Stats:');
    console.log(`   Total collections: ${metrics.collection.totalCollections}`);
    console.log(`   Avg devices/collection: ${metrics.collection.averageDevicesPerCollection}`);

    console.log('\n📁 Evidence Size:');
    console.log(`   Device history: ${(metrics.evidence.deviceHistorySize / 1024).toFixed(1)} KB`);
    console.log(`   Network history: ${(metrics.evidence.networkHistorySize / 1024).toFixed(1)} KB`);
    console.log(`   Changes recorded: ${metrics.evidence.changesRecorded}`);

    console.log('\n🌐 Network Stability:');
    console.log(`   Snapshots: ${metrics.network.totalSnapshots}`);
    console.log(`   Avg devices: ${metrics.network.averageDeviceCount}`);
    console.log(`   Range: ${metrics.network.minDevices} - ${metrics.network.maxDevices}`);
    console.log(`   Stability: ${metrics.network.stability}`);

    console.log('\n📹 Camera Status:');
    console.log(`   Monitored: ${metrics.cameras.camerasMonitored}`);
    console.log(`   Online: ${metrics.cameras.onlineCount}`);
    console.log(`   Offline: ${metrics.cameras.offlineCount} (${metrics.cameras.offlinePercentage}%)`);

    console.log('');
  }
}

// Execute
const telemetry = new CollectorTelemetry();
telemetry.displayMetrics();
telemetry.appendTelemetry(telemetry.recordMetrics());
telemetry.generateDailySummary();

export { CollectorTelemetry };
