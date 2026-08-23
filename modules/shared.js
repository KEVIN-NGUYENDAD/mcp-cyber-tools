import { execSync } from "child_process";
import { z } from "zod";

export { z };

export function runPowerShell(command) {
  try {
    const fullCommand = `powershell -NoProfile -Command "${command}"`;
    console.error("\n=== DEBUG: runPowerShell ===");
    console.error("INPUT_COMMAND:", command.substring(0, 100) + "...");

    const output = execSync(fullCommand, { encoding: "utf8", stdio: ["pipe", "pipe", "pipe"] });

    console.error("RAW_OUTPUT_LENGTH:", output.length);
    console.error("RAW_OUTPUT (first 1000):", output.substring(0, 1000));
    console.error("=== END DEBUG ===\n");

    return { success: true, data: output };
  } catch (error) {
    console.error("\n=== DEBUG: Command Failed ===");
    console.error("ERROR_TYPE:", error.constructor.name);
    console.error("ERROR_MESSAGE:", error.message.substring(0, 300));
    if (error.stdout) console.error("ERROR_STDOUT:", error.stdout.substring(0, 300));
    if (error.stderr) console.error("ERROR_STDERR:", error.stderr.substring(0, 300));
    console.error("=== END DEBUG ===\n");

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
