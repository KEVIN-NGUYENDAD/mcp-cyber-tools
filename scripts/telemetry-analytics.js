#!/usr/bin/env node

// TELEMETRY ANALYTICS ENGINE
// Generates Customer Truth Report from real usage data

const fs = require('fs');
const path = require('path');
const UsageDatabase = require('../modules/usage-database');

class TelemetryAnalytics {
  constructor(telemetryPath = './telemetry') {
    this.db = new UsageDatabase(telemetryPath);
    this.telemetryPath = telemetryPath;
  }

  // TEAM C: Track usage patterns
  analyzeUsagePatterns() {
    const topUsed = this.db.getTopUsed(20);
    const bottomUsed = this.db.getBottomUsed(10);

    return {
      topUsed: topUsed.map(t => ({
        tool: t.toolName,
        executions: t.executions,
        category: t.category,
        priority: t.priority
      })),
      bottomUsed: bottomUsed.map(t => ({
        tool: t.toolName,
        executions: t.executions,
        category: t.category
      }))
    };
  }

  // TEAM D: Track failure rates
  analyzeFailureRates() {
    const stats = this.db.generateUsageStats();
    const toolsByFailure = Object.values(stats)
      .filter(t => t.executions >= 5) // Min 5 executions for valid sample
      .sort((a, b) => b.failureRate - a.failureRate);

    return {
      totalTools: Object.keys(stats).length,
      toolsWithFailures: toolsByFailure.filter(t => t.failureRate > 0).length,
      highFailureTools: toolsByFailure.slice(0, 10),
      reliableTools: toolsByFailure.filter(t => t.failureRate === 0)
    };
  }

  // TEAM E: Track performance (runtime)
  analyzePerformance() {
    const stats = this.db.generateUsageStats();
    const byDuration = Object.values(stats)
      .sort((a, b) => b.avgDuration - a.avgDuration);

    return {
      slowest: byDuration.slice(0, 10).map(t => ({
        tool: t.toolName,
        avgDuration: t.avgDuration,
        executions: t.executions
      })),
      fastest: byDuration.slice(-10).reverse().map(t => ({
        tool: t.toolName,
        avgDuration: t.avgDuration,
        executions: t.executions
      }))
    };
  }

