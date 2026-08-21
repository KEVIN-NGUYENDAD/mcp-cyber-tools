import { execSync } from "child_process";

export function runPowerShell(command) {
  try {
    const output = execSync(`powershell ${command}`, { encoding: "utf8" });
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
    return {
      content: [{ type: "text", text: data }]
    };
  }
  return {
    content: [{ type: "text", text: `ERROR: ${error || "Unknown error"}` }]
  };
}

export function formatJson(obj) {
  return JSON.stringify(obj, null, 2);
}
