#!/usr/bin/env node

// TELEMETRY-VALIDATOR.js
// Validates telemetry data integrity and quality

const fs = require('fs');
const path = require('path');

class TelemetryValidator {
  constructor(telemetryPath = './telemetry') {
    this.telemetryPath = telemetryPath;
    this.report = {
      timestamp: new Date().toISOString(),
      validation: {
        fileCount: 0,
        recordCount: 0,
        schemaValid: 0,
        schemaInvalid: 0,
        missingFields: [],
        corruptEntries: [],
        eventCounts: {},
        warnings: []
      }
    };
  }

  validateSchema(record, index) {
    const required = ['timestamp', 'toolName', 'startTime', 'duration', 'success'];
    const missing = required.filter(field => !(field in record));

    if (missing.length > 0) {
      this.report.validation.schemaInvalid++;
      this.report.validation.missingFields.push({
        file: record.file,
        record: index,
        missing
      });
      return false;
    }

    // Validate types
    if (typeof record.duration !== 'number' || record.duration < 0) {
      this.report.validation.corruptEntries.push({
        file: record.file,
        record: index,
        issue: 'Invalid duration (should be positive number)'
      });
      return false;
    }

    if (typeof record.success !== 'boolean') {
      this.report.validation.corruptEntries.push({
        file: record.file,
        record: index,
        issue: 'Invalid success (should be boolean)'
      });
      return false;
    }

    this.report.validation.schemaValid++;
    return true;
  }

  validateFiles() {
    if (!fs.existsSync(this.telemetryPath)) {
      console.log(`❌ Telemetry directory not found: ${this.telemetryPath}`);
      return false;
    }

    const files = fs.readdirSync(this.telemetryPath)
      .filter(f => f.startsWith('telemetry-') && f.endsWith('.json'));

    if (files.length === 0) {
      console.log('⚠️ No telemetry files found');
      this.report.validation.warnings.push('No telemetry data collected');
      return true; // Not an error, just no data yet
    }

    this.report.validation.fileCount = files.length;

    for (const file of files) {
      try {
        const data = JSON.parse(fs.readFileSync(path.join(this.telemetryPath, file), 'utf8'));

        if (!Array.isArray(data)) {
          this.report.validation.corruptEntries.push({
            file,
            issue: 'File should contain array of records'
          });
          continue;
        }

        for (let i = 0; i < data.length; i++) {
          data[i].file = file; // Add file context
          this.validateSchema(data[i], i);

          this.report.validation.recordCount++;

          // Track event counts
          const toolName = data[i].toolName;
          if (!this.report.validation.eventCounts[toolName]) {
            this.report.validation.eventCounts[toolName] = { total: 0, success: 0, failed: 0 };
          }
          this.report.validation.eventCounts[toolName].total++;
          if (data[i].success) {
            this.report.validation.eventCounts[toolName].success++;
          } else {
            this.report.validation.eventCounts[toolName].failed++;
          }
        }
      } catch (error) {
        this.report.validation.corruptEntries.push({
          file,
          issue: `Invalid JSON: ${error.message}`
        });
      }
    }

    return true;
  }

  generateReport() {
    const filename = 'telemetry-health-report.json';
    fs.writeFileSync(filename, JSON.stringify(this.report, null, 2));

    console.log('\n╔════════════════════════════════════════════════════════╗');
    console.log('║         TELEMETRY VALIDATION REPORT                   ║');
    console.log('╚════════════════════════════════════════════════════════╝\n');

    console.log(`📊 Files Found: ${this.report.validation.fileCount}`);
    console.log(`📝 Total Records: ${this.report.validation.recordCount}`);
    console.log(`✅ Valid Records: ${this.report.validation.schemaValid}`);
    console.log(`❌ Invalid Records: ${this.report.validation.schemaInvalid}`);

    if (this.report.validation.missingFields.length > 0) {
      console.log(`\n⚠️ Missing Fields Found:`);
      this.report.validation.missingFields.slice(0, 5).forEach(entry => {
        console.log(`   ${entry.file} (record ${entry.record}): ${entry.missing.join(', ')}`);
      });
    }

    if (this.report.validation.corruptEntries.length > 0) {
      console.log(`\n⚠️ Corrupt Entries Found:`);
      this.report.validation.corruptEntries.slice(0, 5).forEach(entry => {
        console.log(`   ${entry.file} (record ${entry.record}): ${entry.issue}`);
      });
    }

    console.log(`\n📈 Event Counts by Tool:`);
    const sorted = Object.entries(this.report.validation.eventCounts)
      .sort((a, b) => b[1].total - a[1].total);

    sorted.slice(0, 10).forEach(([tool, counts]) => {
      const successRate = ((counts.success / counts.total) * 100).toFixed(1);
      console.log(`   ${tool}: ${counts.total} total (${successRate}% success)`);
    });

    if (this.report.validation.warnings.length > 0) {
      console.log(`\n⚠️ Warnings:`);
      this.report.validation.warnings.forEach(w => console.log(`   - ${w}`));
    }

    console.log(`\n✅ Report saved to ${filename}\n`);
    return this.report;
  }

  run() {
    this.validateFiles();
    this.generateReport();
  }
}

if (require.main === module) {
  const validator = new TelemetryValidator();
  validator.run();
}

module.exports = TelemetryValidator;
