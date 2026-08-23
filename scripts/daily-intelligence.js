#!/usr/bin/env node

// DAILY INTELLIGENCE SYSTEM
// Analyzes telemetry daily and extracts actionable insights

const fs = require('fs');
const path = require('path');
const UsageDatabase = require('../modules/usage-database');

class DailyIntelligence {
  constructor(telemetryPath = './telemetry') {
    this.telemetryPath = telemetryPath;
    this.db = new UsageDatabase(telemetryPath);
    this.insights = [];
  }

  // TEAM B: Daily usage leaderboard
  getDailyUsageLeaderboard(days = 1) {
    const records = this.getTodaysTelemetry(days);
    const usage = {};

    for (const record of records) {
      if (!usage[record.toolName]) {
        usage[record.toolName] = 0;
      }
      usage[record.toolName]++;
    }

    return Object.entries(usage)
      .map(([tool, count]) => ({ tool, executions: count }))
      .sort((a, b) => b.executions - a.executions);
  }

  // TEAM C: Daily failure leaderboard
  getDailyFailureLeaderboard(days = 1) {
    const records = this.getTodaysTelemetry(days);
    const failures = {};

    for (const record of records) {
      if (!failures[record.toolName]) {
        failures[record.toolName] = { total: 0, failed: 0 };
      }
      failures[record.toolName].total++;
      if (!record.success) {
        failures[record.toolName].failed++;
      }
    }

    return Object.entries(failures)
      .filter(([_, data]) => data.total >= 3) // Min 3 executions
      .map(([tool, data]) => ({
        tool,
        failureRate: Math.round((data.failed / data.total) * 100),
        executions: data.total,
        failures: data.failed
      }))
      .sort((a, b) => b.failureRate - a.failureRate);
  }

  // TEAM D: Daily performance leaderboard
  getDailyPerformanceLeaderboard(days = 1) {
    const records = this.getTodaysTelemetry(days);
    const performance = {};

    for (const record of records) {
      if (!performance[record.toolName]) {
        performance[record.toolName] = { durations: [], count: 0 };
      }
      performance[record.toolName].durations.push(record.duration);
      performance[record.toolName].count++;
    }

    return Object.entries(performance)
      .map(([tool, data]) => ({
        tool,
        avgDuration: Math.round(data.durations.reduce((a, b) => a + b, 0) / data.durations.length),
        maxDuration: Math.max(...data.durations),
        minDuration: Math.min(...data.durations),
        executions: data.count
      }))
      .sort((a, b) => b.avgDuration - a.avgDuration);
  }

  // TEAM E: Detect anomalies within 24 hours
  detectAnomalies(days = 1) {
    const anomalies = [];
    const failures = this.getDailyFailureLeaderboard(days);
    const performance = this.getDailyPerformanceLeaderboard(days);

    // New failures detected
    failures.slice(0, 5).forEach(tool => {
      if (tool.failureRate > 30) {
        anomalies.push({
          type: 'NEW_FAILURE',
          severity: 'HIGH',
          tool: tool.tool,
          metric: `${tool.failureRate}% failure rate`,
          action: `Investigate ${tool.tool}: ${tool.failures}/${tool.executions} failures`
        });
      }
    });

    // New bottlenecks detected
    performance.slice(0, 5).forEach(tool => {
      if (tool.avgDuration > 2000) {
        anomalies.push({
          type: 'BOTTLENECK',
          severity: 'MEDIUM',
          tool: tool.tool,
          metric: `${tool.avgDuration}ms average`,
          action: `Optimize ${tool.tool}: slow performance detected`
        });
      }
    });

    return anomalies;
  }

  // TEAM F: Extract insights
  extractInsights() {
    const insights = [];
    const usage = this.getDailyUsageLeaderboard();
    const failures = this.getDailyFailureLeaderboard();
    const performance = this.getDailyPerformanceLeaderboard();

    // Insight 1: Most used tool
    if (usage.length > 0) {
      insights.push({
        id: 'INSIGHT_001',
        type: 'USAGE_PATTERN',
        title: 'Most Used Tool Today',
        content: `${usage[0].tool} executed ${usage[0].executions} times`,
        value: 'Confirms core tool reliability',
        action: 'Monitor for performance regression'
      });
    }

    // Insight 2: High failure rate
    if (failures.length > 0 && failures[0].failureRate > 20) {
      insights.push({
        id: 'INSIGHT_002',
        type: 'RELIABILITY',
        title: 'Tool Failure Detected',
        content: `${failures[0].tool} has ${failures[0].failureRate}% failure rate`,
        value: 'Critical issue affecting users',
        action: `Prioritize fix for ${failures[0].tool}`
      });
    }

    // Insight 3: Performance bottleneck
    if (performance.length > 0 && performance[0].avgDuration > 1500) {
      insights.push({
        id: 'INSIGHT_003',
        type: 'PERFORMANCE',
        title: 'Slow Tool Detected',
        content: `${performance[0].tool} averaging ${performance[0].avgDuration}ms`,
        value: 'User experience degradation',
        action: `Profile and optimize ${performance[0].tool}`
      });
    }

    // Insight 4: Unused tool
    if (usage.length > 20) {
      const unused = usage.slice(-5).filter(t => t.executions < 2);
      if (unused.length > 0) {
        insights.push({
          id: 'INSIGHT_004',
          type: 'COVERAGE',
          title: 'Unused Tools Detected',
          content: `${unused.map(t => t.tool).join(', ')} not used today`,
          value: 'Maintenance burden on non-essential tools',
          action: 'Mark for archival'
        });
      }
    }

    // Insight 5: Most reliable tool
    const reliable = failures.filter(t => t.failureRate === 0);
    if (reliable.length > 0) {
      insights.push({
        id: 'INSIGHT_005',
        type: 'RELIABILITY',
        title: 'Reliable Tool Identified',
        content: `${reliable[0].tool} had 0% failure rate (${reliable[0].executions} executions)`,
        value: 'Production-ready tool',
        action: 'Use as baseline for other tools'
      });
    }

    return insights;
  }

