import { execSync } from "child_process";
import { z } from "zod";

export { z };

export function runPowerShell(command) {
  try {
    const fullCommand = `powershell -NoProfile -Command "${command}"`;
    console.log("\n=== DEBUG: runPowerShell ===");
    console.log("COMMAND:", fullCommand.substring(0, 150) + "...");

    const output = execSync(fullCommand, { encoding: "utf8", stdio: ["pipe", "pipe", "pipe"] });

    console.log("STDOUT_LENGTH:", output.length);
    console.log("STDOUT_PREVIEW:", output.substring(0, 500));
    console.log("=== END DEBUG ===\n");

    return { success: true, data: output };
  } catch (error) {
    console.log("\n=== DEBUG: Command Failed ===");
    console.log("ERROR_TYPE:", error.constructor.name);
    console.log("ERROR_MESSAGE:", error.message.substring(0, 300));
    if (error.stdout) console.log("ERROR_STDOUT:", error.stdout.substring(0, 300));
    if (error.stderr) console.log("ERROR_STDERR:", error.stderr.substring(0, 300));
    console.log("=== END DEBUG ===\n");

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
