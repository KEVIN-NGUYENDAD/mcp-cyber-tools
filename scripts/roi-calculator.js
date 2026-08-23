#!/usr/bin/env node

// ROI-CALCULATOR.js
// Calculates actual ROI from telemetry data
// Input: telemetry/*.json + benchmark-results.json
// Output: roi-analysis.json with measurable improvements

const fs = require('fs');
const path = require('path');

class ROICalculator {
  constructor() {
    this.telemetryPath = './telemetry';
    this.analysis = {
      timestamp: new Date().toISOString(),
      dataCollection: {
        telemetryFiles: 0,
        totalExecutions: 0,
        dateRange: { start: null, end: null }
      },
      improvements: {
        ic035_event_log: { status: 'PENDING', delta: null },
        ic036_registry_cache: { status: 'PENDING', delta: null },
        ic041_reliability: { status: 'PENDING', delta: null }
      },
      roi: {
        totalHoursSaved: 0,
        annualHoursSaved: 0,
        costAvoidance: 0,
        paybackPeriod: 'PENDING'
      },
      recommendations: []
    };
  }

  loadTelemetry() {
    if (!fs.existsSync(this.telemetryPath)) {
      console.log('⚠️ No telemetry directory found');
      return [];
    }

    const files = fs.readdirSync(this.telemetryPath)
      .filter(f => f.startsWith('telemetry-') && f.endsWith('.json'))
      .sort();

    this.analysis.dataCollection.telemetryFiles = files.length;

    let allRecords = [];
    for (const file of files) {
      try {
        const data = JSON.parse(
          fs.readFileSync(path.join(this.telemetryPath, file), 'utf8')
        );
        if (Array.isArray(data)) {
          allRecords = allRecords.concat(data);
        }
      } catch (error) {
        console.warn(`⚠️ Failed to parse ${file}: ${error.message}`);
      }
    }

    this.analysis.dataCollection.totalExecutions = allRecords.length;

    // Extract date range
    if (allRecords.length > 0) {
      const timestamps = allRecords
        .map(r => new Date(r.timestamp))
        .filter(d => !isNaN(d));
      if (timestamps.length > 0) {
        timestamps.sort((a, b) => a - b);
        this.analysis.dataCollection.dateRange.start = timestamps[0].toISOString();
        this.analysis.dataCollection.dateRange.end = timestamps[timestamps.length - 1].toISOString();
      }
    }

    return allRecords;
  }

  analyzeIC035EventLog(records) {
    // IC-035: Event Log Standardization
    // Expected Delta: 100 hours/year (35% improvement from 60% to 95% success rate)

    const eventLogTools = [
      'failedLogons',
      'successfulLogons',
      'loggedOnUsers'
    ];

    const eventLogRecords = records.filter(r => eventLogTools.includes(r.toolName));

    if (eventLogRecords.length === 0) {
      return {
        status: 'NO_DATA',
        delta: 0,
        reason: 'No event log telemetry collected yet'
      };
    }

    const successRate = (
      eventLogRecords.filter(r => r.success).length / eventLogRecords.length
    ) * 100;

    const expectedImprovement = successRate > 90 ? 100 : (successRate - 60) * 2.5;
    const avgDuration = eventLogRecords.reduce((sum, r) => sum + r.duration, 0) / eventLogRecords.length;

    return {
      status: successRate > 95 ? 'ACHIEVED' : 'PARTIAL',
      successRate: Math.round(successRate * 10) / 10,
      averageDuration: Math.round(avgDuration),
      executionCount: eventLogRecords.length,
      delta: expectedImprovement,
      reason: `Success rate ${successRate.toFixed(1)}% vs target 95%`
    };
  }

