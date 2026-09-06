// CYBER-TOOLS TELEMETRY SYSTEM
// Records every tool execution with full context

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

class TelemetryEngine {
  constructor(telemetryPath = null) {
    if (!telemetryPath) {
      const __dirname = path.dirname(fileURLToPath(import.meta.url));
      const projectRoot = path.resolve(__dirname, '..');
      telemetryPath = path.join(projectRoot, 'telemetry');
    }
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
    console.error(`[TRACE-SAVE] Saving record for: ${record.toolName}`);
    const dateKey = record.timestamp.split('T')[0];
    const dailyFile = path.join(this.telemetryPath, `telemetry-${dateKey}.json`);
    console.error(`[TRACE-SAVE] File path: ${dailyFile}`);

    let records = [];
    if (fs.existsSync(dailyFile)) {
      try {
        records = JSON.parse(fs.readFileSync(dailyFile, 'utf8'));
        console.error(`[TRACE-SAVE] Read ${records.length} existing records`);
      } catch (e) {
        console.error(`[TRACE-SAVE] Error reading file: ${e.message}`);
        records = [];
      }
    }

    records.push(record);
    try {
      fs.writeFileSync(dailyFile, JSON.stringify(records, null, 2));
      console.error(`[TRACE-SAVE] ✓ Wrote ${records.length} records to ${dailyFile}`);
    } catch (err) {
      console.error(`[TRACE-SAVE] ✗ WRITE FAILED: ${err.message}`);
    }
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
  console.error(`[TRACE-INSTRUMENT] Creating wrapper for: ${toolName}`);

  return async function instrumentedTool(...args) {
    console.error(`[TRACE-EXECUTE] Tool called: ${toolName}`);
    const execution = telemetry.recordExecution(toolName, {
      argumentCount: args.length,
      argumentTypes: args.map(a => typeof a)
    });
    console.error(`[TRACE-RECORD] Execution tracked, calling complete()`);

    try {
      const result = await toolFunction(...args);
      console.error(`[TRACE-SUCCESS] Tool succeeded: ${toolName}`);
      execution.complete(true);
      return result;
    } catch (error) {
      console.error(`[TRACE-ERROR] Tool failed: ${toolName}, error: ${error.message}`);
      execution.complete(false, error);
      throw error;
    }
  };
}

export { TelemetryEngine, instrumentTool };

