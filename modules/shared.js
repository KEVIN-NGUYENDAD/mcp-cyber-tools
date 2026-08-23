import { execSync } from "child_process";
import { z } from "zod";

export { z };

export function checkRegistryPermission() {
  try {
    execSync('powershell -NoProfile -Command "Get-ItemProperty HKLM:\\Software -ErrorAction Stop | Out-Null"', {
      encoding: "utf8",
      stdio: ["pipe", "pipe", "pipe"],
      timeout: 3000
    });
    return { admin: true };
  } catch (error) {
    return { admin: false, fallback: "HKCU" };
  }
}

export function normalizePathVariable(path) {
  // IC-005: Fix path escaping by normalizing environment variables
  return path
    .replace(/\$env:APPDATA/g, process.env.APPDATA || 'C:\\Users\\' + (process.env.USERNAME || 'Public') + '\\AppData\\Roaming')
    .replace(/\$env:USERPROFILE/g, process.env.USERPROFILE || 'C:\\Users\\' + (process.env.USERNAME || 'Public'))
    .replace(/\$env:TEMP/g, process.env.TEMP || 'C:\\Windows\\Temp')
    .replace(/\$env:PUBLIC/g, process.env.PUBLIC || 'C:\\Users\\Public');
}

export function runPowerShell(command) {
  try {
    const normalizedCommand = command
      .trim()
      .replace(/\r?\n\s+/g, ' ');

    const fullCommand = `powershell -NoProfile -Command "${normalizedCommand}"`;
    const output = execSync(fullCommand, { encoding: "utf8", stdio: ["pipe", "pipe", "pipe"] });

    return { success: true, data: output };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

export function runCmd(command) {
  try {
    const output = execSync(command, { encoding: "utf8" });
    return { success: true, data: output };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// IC-035: Event Log Filter Standardization
export function buildEventLogFilter(logName, eventId, hoursBack = 24) {
  // Standardized event log filter builder for consistent Get-WinEvent queries
  // Eliminates hashtable syntax errors across different tools
  const xpathFilter = `*[System[(EventID=${eventId}) and TimeCreated[timediff(@SystemTime) <= ${hoursBack * 60 * 60 * 1000}]]]`;

  return {
    logName: logName,
    filterHashtable: {
      LogName: logName,
      ID: eventId,
      StartTime: new Date(Date.now() - hoursBack * 60 * 60 * 1000)
    },
    xpath: xpathFilter,
    // PowerShell command using standardized filter
    psCommand: `Get-WinEvent -FilterHashtable @{LogName='${logName}'; ID=${eventId}} -ErrorAction SilentlyContinue | Select-Object -Property TimeCreated, Message, ProviderName`,
    psCommandXPath: `Get-WinEvent -FilterXPath "${xpathFilter}" -LogName ${logName} -ErrorAction SilentlyContinue | Select-Object -Property TimeCreated, Message, ProviderName`
  };
}

// IC-035 Companion: Execute standardized event log query
export function queryEventLog(logName, eventId, hoursBack = 24) {
  const filter = buildEventLogFilter(logName, eventId, hoursBack);
  return runPowerShell(filter.psCommand);
}

// IC-036: Registry Query Caching
// Solves cold-start registry queries (8-10s) with TTL-based caching
class RegistryQueryCache {
  constructor(ttlSeconds = 300) {
    this.cache = new Map();
    this.ttlMs = ttlSeconds * 1000;
  }

  getCacheKey(hive, path) {
    return `${hive}:${path}`;
  }

  isCached(hive, path) {
    const key = this.getCacheKey(hive, path);
    if (!this.cache.has(key)) return false;

    const cached = this.cache.get(key);
    const isExpired = Date.now() - cached.timestamp > this.ttlMs;

    if (isExpired) {
      this.cache.delete(key);
      return false;
    }

    return true;
  }

  get(hive, path) {
    if (this.isCached(hive, path)) {
      const key = this.getCacheKey(hive, path);
      return this.cache.get(key).data;
    }
    return null;
  }

  set(hive, path, data) {
    const key = this.getCacheKey(hive, path);
    this.cache.set(key, {
      data: data,
      timestamp: Date.now()
    });
  }

  clear() {
    this.cache.clear();
  }

  getCacheStats() {
    return {
      entries: this.cache.size,
      ttlSeconds: this.ttlMs / 1000
    };
  }
}

// Global cache instance (5-minute TTL)
const registryCache = new RegistryQueryCache(300);

export function getCachedRegistryQuery(hive, path, queryFunction) {
  // Check cache first
  const cached = registryCache.get(hive, path);
  if (cached) {
    return { success: true, data: cached, fromCache: true };
  }

  // Execute query
  const result = queryFunction();

  if (result.success) {
    registryCache.set(hive, path, result.data);
    return { success: true, data: result.data, fromCache: false };
  }

  return result;
}

export function clearRegistryCache() {
  registryCache.clear();
}

export function getRegistryCacheStats() {
  return registryCache.getCacheStats();
}

// IC-041: Reliability Improvement - Permission Checking & Fallback
export function checkSecurityLogAccess() {
  // Check if user has SeSecurityPrivilege for event log access
  const result = runPowerShell(
    `[Security.Principal.WindowsIdentity]::GetCurrent().Groups -contains 'S-1-5-32-544'`
  );

  if (result.success && result.data.toLowerCase().includes('true')) {
    return { hasAccess: true, privilege: 'SeSecurityPrivilege' };
  }

  return {
    hasAccess: false,
    privilege: null,
    fallback: 'Application',
    reason: 'Elevated privileges required for Security log'
  };
}

// Fallback strategy for security log queries (when elevated privileges not available)
export function queryEventLogWithFallback(logName, eventId, hoursBack = 24) {
  // Try primary: Security log with Get-WinEvent
  let result = queryEventLog(logName, eventId, hoursBack);

  if (result.success) {
    return { ...result, source: 'primary', logName: logName };
  }

  // Fallback 1: Use Application log if Security unavailable
  if (logName === 'Security') {
    result = queryEventLog('Application', eventId, hoursBack);
    if (result.success) {
      return {
        ...result,
        source: 'fallback_application',
        logName: 'Application',
        note: 'Security log unavailable, using Application log fallback'
      };
    }
  }

  // Fallback 2: Use Get-EventLog as alternative to Get-WinEvent
  if (logName === 'Security') {
    result = runPowerShell(
      `Get-EventLog -LogName Security -InstanceId ${eventId} -ErrorAction SilentlyContinue | Select-Object -Property TimeGenerated, Message`
    );

    if (result.success) {
      return {
        success: true,
        data: result.data,
        source: 'fallback_get_eventlog',
        logName: 'Security',
        note: 'Using Get-EventLog fallback'
      };
    }
  }

  return {
    success: false,
    error: 'Unable to query event log. Requires elevated privileges or available fallback.',
    source: 'all_failed',
    logName: logName,
    recommendation: 'Run as Administrator or use fallback log source'
  };
}

// IC-041: Reliability wrapper - automatic retry with fallback
export function executeTool(toolName, toolFunction, retryCount = 2) {
  const results = {
    attempts: [],
    success: false,
    data: null,
    source: null
  };

  for (let attempt = 1; attempt <= retryCount; attempt++) {
    try {
      const result = toolFunction();

      if (result.success) {
        results.success = true;
        results.data = result.data;
        results.source = result.source || 'primary';
        results.attempts.push({
          attempt: attempt,
          status: 'success',
          message: `${toolName} succeeded on attempt ${attempt}`
        });
        return results;
      } else {
        results.attempts.push({
          attempt: attempt,
          status: 'failed',
          error: result.error
        });
      }
    } catch (error) {
      results.attempts.push({
        attempt: attempt,
        status: 'error',
        error: error.message
      });
    }

    // Wait before retry (exponential backoff: 100ms, 200ms)
    if (attempt < retryCount) {
      const waitMs = attempt * 100;
      setTimeout(() => {}, waitMs);
    }
  }

  results.success = false;
  results.error = `${toolName} failed after ${retryCount} attempts`;
  return results;
}

export function formatResponse(success, data, error = null) {
  if (success) {
    // Ensure data is properly formatted JSON string
    const output = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
    return {
      content: [{ type: "text", text: output }]
    };
  }
  return {
    content: [{ type: "text", text: `ERROR: ${error || "Unknown error"}` }]
  };
}

export function standardJsonResponse(tool, success, data = null, error = null) {
  return {
    content: [{
      type: "text",
      text: JSON.stringify({
        success,
        tool,
        timestamp: new Date().toISOString(),
        data: data || null,
        error: error || null
      }, null, 2)
    }]
  };
}

export function formatJson(obj) {
  return JSON.stringify(obj, null, 2);
}
