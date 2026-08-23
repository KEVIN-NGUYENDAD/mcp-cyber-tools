// CYBER-TOOLS TELEMETRY SYSTEM
// Records every tool execution with full context

import fs from 'fs';
import path from 'path';

class TelemetryEngine {
  constructor(telemetryPath = './telemetry') {
    this.telemetryPath = telemetryPath;
    this.ensureDirectory();
  }

  ensureDirectory() {
    if (!fs.existsSync(this.telemetryPath)) {
      fs.mkdirSync(this.telemetryPath, { recursive: true });
    }
  }

  recordExecution(toolName, context = {}) {
    const record = {
      timestamp: new Date().toISOString(),
      toolName: toolName,
      startTime: Date.now(),
      duration: null,
      success: null,
      errorMessage: null,
      errorCode: null,
      executionContext: {
        userId: process.env.USERNAME || 'unknown',
        systemInfo: process.platform,
        nodeVersion: process.version,
        ...context
      },
      metadata: {
        toolCategory: this.categorizeToolByName(toolName),
        toolPriority: this.getPriorityByName(toolName)
      }
    };

    return {
      recordId: `${toolName}-${record.timestamp.replace(/[:.]/g, '-')}`,
      record: record,
      complete: (success, error = null) => {
        record.duration = Date.now() - record.startTime;
        record.success = success;
        if (!success && error) {
          record.errorMessage = error.message;
          record.errorCode = error.code;
        }
        this.saveRecord(record);
        return record;
      }
    };
  }

  saveRecord(record) {
    const dateKey = record.timestamp.split('T')[0];
    const dailyFile = path.join(this.telemetryPath, `telemetry-${dateKey}.json`);

    let records = [];
    if (fs.existsSync(dailyFile)) {
      try {
        records = JSON.parse(fs.readFileSync(dailyFile, 'utf8'));
      } catch (e) {
        records = [];
      }
    }

    records.push(record);
    fs.writeFileSync(dailyFile, JSON.stringify(records, null, 2));
  }

  categorizeToolByName(toolName) {
    const categories = {
      'running': 'Process',
      'process': 'Process',
      'firewall': 'Network',
      'local': 'Access',
      'user': 'Access',
      'event': 'Forensics',
      'registry': 'Persistence',
      'scheduled': 'Persistence',
      'startup': 'Persistence',
      'service': 'Persistence',
      'wmi': 'Persistence',
      'hunt': 'Hunting',
      'file': 'Files',
      'system': 'System',
      'timeline': 'Timeline',
      'defender': 'Security'
    };

    for (const [key, category] of Object.entries(categories)) {
      if (toolName.toLowerCase().includes(key)) {
        return category;
      }
    }
    return 'Uncategorized';
  }

  getPriorityByName(toolName) {
    const coreTools = [
      'runningProcesses', 'firewallStatus', 'firewallRules',
      'localUsers', 'localAdmins', 'eventLogs', 'registryRunKeys',
      'scheduledTasks', 'startupPrograms', 'processDetails'
    ];
    return coreTools.includes(toolName) ? 'CORE' : 'STANDARD';
  }
}

// Usage Pattern
function instrumentTool(toolName, toolFunction) {
  const telemetry = new TelemetryEngine();

  return async function instrumentedTool(...args) {
    const execution = telemetry.recordExecution(toolName, {
      argumentCount: args.length,
      argumentTypes: args.map(a => typeof a)
    });

    try {
      const result = await toolFunction(...args);
      execution.complete(true);
      return result;
    } catch (error) {
      execution.complete(false, error);
      throw error;
    }
  };
}

export { TelemetryEngine, instrumentTool };