  // TEAM F: Track investigation paths
  analyzeInvestigationPaths() {
    const records = this.db.loadAllTelemetry();
    const sequences = {};

    // Group by user session and time window (within 5 minutes)
    const sessions = {};
    for (const record of records) {
      const userId = record.executionContext.userId;
      const time = new Date(record.timestamp).getTime();

      if (!sessions[userId]) sessions[userId] = [];
      sessions[userId].push({ tool: record.toolName, time });
    }

    // Extract sequences
    for (const userId in sessions) {
      const userTools = sessions[userId].sort((a, b) => a.time - b.time);

      for (let i = 0; i < userTools.length - 1; i++) {
        const timeDiff = userTools[i + 1].time - userTools[i].time;
        if (timeDiff < 5 * 60 * 1000) { // Within 5 minutes
          const sequence = `${userTools[i].tool} → ${userTools[i + 1].tool}`;
          sequences[sequence] = (sequences[sequence] || 0) + 1;
        }
      }
    }

    // Sort by frequency
    return Object.entries(sequences)
      .map(([path, count]) => ({ path, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 20);
  }

  // TEAM G: Generate Customer Truth Report
  generateCustomerTruthReport() {
    const timestamp = new Date().toISOString();
    const recordCount = this.db.loadAllTelemetry().length;
    const uniqueTools = Object.keys(this.db.generateUsageStats()).length;

    const report = {
      reportType: 'CUSTOMER_TRUTH_REPORT',
      generatedAt: timestamp,
      dataWindow: {
        totalTelemetryRecords: recordCount,
        uniqueToolsExecuted: uniqueTools,
        daysOfData: this.calculateDaysOfData()
      },

      TEAM_C_USAGE_PATTERNS: this.analyzeUsagePatterns(),

      TEAM_D_FAILURE_ANALYSIS: this.analyzeFailureRates(),

      TEAM_E_PERFORMANCE_ANALYSIS: this.analyzePerformance(),

      TEAM_F_INVESTIGATION_PATHS: this.analyzeInvestigationPaths(),

      // Composite analysis
      CONCLUSIONS: {
        coreTools: this.identifyCoreTools(),
        deadWeight: this.identifyDeadWeight(),
        reliabilityIssues: this.identifyReliabilityIssues(),
        performanceBottlenecks: this.identifyPerformanceBottlenecks(),
        criticalWorkflows: this.identifyCriticalWorkflows()
      },

      RECOMMENDATIONS: {
        mustFix: this.getMustFixRecommendations(),
        shouldOptimize: this.getShouldOptimizeRecommendations(),
        canArchive: this.getCanArchiveRecommendations(),
        shouldDelete: this.getShouldDeleteRecommendations()
      }
    };

    return report;
  }

  calculateDaysOfData() {
    const files = fs.readdirSync(this.telemetryPath)
      .filter(f => f.startsWith('telemetry-'));
    return files.length;
  }

  identifyCoreTools() {
    const topUsed = this.db.getTopUsed(15);
    const totalExecutions = topUsed.reduce((sum, t) => sum + t.executions, 0);

    return {
      tools: topUsed,
      concentration: `Top 15 tools = ${totalExecutions} total executions`
    };
  }

  identifyDeadWeight() {
    const bottomUsed = this.db.getBottomUsed(20);
    return {
      tools: bottomUsed.filter(t => t.executions < 5),
      count: bottomUsed.filter(t => t.executions < 5).length
    };
  }

  identifyReliabilityIssues() {
    const failures = this.analyzeFailureRates();
    return {
      failingTools: failures.highFailureTools.slice(0, 5),
      recommendation: 'Fix or archive tools with >20% failure rate'
    };
  }

  identifyPerformanceBottlenecks() {
    const performance = this.analyzePerformance();
    return {
      slowest: performance.slowest.slice(0, 5),
      recommendation: 'Optimize tools averaging >1000ms'
    };
  }

  identifyCriticalWorkflows() {
    const paths = this.analyzeInvestigationPaths();
    return {
      topWorkflows: paths.slice(0, 5),
      recommendation: 'Optimize these common investigation sequences'
    };
  }

  getMustFixRecommendations() {
    const failures = this.analyzeFailureRates();
    return {
      priority: 'IMMEDIATE',
      items: failures.highFailureTools
        .filter(t => t.failureRate > 30)
        .map(t => `Fix ${t.toolName} (${t.failureRate}% failure rate)`)
    };
  }

  getShouldOptimizeRecommendations() {
    const performance = this.analyzePerformance();
    return {
      priority: 'HIGH',
      items: performance.slowest
        .filter(t => t.avgDuration > 1000)
        .map(t => `Optimize ${t.tool} (${t.avgDuration}ms avg)`)
    };
  }

  getCanArchiveRecommendations() {
    const usage = this.analyzeUsagePatterns();
    return {
      priority: 'MEDIUM',
      items: usage.bottomUsed
        .filter(t => t.executions < 3)
        .map(t => `Archive ${t.tool} (${t.executions} executions in period)`)
    };
  }

  getShouldDeleteRecommendations() {
    const failures = this.analyzeFailureRates();
    return {
      priority: 'LOW',
      items: failures.highFailureTools
        .filter(t => t.failureRate > 50 && t.executions > 5)
        .map(t => `Consider deletion: ${t.toolName} (${t.failureRate}% failure)`)
    };
  }

  saveReport(filename = 'customer-truth-report.json') {
    const report = this.generateCustomerTruthReport();
    fs.writeFileSync(filename, JSON.stringify(report, null, 2));
    console.log(`\n✅ Customer Truth Report saved to ${filename}\n`);
    return report;
  }

  printReport() {
    const report = this.generateCustomerTruthReport();

    console.log('\n╔════════════════════════════════════════════════════════════╗');
    console.log('║         CYBER-TOOLS CUSTOMER TRUTH REPORT                  ║');
    console.log('╚════════════════════════════════════════════════════════════╝\n');

    console.log(`Generated: ${report.generatedAt}`);
    console.log(`Total Records: ${report.dataWindow.totalTelemetryRecords}`);
    console.log(`Unique Tools: ${report.dataWindow.uniqueToolsExecuted}`);
    console.log(`Days of Data: ${report.dataWindow.daysOfData}\n`);

    console.log('TOP USED TOOLS:');
    report.TEAM_C_USAGE_PATTERNS.topUsed.forEach((t, i) => {
      console.log(`  ${i + 1}. ${t.tool}: ${t.executions} executions [${t.priority}]`);
    });

    console.log('\nLEAST USED TOOLS:');
    report.TEAM_C_USAGE_PATTERNS.bottomUsed.forEach((t, i) => {
      console.log(`  ${i + 1}. ${t.tool}: ${t.executions} executions`);
    });

    console.log('\nHIGH FAILURE RATE TOOLS:');
    report.TEAM_D_FAILURE_ANALYSIS.highFailureTools.slice(0, 5).forEach(t => {
      console.log(`  ${t.toolName}: ${t.failureRate}% failure rate (${t.executions} executions)`);
    });

    console.log('\nSLOWEST TOOLS:');
    report.TEAM_E_PERFORMANCE_ANALYSIS.slowest.slice(0, 5).forEach(t => {
      console.log(`  ${t.tool}: ${t.avgDuration}ms average`);
    });

    console.log('\nTOP INVESTIGATION WORKFLOWS:');
    report.TEAM_F_INVESTIGATION_PATHS.slice(0, 5).forEach((p, i) => {
      console.log(`  ${i + 1}. ${p.path} (${p.count} times)`);
    });

    console.log('\nRECOMMENDATIONS:');
    console.log(`  Must Fix (${report.RECOMMENDATIONS.mustFix.items.length}):`);
    report.RECOMMENDATIONS.mustFix.items.slice(0, 3).forEach(r => console.log(`    - ${r}`));

    console.log(`  Can Archive (${report.RECOMMENDATIONS.canArchive.items.length}):`);
    report.RECOMMENDATIONS.canArchive.items.slice(0, 3).forEach(r => console.log(`    - ${r}`));

    console.log('\n════════════════════════════════════════════════════════════\n');
  }
}

// CLI Execution
if (require.main === module) {
  const analytics = new TelemetryAnalytics('./telemetry');

  if (fs.existsSync('./telemetry')) {
    analytics.printReport();
    analytics.saveReport();
  } else {
    console.log('No telemetry data found. Run tools with telemetry instrumentation first.');
  }
}

module.exports = TelemetryAnalytics;
