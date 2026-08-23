#!/usr/bin/env node

// DAILY-REPORT.js
// Generate daily intelligence from telemetry collected so far
// Run this EVERY DAY during 7-day collection phase

import fs from 'fs';
import path from 'path';

class DailyReport {
  constructor() {
    this.telemetryPath = './telemetry';
    this.data = { records: [], tools: {} };
  }

  loadTelemetry() {
    if (!fs.existsSync(this.telemetryPath)) {
      return false;
    }

    const files = fs.readdirSync(this.telemetryPath)
      .filter(f => f.startsWith('telemetry-') && f.endsWith('.json'))
      .sort();

    if (files.length === 0) return false;

    for (const file of files) {
      try {
        const data = JSON.parse(fs.readFileSync(path.join(this.telemetryPath, file), 'utf8'));
        if (Array.isArray(data)) {
          this.data.records = this.data.records.concat(data);
        }
      } catch (error) {
        // Silently skip corrupt files
      }
    }

    return this.data.records.length > 0;
  }

  analyzeTools() {
    const tools = {};

    for (const record of this.data.records) {
      if (!tools[record.toolName]) {
        tools[record.toolName] = {
          executions: 0,
          success: 0,
          failed: 0,
          totalDuration: 0
        };
      }

      const tool = tools[record.toolName];
      tool.executions++;
      tool.totalDuration += record.duration || 0;

      if (record.success) {
        tool.success++;
      } else {
        tool.failed++;
      }
    }

    // Add metrics
    for (const tool of Object.values(tools)) {
      tool.avgDuration = Math.round(tool.totalDuration / tool.executions);
      tool.successRate = Math.round((tool.success / tool.executions) * 100);
    }

    this.data.tools = tools;
  }

  generateReport() {
    const today = new Date().toISOString().split('T')[0];
    const totalExecution = this.data.records.length;
    const totalSuccess = this.data.records.filter(r => r.success).length;
    const totalFailed = totalExecution - totalSuccess;
    const avgDuration = Math.round(
      this.data.records.reduce((sum, r) => sum + (r.duration || 0), 0) / totalExecution
    );

    const tools = Object.values(this.data.tools)
      .sort((a, b) => b.executions - a.executions);

    const topTools = tools.slice(0, 10);
    const failureTools = tools.filter(t => t.failed > 0).sort((a, b) => b.failed - a.failed);

    let report = `# DAILY INTELLIGENCE REPORT\n\n`;
    report += `**Generated:** ${new Date().toISOString()}\n`;
    report += `**Data Period:** ${this.getDateRange()}\n`;
    report += `**Collection Days:** ${this.getCollectionDays()}\n\n`;

    report += `## SUMMARY\n\n`;
    report += `| Metric | Value |\n`;
    report += `|--------|-------|\n`;
    report += `| Total Executions | ${totalExecution} |\n`;
    report += `| Successful | ${totalSuccess} (${Math.round((totalSuccess/totalExecution)*100)}%) |\n`;
    report += `| Failed | ${totalFailed} (${Math.round((totalFailed/totalExecution)*100)}%) |\n`;
    report += `| Unique Tools | ${tools.length} |\n`;
    report += `| Avg Execution Time | ${avgDuration}ms |\n\n`;

    report += `## TOP 10 TOOLS (by usage)\n\n`;
    report += `| Tool | Executions | Success Rate | Avg Duration |\n`;
    report += `|------|------------|--------------|---------------|\n`;
    for (const tool of topTools) {
      report += `| ${tool.name || 'unknown'} | ${tool.executions} | ${tool.successRate}% | ${tool.avgDuration}ms |\n`;
    }

    if (failureTools.length > 0) {
      report += `\n## TOOLS WITH FAILURES\n\n`;
      report += `| Tool | Failures | Success Rate |\n`;
      report += `|------|----------|---------------|\n`;
      for (const tool of failureTools.slice(0, 10)) {
        report += `| ${tool.name || 'unknown'} | ${tool.failed} | ${tool.successRate}% |\n`;
      }
    }

    report += `\n## INSIGHTS\n\n`;

    if (tools.length > 0) {
      const mostUsed = tools[0];
      report += `- **Most Used:** ${mostUsed.name || 'unknown'} (${mostUsed.executions} executions)\n`;
    }

    if (failureTools.length > 0) {
      const worstReliability = failureTools.find(t => t.executions >= 3) || failureTools[0];
      if (worstReliability) {
        report += `- **Reliability Concern:** ${worstReliability.name || 'unknown'} (${worstReliability.successRate}% success)\n`;
      }
    }

    const slowest = tools.sort((a, b) => b.avgDuration - a.avgDuration)[0];
    if (slowest) {
      report += `- **Slowest:** ${slowest.name || 'unknown'} (${slowest.avgDuration}ms avg)\n`;
    }

    report += `\n## NEXT STEPS\n\n`;
    report += `- Continue normal operations\n`;
    report += `- Monitor for changes in reliability\n`;
    report += `- Note unusual patterns\n`;
    report += `- Collection continues...\n`;

    return report;
  }

  getDateRange() {
    if (this.data.records.length === 0) return 'N/A';

    const timestamps = this.data.records
      .map(r => new Date(r.timestamp))
      .filter(d => !isNaN(d))
      .sort((a, b) => a - b);

    if (timestamps.length < 2) return 'N/A';

    const start = timestamps[0].toISOString().split('T')[0];
    const end = timestamps[timestamps.length - 1].toISOString().split('T')[0];

    return `${start} to ${end}`;
  }

  getCollectionDays() {
    if (this.data.records.length === 0) return '0';

    const timestamps = this.data.records
      .map(r => new Date(r.timestamp).toISOString().split('T')[0])
      .filter((v, i, a) => a.indexOf(v) === i);

    return timestamps.length;
  }

  run() {
    console.log('╔════════════════════════════════════════════════════════╗');
    console.log('║           DAILY INTELLIGENCE REPORT                   ║');
    console.log('║        (Run this daily during 7-day collection)       ║');
    console.log('╚════════════════════════════════════════════════════════╝\n');

    if (!this.loadTelemetry()) {
      console.log('⚠️ No telemetry data found yet.\n');
      console.log('Telemetry will be generated when tools are executed.\n');
      process.exit(0);
    }

    console.log(`✅ Loaded telemetry data\n`);

    this.analyzeTools();

    const report = this.generateReport();

    const filename = 'DAILY-INTELLIGENCE.md';
    fs.writeFileSync(filename, report);

    console.log(report);
    console.log(`\n✅ Report saved to ${filename}\n`);
  }
}

const daily = new DailyReport();
daily.run();