  // TEAM G: Create daily dashboard
  generateDailyDashboard() {
    const timestamp = new Date().toISOString();
    const date = timestamp.split('T')[0];

    return {
      date: date,
      timestamp: timestamp,
      sections: {
        'TOP_USED': this.getDailyUsageLeaderboard().slice(0, 5),
        'TOP_FAILURES': this.getDailyFailureLeaderboard().slice(0, 5),
        'SLOWEST_TOOLS': this.getDailyPerformanceLeaderboard().slice(0, 5),
        'ANOMALIES': this.detectAnomalies(),
        'INSIGHTS': this.extractInsights()
      }
    };
  }

  // Helper: Get today's telemetry
  getTodaysTelemetry(days = 1) {
    const date = new Date();
    date.setDate(date.getDate() - days + 1);
    const dateStr = date.toISOString().split('T')[0];

    const filePath = path.join(this.telemetryPath, `telemetry-${dateStr}.json`);

    if (!fs.existsSync(filePath)) {
      return [];
    }

    try {
      return JSON.parse(fs.readFileSync(filePath, 'utf8'));
    } catch (e) {
      return [];
    }
  }

  // Print daily report
  printDailyReport() {
    const dashboard = this.generateDailyDashboard();
    const date = dashboard.date;

    console.log('\n╔════════════════════════════════════════════════════════════╗');
    console.log('║         CYBER-TOOLS DAILY INTELLIGENCE REPORT             ║');
    console.log('╚════════════════════════════════════════════════════════════╝\n');

    console.log(`Date: ${date}\n`);

    console.log('📊 TOP USED TOOLS (Today):');
    dashboard.sections.TOP_USED.forEach((t, i) => {
      console.log(`  ${i + 1}. ${t.tool}: ${t.executions} executions`);
    });

    console.log('\n⚠️  FAILURE ALERTS (Today):');
    if (dashboard.sections.TOP_FAILURES.length > 0) {
      dashboard.sections.TOP_FAILURES.forEach((t, i) => {
        console.log(`  ${i + 1}. ${t.tool}: ${t.failureRate}% failures (${t.failed}/${t.total})`);
      });
    } else {
      console.log('  ✅ No failures detected');
    }

    console.log('\n⚡ PERFORMANCE (Slowest Tools):');
    dashboard.sections.SLOWEST_TOOLS.slice(0, 3).forEach((t, i) => {
      console.log(`  ${i + 1}. ${t.tool}: ${t.avgDuration}ms average`);
    });

    console.log('\n🚨 ANOMALIES DETECTED:');
    if (dashboard.sections.ANOMALIES.length > 0) {
      dashboard.sections.ANOMALIES.forEach(a => {
        console.log(`  [${a.severity}] ${a.type}: ${a.action}`);
      });
    } else {
      console.log('  ✅ No anomalies');
    }

    console.log('\n💡 INSIGHTS (Actions Required):');
    dashboard.sections.INSIGHTS.forEach((insight, i) => {
      console.log(`  ${i + 1}. ${insight.title}`);
      console.log(`     → ${insight.content}`);
      console.log(`     → Action: ${insight.action}\n`);
    });

    console.log('════════════════════════════════════════════════════════════\n');

    return dashboard;
  }

  // Save daily report
  saveDailyReport() {
    const dashboard = this.generateDailyDashboard();
    const filename = `daily-intelligence-${dashboard.date}.json`;
    fs.writeFileSync(filename, JSON.stringify(dashboard, null, 2));
    console.log(`✅ Daily report saved: ${filename}\n`);
    return dashboard;
  }

  // Save insights to knowledge base
  saveInsights() {
    const dashboard = this.generateDailyDashboard();
    const insightsFile = 'daily-insights.json';

    let allInsights = [];
    if (fs.existsSync(insightsFile)) {
      try {
        allInsights = JSON.parse(fs.readFileSync(insightsFile, 'utf8'));
      } catch (e) {
        allInsights = [];
      }
    }

    allInsights.push({
      date: dashboard.date,
      count: dashboard.sections.INSIGHTS.length,
      insights: dashboard.sections.INSIGHTS
    });

    fs.writeFileSync(insightsFile, JSON.stringify(allInsights.slice(-30), null, 2)); // Keep last 30 days
  }
}

// CLI Execution
if (require.main === module) {
  const intelligence = new DailyIntelligence('./telemetry');

  if (fs.existsSync('./telemetry')) {
    intelligence.printDailyReport();
    intelligence.saveDailyReport();
    intelligence.saveInsights();
  } else {
    console.log('No telemetry data found. Start collecting data first.');
  }
}

module.exports = DailyIntelligence;