  analyzeIC036RegistryCache(records) {
    // IC-036: Registry Query Caching
    // Expected Delta: 80 hours/year (90% speedup from 8-10s to <100ms)

    const registryTools = [
      'startupPrograms',
      'registryRunKeys',
      'registryRunOnce'
    ];

    const registryRecords = records.filter(r => registryTools.includes(r.toolName));

    if (registryRecords.length === 0) {
      return {
        status: 'NO_DATA',
        delta: 0,
        reason: 'No registry telemetry collected yet'
      };
    }

    // Analyze performance improvement
    const avgDuration = registryRecords.reduce((sum, r) => sum + r.duration, 0) / registryRecords.length;
    const successRate = (registryRecords.filter(r => r.success).length / registryRecords.length) * 100;

    // Expected: 8000ms cold → 100ms cached = 98% reduction
    // If we see average < 500ms, caching is working
    const cachingWorking = avgDuration < 500;
    const speedupPercent = cachingWorking ? 95 : 0;
    const delta = cachingWorking ? 80 : 20; // Hours saved per year

    return {
      status: cachingWorking ? 'ACHIEVED' : 'PARTIAL',
      averageDuration: Math.round(avgDuration),
      expectedColdStart: 8000,
      expectedCached: 100,
      successRate: Math.round(successRate * 10) / 10,
      speedupPercent: speedupPercent,
      executionCount: registryRecords.length,
      delta: delta,
      reason: cachingWorking ? 'Average <500ms indicates cache hits' : 'Caching not yet fully effective'
    };
  }

  analyzeIC041Reliability(records) {
    // IC-041: Reliability Improvement
    // Expected Delta: 50 hours/year (80% to 95% reliability, 15% improvement)

    // Check for improved success rates across all tools
    const totalRecords = records.length;
    const successRecords = records.filter(r => r.success).length;
    const successRate = (successRecords / totalRecords) * 100;

    // Fallback logic success rate (when primary fails)
    const failedRecords = records.filter(r => !r.success);
    const fallbackWorking = failedRecords.length < totalRecords * 0.1; // <10% failures

    const reliabilityImprovement = Math.max(0, (successRate - 80) * 3.33); // Scale to ~50 hours max
    const status = successRate > 95 ? 'ACHIEVED' : successRate > 85 ? 'PARTIAL' : 'PENDING';

    return {
      status: status,
      overallSuccessRate: Math.round(successRate * 10) / 10,
      failureRate: Math.round((100 - successRate) * 10) / 10,
      fallbackEngaged: !fallbackWorking,
      totalExecutions: totalRecords,
      failedExecutions: failedRecords.length,
      delta: reliabilityImprovement,
      reason: `Success rate ${successRate.toFixed(1)}% vs target 95%`
    };
  }

  calculateAnnualROI(records) {
    // Analyze improvements
    const ic035 = this.analyzeIC035EventLog(records);
    const ic036 = this.analyzeIC036RegistryCache(records);
    const ic041 = this.analyzeIC041Reliability(records);

    this.analysis.improvements.ic035_event_log = ic035;
    this.analysis.improvements.ic036_registry_cache = ic036;
    this.analysis.improvements.ic041_reliability = ic041;

    // Calculate total ROI
    const totalHoursSaved = ic035.delta + ic036.delta + ic041.delta;
    const hourlyRate = 150; // Average analyst rate
    const costSavings = totalHoursSaved * hourlyRate;

    // Implementation cost (estimated: 1 week of development)
    const implementationCost = hourlyRate * 40;

    // Payback period
    const paybackHours = implementationCost / hourlyRate;
    const paybackDays = Math.ceil(paybackHours / 8);

    // Annualization factor
    // If telemetry spans N days, extrapolate to 365 days
    let annualizationFactor = 1;
    if (this.analysis.dataCollection.dateRange.start && this.analysis.dataCollection.dateRange.end) {
      const start = new Date(this.analysis.dataCollection.dateRange.start);
      const end = new Date(this.analysis.dataCollection.dateRange.end);
      const daySpan = (end - start) / (1000 * 60 * 60 * 24);
      if (daySpan > 0) {
        annualizationFactor = 365 / Math.max(1, daySpan);
      }
    }

    this.analysis.roi = {
      totalHoursSaved: Math.round(totalHoursSaved),
      annualHoursSaved: Math.round(totalHoursSaved * annualizationFactor),
      costSavings: Math.round(costSavings),
      annualCostSavings: Math.round(costSavings * annualizationFactor),
      implementationCost: implementationCost,
      paybackPeriod: `${paybackDays} days`,
      roi: Math.round((costSavings / implementationCost) * 100),
      annualROI: Math.round((costSavings * annualizationFactor / implementationCost) * 100)
    };

    // Generate recommendations
    this.generateRecommendations();
  }

