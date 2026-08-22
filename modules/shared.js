import { execSync } from "child_process";
import { z } from "zod";

export { z };

export function runPowerShell(command) {
  try {
    const fullCommand = `powershell -NoProfile -Command "${command}"`;
    console.log("DEBUG: Executing command:", fullCommand.substring(0, 100) + "...");
    const output = execSync(fullCommand, { encoding: "utf8" });
    console.log("DEBUG: Raw output length:", output.length);
    console.log("DEBUG: First 200 chars:", output.substring(0, 200));
    return { success: true, data: output };
  } catch (error) {
    console.log("DEBUG: Command failed:", error.message.substring(0, 100));
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
