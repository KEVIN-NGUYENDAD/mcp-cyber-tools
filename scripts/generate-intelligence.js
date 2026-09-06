#!/usr/bin/env node

// GENERATE-INTELLIGENCE.js
// Analyzes collected telemetry data and produces intelligence reports
// Input: 7 days of telemetry-*.json files
// Output: TOP-TOOLS.md, PERFORMANCE-REPORT.md, RELIABILITY-REPORT.md, WORKFLOW-REPORT.md, EVIDENCE-BASED-ROADMAP.md

import fs from 'fs';
import path from 'path';

class IntelligenceEngine {
  constructor() {
    this.telemetryPath = './telemetry';
    this.data = {
      records: [],
      tools: {},
      workflows: [],
      timestamps: []
    };
  }

  loadTelemetry() {
    if (!fs.existsSync(this.telemetryPath)) {
      console.log('❌ No telemetry directory found');
      return false;
    }

    const files = fs.readdirSync(this.telemetryPath)
      .filter(f => f.startsWith('telemetry-') && f.endsWith('.json'))
      .sort();

    if (files.length === 0) {
      console.log('❌ No telemetry files found');
      return false;
    }

    console.log(`\n📊 Loading telemetry from ${files.length} file(s)...`);

    for (const file of files) {
      try {
        const data = JSON.parse(fs.readFileSync(path.join(this.telemetryPath, file), 'utf8'));
        if (Array.isArray(data)) {
          this.data.records = this.data.records.concat(data);
        }
      } catch (error) {
        console.warn(`⚠️ Failed to parse ${file}`);
      }
    }

    console.log(`✅ Loaded ${this.data.records.length} records`);
    return true;
  }

  analyzeToolUsage() {
    const tools = {};

    for (const record of this.data.records) {
      if (!tools[record.toolName]) {
        tools[record.toolName] = {
          name: record.toolName,
          executionCount: 0,
          successCount: 0,
          failureCount: 0,
          totalDuration: 0,
          minDuration: Infinity,
          maxDuration: 0,
          category: record.metadata?.toolCategory || 'Unknown'
        };
      }

      const tool = tools[record.toolName];
      tool.executionCount++;
      tool.totalDuration += record.duration || 0;
      tool.minDuration = Math.min(tool.minDuration, record.duration || 0);
      tool.maxDuration = Math.max(tool.maxDuration, record.duration || 0);

      if (record.success) {
        tool.successCount++;
      } else {
        tool.failureCount++;
      }
    }

    // Calculate averages and rates
    for (const tool of Object.values(tools)) {
      tool.avgDuration = Math.round(tool.totalDuration / tool.executionCount);
      tool.successRate = Math.round((tool.successCount / tool.executionCount) * 100);
      tool.reliabilityScore = tool.successRate; // For ranking
    }

    this.data.tools = tools;
    return tools;
  }

  generateTopToolsReport() {
    const tools = Object.values(this.data.tools);
    const byUsage = tools.sort((a, b) => b.executionCount - a.executionCount);
    const byReliability = tools.sort((a, b) => b.successRate - a.successRate);

    let report = '# TOP TOOLS REPORT\n\n';
    report += `**Generated:** ${new Date().toISOString()}\n`;
    report += `**Total Records:** ${this.data.records.length}\n`;
    report += `**Unique Tools:** ${tools.length}\n`;
    report += `**Collection Period:** 7 days\n\n`;

    report += '## TOP 10 BY USAGE\n\n';
    report += '| Tool | Executions | Success Rate | Avg Duration |\n';
    report += '|------|------------|--------------|---------------|\n';
    for (const tool of byUsage.slice(0, 10)) {
      report += `| ${tool.name} | ${tool.executionCount} | ${tool.successRate}% | ${tool.avgDuration}ms |\n`;
    }

    report += '\n## BOTTOM 10 BY USAGE\n\n';
    report += '| Tool | Executions | Success Rate | Avg Duration |\n';
    report += '|------|------------|--------------|---------------|\n';
    for (const tool of byUsage.slice(-10).reverse()) {
      report += `| ${tool.name} | ${tool.executionCount} | ${tool.successRate}% | ${tool.avgDuration}ms |\n`;
    }

    report += '\n## MOST RELIABLE\n\n';
    report += '| Tool | Success Rate | Executions |\n';
    report += '|------|--------------|-------------|\n';
    for (const tool of byReliability.filter(t => t.executionCount >= 5).slice(0, 10)) {
      report += `| ${tool.name} | ${tool.successRate}% | ${tool.executionCount} |\n`;
    }

    report += '\n## LEAST RELIABLE\n\n';
    report += '| Tool | Success Rate | Executions | Failures |\n';
    report += '|------|--------------|-------------|----------|\n';
    for (const tool of byReliability.filter(t => t.executionCount >= 5).slice(-10).reverse()) {
      report += `| ${tool.name} | ${tool.successRate}% | ${tool.executionCount} | ${tool.failureCount} |\n`;
    }

    fs.writeFileSync('TOP-TOOLS.md', report);
    return report;
  }

