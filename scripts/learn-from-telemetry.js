#!/usr/bin/env node

// LEARN-FROM-TELEMETRY.js
// Analyzes telemetry to extract learning insights
// Identifies: bottlenecks, patterns, validation candidates

import fs from 'fs';
import path from 'path';

class TelemetryLearning {
  constructor() {
    this.telemetryPath = './telemetry';
    this.knowledgePath = './knowledge';
    this.data = { records: [], insights: [] };
  }

  ensureDirectories() {
    if (!fs.existsSync(this.knowledgePath)) {
      fs.mkdirSync(this.knowledgePath, { recursive: true });
    }
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
        // Silently skip
      }
    }

    return this.data.records.length > 0;
  }

  identifyBottlenecks() {
    const tools = {};

    for (const record of this.data.records) {
      if (!tools[record.toolName]) {
        tools[record.toolName] = {
          executions: 0,
          failures: 0,
          totalTime: 0,
          durations: []
        };
      }

      tools[record.toolName].executions++;
      tools[record.toolName].totalTime += record.duration || 0;
      tools[record.toolName].durations.push(record.duration || 0);
      if (!record.success) {
        tools[record.toolName].failures++;
      }
    }

    // Calculate metrics
    const bottlenecks = [];
    for (const [name, data] of Object.entries(tools)) {
      const durations = data.durations.sort((a, b) => a - b);
      const p95 = durations[Math.floor(durations.length * 0.95)];
      const failureRate = (data.failures / data.executions) * 100;
      const timeWasted = data.failures * (data.totalTime / data.executions);

      if (failureRate > 10 || p95 > 5000) {
        bottlenecks.push({
          tool: name,
          failureRate: Math.round(failureRate * 10) / 10,
          p95Duration: p95,
          timeWasted: Math.round(timeWasted),
          executionCount: data.executions,
          severity: failureRate > 20 ? 'high' : 'medium'
        });
      }
    }

    return bottlenecks.sort((a, b) => b.timeWasted - a.timeWasted);
  }

  identifyWorkflowPatterns() {
    const patterns = {};
    const sorted = this.data.records.sort((a, b) =>
      new Date(a.timestamp) - new Date(b.timestamp)
    );

    // Find tool sequences
    for (let i = 0; i < sorted.length - 1; i++) {
      const current = sorted[i];
      const next = sorted[i + 1];

      const timeDiff = new Date(next.timestamp) - new Date(current.timestamp);
      if (timeDiff < 60000) { // Within 60 seconds
        const sequence = `${current.toolName} → ${next.toolName}`;
        patterns[sequence] = (patterns[sequence] || 0) + 1;
      }
    }

    return Object.entries(patterns)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20)
      .map(([sequence, count]) => ({ sequence, count }));
  }

  identifyValidationCandidates() {
    // Tools with moderate execution count and mixed results
    const tools = {};

    for (const record of this.data.records) {
      if (!tools[record.toolName]) {
        tools[record.toolName] = { executions: 0, failures: 0 };
      }
      tools[record.toolName].executions++;
      if (!record.success) {
        tools[record.toolName].failures++;
      }
    }

    const candidates = [];
    for (const [name, data] of Object.entries(tools)) {
      const failureRate = (data.failures / data.executions) * 100;

      // Candidates: 5-50 executions with 10-50% failure rate
      if (data.executions >= 5 && data.executions <= 50 && failureRate >= 10 && failureRate <= 50) {
        candidates.push({
          tool: name,
          failureRate: Math.round(failureRate * 10) / 10,
          executionCount: data.executions,
          failureCount: data.failures,
          priority: 'medium',
          reason: 'Mixed results - needs human validation'
        });
      }
    }

    return candidates.sort((a, b) => b.failureRate - a.failureRate);
  }

  generateInsightReport() {
    const bottlenecks = this.identifyBottlenecks();
    const patterns = this.identifyWorkflowPatterns();
    const candidates = this.identifyValidationCandidates();

    let report = '# LEARNING INSIGHTS FROM TELEMETRY\n\n';
    report += `**Generated:** ${new Date().toISOString()}\n`;
    report += `**Records Analyzed:** ${this.data.records.length}\n\n`;

    report += '## BOTTLENECKS (High Failure or Slow)\n\n';
    if (bottlenecks.length > 0) {
      report += '| Tool | Failure Rate | P95 Duration | Time Wasted | Severity |\n';
      report += '|------|--------------|--------------|-------------|----------|\n';
      for (const b of bottlenecks) {
        report += `| ${b.tool} | ${b.failureRate}% | ${b.p95Duration}ms | ${b.timeWasted}s | ${b.severity} |\n`;
      }
    } else {
      report += 'No significant bottlenecks detected\n';
    }

    report += '\n## WORKFLOW PATTERNS\n\n';
    if (patterns.length > 0) {
      report += '| Sequence | Count |\n';
      report += '|----------|-------|\n';
      for (const p of patterns) {
        report += `| ${p.sequence} | ${p.count} |\n`;
      }
    } else {
      report += 'No patterns detected\n';
    }

    report += '\n## VALIDATION CANDIDATES\n\n';
    report += 'Tools with mixed results that need human verification:\n\n';
    if (candidates.length > 0) {
      report += '| Tool | Failure Rate | Executions | Failures |\n';
      report += '|------|--------------|------------|----------|\n';
      for (const c of candidates) {
        report += `| ${c.tool} | ${c.failureRate}% | ${c.executionCount} | ${c.failureCount} |\n`;
      }
    } else {
      report += 'No validation candidates\n';
    }

    report += '\n## NEXT STEPS\n\n';
    report += '1. Review validation candidates for false positives\n';
    report += '2. Verify bottleneck tools against context\n';
    report += '3. Document lessons from workflow patterns\n';
    report += '4. Update confidence scores based on findings\n';

    fs.writeFileSync('LEARNING-INSIGHTS.md', report);
    return report;
  }

  run() {
    console.log('╔════════════════════════════════════════════════════════╗');
    console.log('║          TELEMETRY LEARNING ANALYSIS                  ║');
    console.log('║      Identifying patterns and validation needs        ║');
    console.log('╚════════════════════════════════════════════════════════╝\n');

    this.ensureDirectories();

    if (!this.loadTelemetry()) {
      console.log('⚠️ No telemetry data found yet\n');
      process.exit(0);
    }

    console.log(`✅ Loaded ${this.data.records.length} telemetry records\n`);

    const report = this.generateInsightReport();
    console.log(report);
    console.log('\n✅ Insights saved to LEARNING-INSIGHTS.md\n');
  }
}

const learning = new TelemetryLearning();
learning.run();