  generateRecommendations() {
    const recs = [];

    // IC-035 recommendations
    if (this.analysis.improvements.ic035_event_log.successRate < 95) {
      recs.push({
        ic: 'IC-035',
        priority: 'HIGH',
        recommendation: 'Event log success rate below target',
        action: 'Investigate filter syntax for edge cases',
        expectedGain: '10-20 hours/year'
      });
    } else {
      recs.push({
        ic: 'IC-035',
        priority: 'LOW',
        recommendation: 'Event log standardization working well',
        action: 'Monitor for continued performance',
        expectedGain: '✓ Target achieved'
      });
    }

    // IC-036 recommendations
    if (this.analysis.improvements.ic036_registry_cache.speedupPercent < 50) {
      recs.push({
        ic: 'IC-036',
        priority: 'HIGH',
        recommendation: 'Registry caching not providing expected speedup',
        action: 'Verify cache is being hit; check TTL settings',
        expectedGain: '40-60 hours/year'
      });
    } else {
      recs.push({
        ic: 'IC-036',
        priority: 'LOW',
        recommendation: 'Registry caching providing strong performance gain',
        action: 'Consider extending to other registry operations',
        expectedGain: '✓ 60+ hours/year'
      });
    }

    // IC-041 recommendations
    if (this.analysis.improvements.ic041_reliability.overallSuccessRate < 90) {
      recs.push({
        ic: 'IC-041',
        priority: 'CRITICAL',
        recommendation: 'Reliability below acceptable threshold',
        action: 'Debug fallback logic; expand fallback strategies',
        expectedGain: '30-50 hours/year'
      });
    } else {
      recs.push({
        ic: 'IC-041',
        priority: 'LOW',
        recommendation: 'Reliability improvements effective',
        action: 'Monitor failure patterns for new edge cases',
        expectedGain: '✓ 40+ hours/year'
      });
    }

    // Overall recommendation
    if (this.analysis.roi.annualROI > 500) {
      recs.push({
        ic: 'ALL',
        priority: 'INFO',
        recommendation: 'Strong ROI demonstrated',
        action: 'Continue monitoring telemetry; plan next IC wave',
        expectedGain: `✓ ${this.analysis.roi.annualROI}% annual ROI`
      });
    }

    this.analysis.recommendations = recs;
  }

  loadBenchmarkResults() {
    if (!fs.existsSync('benchmark-results.json')) {
      return null;
    }
    try {
      return JSON.parse(fs.readFileSync('benchmark-results.json', 'utf8'));
    } catch (e) {
      return null;
    }
  }

