// TOOL USAGE DATABASE
// Aggregates telemetry data into usage statistics

const fs = require('fs');
const path = require('path');

class UsageDatabase {
  constructor(telemetryPath = './telemetry') {
    this.telemetryPath = telemetryPath;
  }

  loadAllTelemetry() {
    const files = fs.readdirSync(this.telemetryPath).filter(f => f.startsWith('telemetry-'));
    let allRecords = [];

    for (const file of files) {
      try {
        const data = JSON.parse(fs.readFileSync(path.join(this.telemetryPath, file), 'utf8'));
        allRecords = allRecords.concat(data);
      } catch (e) {
        console.error(`Error reading ${file}:`, e.message);
      }
    }

    return allRecords;
  }

  generateUsageStats() {
    const records = this.loadAllTelemetry();
    const stats = {};

    for (const record of records) {
      if (!stats[record.toolName]) {
        stats[record.toolName] = {
          toolName: record.toolName,
          category: record.metadata.toolCategory,
          priority: record.metadata.toolPriority,
          executions: 0,
          successes: 0,
          failures: 0,
          totalDuration: 0,
          avgDuration: 0,
          failureRate: 0,
          lastUsed: null
        };
      }

      stats[record.toolName].executions++;
      if (record.success) {
        stats[record.toolName].successes++;
      } else {
        stats[record.toolName].failures++;
      }
      stats[record.toolName].totalDuration += record.duration;
      stats[record.toolName].lastUsed = record.timestamp;
    }

    // Calculate derived metrics
    for (const toolName in stats) {
      const tool = stats[toolName];
      tool.avgDuration = Math.round(tool.totalDuration / tool.executions);
      tool.failureRate = Math.round((tool.failures / tool.executions) * 100);
    }

    return stats;
  }

  getRankedByUsage(limit = 95) {
    const stats = this.generateUsageStats();
    return Object.values(stats)
      .sort((a, b) => b.executions - a.executions)
      .slice(0, limit);
  }

  getTopUsed(count = 10) {
    return this.getRankedByUsage().slice(0, count);
  }

  getBottomUsed(count = 10) {
    const all = this.getRankedByUsage();
    return all.slice(-count).reverse();
  }

  getByCategory(category) {
    const stats = this.generateUsageStats();
    return Object.values(stats)
      .filter(s => s.category === category)
      .sort((a, b) => b.executions - a.executions);
  }

  saveDatabase(filename = 'usage-database.json') {
    const data = {
      timestamp: new Date().toISOString(),
      totalRecords: this.loadAllTelemetry().length,
      stats: this.generateUsageStats(),
      topUsed: this.getTopUsed(10),
      bottomUsed: this.getBottomUsed(10),
      byCategory: {
        'Process': this.getByCategory('Process'),
        'Network': this.getByCategory('Network'),
        'Access': this.getByCategory('Access'),
        'Forensics': this.getByCategory('Forensics'),
        'Persistence': this.getByCategory('Persistence'),
        'Hunting': this.getByCategory('Hunting'),
        'Files': this.getByCategory('Files'),
        'System': this.getByCategory('System'),
        'Timeline': this.getByCategory('Timeline'),
        'Security': this.getByCategory('Security')
      }
    };

    fs.writeFileSync(filename, JSON.stringify(data, null, 2));
    return data;
  }
}

module.exports = UsageDatabase;