  generatePerformanceReport() {
    const tools = Object.values(this.data.tools);
    const fastest = tools.sort((a, b) => a.avgDuration - b.avgDuration);
    const slowest = tools.sort((a, b) => b.avgDuration - a.avgDuration);
    const allDurations = this.data.records.map(r => r.duration || 0).sort((a, b) => a - b);
    const p50 = allDurations[Math.floor(allDurations.length * 0.5)];
    const p95 = allDurations[Math.floor(allDurations.length * 0.95)];
    const p99 = allDurations[Math.floor(allDurations.length * 0.99)];

    let report = '# PERFORMANCE REPORT\n\n';
    report += `**Generated:** ${new Date().toISOString()}\n`;
    report += `**Total Executions:** ${this.data.records.length}\n`;
    report += `**Unique Tools:** ${tools.length}\n\n`;

    report += '## OVERALL PERFORMANCE\n\n';
    report += `| Metric | Value |\n`;
    report += `|--------|-------|\n`;
    report += `| P50 Latency | ${p50}ms |\n`;
    report += `| P95 Latency | ${p95}ms |\n`;
    report += `| P99 Latency | ${p99}ms |\n`;

    report += '\n## FASTEST 10 TOOLS\n\n';
    report += '| Tool | Avg Duration | P95 Duration | Executions |\n';
    report += '|------|--------------|--------------|-------------|\n';
    for (const tool of fastest.slice(0, 10)) {
      const toolRecords = this.data.records.filter(r => r.toolName === tool.name);
      const durations = toolRecords.map(r => r.duration || 0).sort((a, b) => a - b);
      const p95 = durations[Math.floor(durations.length * 0.95)];
      report += `| ${tool.name} | ${tool.avgDuration}ms | ${p95}ms | ${tool.executionCount} |\n`;
    }

    report += '\n## SLOWEST 10 TOOLS\n\n';
    report += '| Tool | Avg Duration | P95 Duration | Executions |\n';
    report += '|------|--------------|--------------|-------------|\n';
    for (const tool of slowest.slice(0, 10)) {
      const toolRecords = this.data.records.filter(r => r.toolName === tool.name);
      const durations = toolRecords.map(r => r.duration || 0).sort((a, b) => a - b);
      const p95 = durations[Math.floor(durations.length * 0.95)];
      report += `| ${tool.name} | ${tool.avgDuration}ms | ${p95}ms | ${tool.executionCount} |\n`;
    }

    fs.writeFileSync('PERFORMANCE-REPORT.md', report);
    return report;
  }