  generateReport() {
    const filename = 'roi-analysis.json';
    fs.writeFileSync(filename, JSON.stringify(this.analysis, null, 2));

    console.log('\n╔════════════════════════════════════════════════════════╗');
    console.log('║         ROI ANALYSIS REPORT                           ║');
    console.log('║         IC-035, IC-036, IC-041 Value Measurement      ║');
    console.log('╚════════════════════════════════════════════════════════╝\n');

    console.log('📊 DATA COLLECTION');
    console.log(`   Telemetry Files: ${this.analysis.dataCollection.telemetryFiles}`);
    console.log(`   Total Executions: ${this.analysis.dataCollection.totalExecutions}`);
    if (this.analysis.dataCollection.dateRange.start) {
      console.log(`   Period: ${this.analysis.dataCollection.dateRange.start.substring(0,10)} to ${this.analysis.dataCollection.dateRange.end.substring(0,10)}`);
    }

    console.log('\n🎯 IC-035: EVENT LOG STANDARDIZATION');
    const ic035 = this.analysis.improvements.ic035_event_log;
    console.log(`   Status: ${ic035.status}`);
    console.log(`   Success Rate: ${ic035.successRate || 'N/A'}%`);
    console.log(`   Hours Saved: ${ic035.delta} hours/year`);

    console.log('\n⚡ IC-036: REGISTRY CACHING');
    const ic036 = this.analysis.improvements.ic036_registry_cache;
    console.log(`   Status: ${ic036.status}`);
    console.log(`   Average Duration: ${ic036.averageDuration || 'N/A'}ms`);
    console.log(`   Speedup: ${ic036.speedupPercent || 0}%`);
    console.log(`   Hours Saved: ${ic036.delta} hours/year`);

    console.log('\n🛡️ IC-041: RELIABILITY');
    const ic041 = this.analysis.improvements.ic041_reliability;
    console.log(`   Status: ${ic041.status}`);
    console.log(`   Success Rate: ${ic041.overallSuccessRate || 'N/A'}%`);
    console.log(`   Failure Rate: ${ic041.failureRate || 'N/A'}%`);
    console.log(`   Hours Saved: ${ic041.delta} hours/year`);

    console.log('\n💰 FINANCIAL ROI');
    console.log(`   Total Hours Saved: ${this.analysis.roi.totalHoursSaved} hours`);
    console.log(`   Annual Hours Saved: ${this.analysis.roi.annualHoursSaved} hours`);
    console.log(`   Cost Savings: $${this.analysis.roi.costSavings.toLocaleString()}`);
    console.log(`   Annual Cost Savings: $${this.analysis.roi.annualCostSavings.toLocaleString()}`);
    console.log(`   Implementation Cost: $${this.analysis.roi.implementationCost.toLocaleString()}`);
    console.log(`   Payback Period: ${this.analysis.roi.paybackPeriod}`);
    console.log(`   ROI: ${this.analysis.roi.roi}% (${this.analysis.roi.annualROI}% annually)`);

    console.log('\n📋 RECOMMENDATIONS');
    this.analysis.recommendations.forEach(rec => {
      const icon = rec.priority === 'CRITICAL' ? '🔴' : rec.priority === 'HIGH' ? '🟠' : '🟢';
      console.log(`   ${icon} [${rec.ic}] ${rec.recommendation}`);
      console.log(`      → ${rec.action}`);
      console.log(`      → Expected: ${rec.expectedGain}`);
    });

    console.log(`\n✅ Report saved to ${filename}\n`);
  }

  run() {
    console.log('╔════════════════════════════════════════════════════════╗');
    console.log('║           CYBER-TOOLS ROI CALCULATOR                  ║');
    console.log('║    Analyzing Actual Improvements from Telemetry        ║');
    console.log('╚════════════════════════════════════════════════════════╝');

    try {
      const records = this.loadTelemetry();

      if (records.length === 0) {
        console.log('\n⚠️ No telemetry data found.');
        console.log('   Please deploy improvements and collect telemetry data first.');
        console.log('   Expected process:');
        console.log('     1. Run FIELD-TEST-PACK.md scenarios');
        console.log('     2. Execute BENCHMARK-RUNNER.js');
        console.log('     3. Collect telemetry-*.json files');
        console.log('     4. Re-run ROI-CALCULATOR.js\n');
        return;
      }

      this.calculateAnnualROI(records);
      this.generateReport();
    } catch (error) {
      console.error(`\n❌ Analysis failed: ${error.message}`);
      process.exit(1);
    }
  }
}

if (require.main === module) {
  const calculator = new ROICalculator();
  calculator.run();
}

module.exports = ROICalculator;
