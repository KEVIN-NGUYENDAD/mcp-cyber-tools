#!/usr/bin/env node

/**
 * BASELINE ANALYZER - Learn normal device patterns
 *
 * Builds hourly baseline of expected device counts
 * Detects anomalies and spikes
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let config = {
  paths: { stateDir: './reports/home-soc-state' }
};

try {
  const configPath = path.join(__dirname, 'config.json');
  if (fs.existsSync(configPath)) {
    config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  }
} catch (e) {
  // Use defaults
}

class BaselineAnalyzer {
  constructor() {
    this.stateDir = config.paths.stateDir;
  }

  loadBaseline() {
    const baselinePath = path.join(this.stateDir, 'baseline.json');
    if (fs.existsSync(baselinePath)) {
      try {
        return JSON.parse(fs.readFileSync(baselinePath, 'utf8'));
      } catch (e) {
        return this.createEmptyBaseline();
      }
    }
    return this.createEmptyBaseline();
  }

  createEmptyBaseline() {
    return {
      created: new Date().toISOString(),
      hourly: {}, // { "00": { avg: 5, min: 3, max: 8, count: 48 }, ... }
      daily: {}, // { "monday": { avg: 5.2, min: 2, max: 10 }, ... }
      overall: { avg: 5, min: 0, max: 20 }
    };
  }

  loadNetworkHistory() {
    const historyPath = path.join(this.stateDir, 'network-history.json');
    if (fs.existsSync(historyPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
        return data.snapshots || [];
      } catch (e) {
        return [];
      }
    }
    return [];
  }

  calculateBaseline(snapshots) {
    const baseline = this.createEmptyBaseline();

    if (snapshots.length === 0) return baseline;

    // Group by hour and day
    const hourly = {};
    const daily = {};
    let total = 0, min = Infinity, max = 0;

    snapshots.forEach(snap => {
      const date = new Date(snap.timestamp);
      const hour = String(date.getHours()).padStart(2, '0');
      const day = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'][date.getDay()];
      const count = snap.deviceCount;

      // Hourly
      if (!hourly[hour]) hourly[hour] = [];
      hourly[hour].push(count);

      // Daily
      if (!daily[day]) daily[day] = [];
      daily[day].push(count);

      total += count;
      min = Math.min(min, count);
      max = Math.max(max, count);
    });

    // Calculate hourly statistics
    Object.entries(hourly).forEach(([hour, counts]) => {
      const avg = counts.reduce((a, b) => a + b, 0) / counts.length;
      baseline.hourly[hour] = {
        avg: Math.round(avg * 10) / 10,
        min: Math.min(...counts),
        max: Math.max(...counts),
        count: counts.length,
        stdDev: this.calculateStdDev(counts, avg)
      };
    });

    // Calculate daily statistics
    Object.entries(daily).forEach(([day, counts]) => {
      const avg = counts.reduce((a, b) => a + b, 0) / counts.length;
      baseline.daily[day] = {
        avg: Math.round(avg * 10) / 10,
        min: Math.min(...counts),
        max: Math.max(...counts),
        count: counts.length
      };
    });

    // Overall statistics
    baseline.overall = {
      avg: Math.round((total / snapshots.length) * 10) / 10,
      min,
      max,
      totalSnapshots: snapshots.length
    };

    baseline.lastUpdated = new Date().toISOString();
    return baseline;
  }

  calculateStdDev(values, mean) {
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
    return Math.round(Math.sqrt(variance) * 10) / 10;
  }

  detectAnomalies(snapshots) {
    if (snapshots.length < 10) return []; // Need at least 10 samples

    const baseline = this.loadBaseline();
    const anomalies = [];
    const recent = snapshots.slice(-20); // Check last 20 snapshots

    recent.forEach(snap => {
      const date = new Date(snap.timestamp);
      const hour = String(date.getHours()).padStart(2, '0');
      const hourlyBaseline = baseline.hourly[hour];

      if (hourlyBaseline) {
        const deviation = Math.abs(snap.deviceCount - hourlyBaseline.avg);
        const threshold = hourlyBaseline.stdDev * 2; // 2 sigma

        if (deviation > threshold && deviation > 2) {
          anomalies.push({
            timestamp: snap.timestamp,
            deviceCount: snap.deviceCount,
            expectedAvg: hourlyBaseline.avg,
            deviation: Math.round(deviation * 10) / 10,
            type: snap.deviceCount > hourlyBaseline.avg ? 'spike' : 'dip',
            severity: deviation > hourlyBaseline.stdDev * 3 ? 'high' : 'medium'
          });
        }
      }
    });

    return anomalies;
  }

  analyze() {
    const snapshots = this.loadNetworkHistory();
    const baseline = this.calculateBaseline(snapshots);
    const anomalies = this.detectAnomalies(snapshots);

    // Save baseline
    const baselinePath = path.join(this.stateDir, 'baseline.json');
    fs.writeFileSync(baselinePath, JSON.stringify(baseline, null, 2));

    return {
      baseline,
      anomalies,
      timestamp: new Date().toISOString()
    };
  }
}

// Execute
const analyzer = new BaselineAnalyzer();
const result = analyzer.analyze();
console.log('📊 Baseline Analysis:');
console.log(`   Overall avg: ${result.baseline.overall.avg} devices`);
console.log(`   Range: ${result.baseline.overall.min}-${result.baseline.overall.max} devices`);
console.log(`   Anomalies detected: ${result.anomalies.length}`);

export { BaselineAnalyzer };