  generateReliabilityReport() {
    const tools = Object.values(this.data.tools);
    const byReliability = tools.sort((a, b) => a.successRate - b.successRate);

    let report = '# RELIABILITY REPORT\n\n';
    report += `**Generated:** ${new Date().toISOString()}\n`;
    report += `**Total Executions:** ${this.data.records.length}\n`;
    report += `**Overall Success Rate:** ${Math.round((this.data.records.filter(r => r.success).length / this.data.records.length) * 100)}%\n\n`;

    report += '## SUCCESS RATES BY TOOL\n\n';
    report += '| Tool | Success Rate | Failures | Executions |\n';
    report += '|------|--------------|----------|-------------|\n';
    for (const tool of byReliability) {
      report += `| ${tool.name} | ${tool.successRate}% | ${tool.failureCount} | ${tool.executionCount} |\n`;
    }

    report += '\n## MOST UNRELIABLE (5+ executions)\n\n';
    const problematic = byReliability.filter(t => t.executionCount >= 5 && t.successRate < 95);
    if (problematic.length > 0) {
      report += '| Tool | Success Rate | Impact |\n';
      report += '|------|--------------|--------|\n';
      for (const tool of problematic.slice(0, 10)) {
        const impact = tool.executionCount * (100 - tool.successRate) / 100;
        report += `| ${tool.name} | ${tool.successRate}% | ${Math.round(impact)} failed runs |\n`;
      }
    } else {
      report += 'All tools with 5+ executions have >95% success rate\n';
    }

    fs.writeFileSync('RELIABILITY-REPORT.md', report);
    return report;
  }

  generateWorkflowReport() {
    let report = '# WORKFLOW REPORT\n\n';
    report += `**Generated:** ${new Date().toISOString()}\n`;
    report += `**Total Executions:** ${this.data.records.length}\n\n`;

    // Analyze tool sequences
    const sequences = {};
    const sortedRecords = this.data.records.sort((a, b) =>
      new Date(a.timestamp) - new Date(b.timestamp)
    );

    for (let i = 0; i < sortedRecords.length - 1; i++) {
      const current = sortedRecords[i];
      const next = sortedRecords[i + 1];

      // Only count as sequence if within 60 seconds
      const timeDiff = new Date(next.timestamp) - new Date(current.timestamp);
      if (timeDiff < 60000) {
        const pair = `${current.toolName} → ${next.toolName}`;
        sequences[pair] = (sequences[pair] || 0) + 1;
      }
    }

    // Sort by frequency
    const topSequences = Object.entries(sequences)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20);

    report += '## COMMON TOOL SEQUENCES (within 60 seconds)\n\n';
    if (topSequences.length > 0) {
      report += '| Sequence | Count |\n';
      report += '|----------|-------|\n';
      for (const [sequence, count] of topSequences) {
        report += `| ${sequence} | ${count} |\n`;
      }
    } else {
      report += 'No common sequences detected\n';
    }

    // Category analysis
    report += '\n## EXECUTIONS BY CATEGORY\n\n';
    const byCategory = {};
    for (const tool of Object.values(this.data.tools)) {
      const cat = tool.category || 'Unknown';
      if (!byCategory[cat]) {
        byCategory[cat] = { count: 0, success: 0, tools: [] };
      }
      byCategory[cat].count += tool.executionCount;
      byCategory[cat].success += tool.successCount;
      byCategory[cat].tools.push(tool.name);
    }

    report += '| Category | Tools | Executions | Success Rate |\n';
    report += '|----------|-------|------------|---------------|\n';
    for (const [cat, data] of Object.entries(byCategory).sort((a, b) => b[1].count - a[1].count)) {
      const rate = Math.round((data.success / data.count) * 100);
      report += `| ${cat} | ${data.tools.length} | ${data.count} | ${rate}% |\n`;
    }

