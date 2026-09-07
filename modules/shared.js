import { execSync } from "child_process";
import { z } from "zod";

export { z };

const COMMAND_TIMEOUT = 30000; // 30 seconds timeout to prevent server blocking

export function runPowerShell(command) {
  try {
    const fullCommand = `powershell -NoProfile -Command "${command}"`;
    console.error("[CMD-POWERSHELL] Starting:", command.substring(0, 100) + "...");
    const startTime = Date.now();

    const output = execSync(fullCommand, {
      encoding: "utf8",
      stdio: ["pipe", "pipe", "pipe"],
      timeout: COMMAND_TIMEOUT,
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer for large outputs
    });

    const elapsed = Date.now() - startTime;
    console.error(`[CMD-POWERSHELL-OK] Completed in ${elapsed}ms, output length: ${output.length}`);

    return { success: true, data: output };
  } catch (error) {
    console.error("[CMD-POWERSHELL-ERROR]", {
      name: error.constructor.name,
      code: error.code,
      signal: error.signal,
      message: error.message.substring(0, 300),
      stdout: error.stdout ? error.stdout.substring(0, 300) : null,
      stderr: error.stderr ? error.stderr.substring(0, 300) : null
    });

    return { success: false, error: error.message };
  }
}

export function runCmd(command) {
  try {
    console.error("[CMD-EXEC] Starting:", command.substring(0, 100) + "...");
    const startTime = Date.now();

    const output = execSync(command, {
      encoding: "utf8",
      timeout: COMMAND_TIMEOUT,
      maxBuffer: 10 * 1024 * 1024
    });

    const elapsed = Date.now() - startTime;
    console.error(`[CMD-EXEC-OK] Completed in ${elapsed}ms, output length: ${output.length}`);

    return { success: true, data: output };
  } catch (error) {
    console.error("[CMD-EXEC-ERROR]", {
      name: error.constructor.name,
      code: error.code,
      signal: error.signal,
      message: error.message.substring(0, 300),
      stdout: error.stdout ? error.stdout.substring(0, 300) : null,
      stderr: error.stderr ? error.stderr.substring(0, 300) : null
    });

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
