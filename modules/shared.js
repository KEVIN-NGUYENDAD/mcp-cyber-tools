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