    fs.writeFileSync('WORKFLOW-REPORT.md', report);
    return report;
  }

  generateEvidenceRoadmap() {
    const tools = Object.values(this.data.tools);
    const byUsage = tools.sort((a, b) => b.executionCount - a.executionCount);
    const unreliable = tools.filter(t => t.successRate < 90 && t.executionCount >= 5);

    let report = '# EVIDENCE-BASED ROADMAP\n\n';
    report += `**Generated:** ${new Date().toISOString()}\n`;
    report += `**Data Period:** 7 days\n`;
    report += `**Total Executions:** ${this.data.records.length}\n\n`;

    report += '## EVIDENCE\n\n';
    report += '### Q1: Which 10 tools create most value?\n\n';
    report += 'Based on execution frequency (analyst time spent):\n\n';
    for (let i = 0; i < Math.min(10, byUsage.length); i++) {
      const tool = byUsage[i];
      report += `${i+1}. **${tool.name}** (${tool.executionCount} executions, ${tool.successRate}% success)\n`;
    }

    report += '\n### Q2: Which 10 tools nobody uses?\n\n';
    const unused = byUsage.filter(t => t.executionCount <= 2).slice(-10);
    if (unused.length > 0) {
      for (let i = 0; i < unused.length; i++) {
        const tool = unused[i];
        report += `${i+1}. **${tool.name}** (${tool.executionCount} executions)\n`;
      }
    } else {
      report += 'All tools have >2 executions\n';
    }

    report += '\n### Q3: Which tool fails most?\n\n';
    const mostFailures = tools.filter(t => t.failureCount > 0).sort((a, b) => b.failureCount - a.failureCount)[0];
    if (mostFailures) {
      report += `**${mostFailures.name}**: ${mostFailures.failureCount} failures (${100-mostFailures.successRate}% failure rate)\n`;
    }

    report += '\n### Q4: Which tool wastes most time?\n\n';
    const slowest = tools.filter(t => t.executionCount >= 5).sort((a, b) => (b.avgDuration * b.executionCount) - (a.avgDuration * a.executionCount))[0];
    if (slowest) {
      report += `**${slowest.name}**: ${slowest.avgDuration}ms × ${slowest.executionCount} executions = ${Math.round(slowest.avgDuration * slowest.executionCount / 1000)}s total\n`;
    }

    report += '\n### Q5: Which improvement would save most analyst time?\n\n';
    if (unreliable.length > 0) {
      const target = unreliable.sort((a, b) => (b.executionCount * (100 - b.successRate)) - (a.executionCount * (100 - a.successRate)))[0];
      const failureCount = Math.round(target.executionCount * (100 - target.successRate) / 100);
      const timePerFailure = 5; // minutes
      const totalTime = failureCount * timePerFailure;

      report += `**Fix ${target.name}** (current success rate: ${target.successRate}%)\n`;
      report += `- Current failures: ${failureCount} per period\n`;
      report += `- Time lost per failure: ~${timePerFailure} minutes (investigation + retry)\n`;
      report += `- Total time wasted: ~${totalTime} minutes (${Math.round(totalTime/60)} hours) per period\n`;
      report += `- If fixed to 99% success: Save ${Math.round(failureCount * 0.9 * timePerFailure / 60)} hours per period\n`;
    }

    report += '\n## RECOMMENDED NEXT STEPS\n\n';
    report += '1. Create IC to improve reliability of top failure sources\n';
    report += '2. Consider removing tools with <3 lifetime executions\n';
    report += '3. Optimize slowest tools used in frequent sequences\n';
    report += '4. Focus on tools in hot workflows\n';

    fs.writeFileSync('EVIDENCE-BASED-ROADMAP.md', report);
    return report;
  }

  run() {
    console.log('╔════════════════════════════════════════════════════════╗');
    console.log('║         INTELLIGENCE GENERATION ENGINE                ║');
    console.log('║    Analyzing 7 Days of Collected Telemetry Data       ║');
    console.log('╚════════════════════════════════════════════════════════╝');

    if (!this.loadTelemetry()) {
      console.log('\n❌ Cannot proceed without telemetry data');
      console.log('Deploy cyber-tools and collect data for 7 days first');
      process.exit(1);
    }

    console.log('\n📊 Analyzing tool usage...');
    this.analyzeToolUsage();

    console.log('📝 Generating TOP-TOOLS.md...');
    this.generateTopToolsReport();

    console.log('📈 Generating PERFORMANCE-REPORT.md...');
    this.generatePerformanceReport();

    console.log('🛡️ Generating RELIABILITY-REPORT.md...');
    this.generateReliabilityReport();

    console.log('🔄 Generating WORKFLOW-REPORT.md...');
    this.generateWorkflowReport();

    console.log('🎯 Generating EVIDENCE-BASED-ROADMAP.md...');
    this.generateEvidenceRoadmap();

    console.log('\n✅ Intelligence generation complete\n');
    console.log('Generated reports:');
    console.log('  - TOP-TOOLS.md');
    console.log('  - PERFORMANCE-REPORT.md');
    console.log('  - RELIABILITY-REPORT.md');
    console.log('  - WORKFLOW-REPORT.md');
    console.log('  - EVIDENCE-BASED-ROADMAP.md\n');
  }
}

const engine = new IntelligenceEngine();
engine.run();
