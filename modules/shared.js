import { execSync, execFileSync } from "child_process";
import { z } from "zod";

export { z };

const COMMAND_TIMEOUT = 30000; // 30 seconds timeout to prevent server blocking

export function runPowerShell(command) {
  try {
    console.error("[CMD-POWERSHELL] Starting:", command.substring(0, 100) + "...");
    const startTime = Date.now();

    // Truyền script qua -EncodedCommand (base64 UTF-16LE) thay vì nhét vào
    // `powershell -Command "..."`.
    //
    // Cách cũ hỏng im lặng với MỌI script nhiều dòng: execSync trên Windows đi
    // qua cmd.exe, và cmd.exe cắt dòng lệnh ở ký tự xuống dòng đầu tiên.
    // PowerShell nhận một lệnh cụt, không in gì, thoát với mã 0 - nên
    // runPowerShell trả về { success: true, data: "" }. 43/81 lời gọi trong
    // modules/ là script nhiều dòng, trong đó có toàn bộ 9 tool hunting.
    //
    // execFileSync bỏ qua cmd.exe hoàn toàn, và -EncodedCommand miễn nhiễm với
    // dấu nháy, $, backslash và xuống dòng.
    const encoded = Buffer.from(command, "utf16le").toString("base64");

    const output = execFileSync(
      "powershell",
      ["-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
      {
        encoding: "utf8",
        stdio: ["pipe", "pipe", "pipe"],
        timeout: COMMAND_TIMEOUT,
        maxBuffer: 10 * 1024 * 1024 // 10MB buffer for large outputs
      }
    );

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
  // isError phải được đặt: không có nó, mọi client MCP (kể cả Claude) nhận một
  // kết quả "thành công" mà nội dung tình cờ bắt đầu bằng chữ ERROR. Lỗi im
  // lặng kiểu này là thứ khiến 10 tool hunting hỏng suốt mà không ai biết.
  return {
    isError: true,
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
