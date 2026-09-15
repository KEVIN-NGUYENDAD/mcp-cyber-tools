import { execSync, execFileSync } from "child_process";
import { z } from "zod";

export { z };

const COMMAND_TIMEOUT = 30000; // 30 seconds timeout to prevent server blocking

// INJ-02. `-EncodedCommand` bảo vệ DÒNG LỆNH, không bảo vệ THÂN SCRIPT.
//
// Tham số được nội suy vào script TRƯỚC khi mã hoá base64, nên nó đã nằm trong
// mã nguồn PowerShell lúc mã hoá — base64 chỉ chuyên chở nguyên vẹn thứ đã bị
// chèn. Và PowerShell bung `$(...)` NGAY BÊN TRONG nháy kép, nên kẻ tấn công
// không cần thoát dấu nháy: `checkHash({ path: "$(calc)" })` là chạy được.
//
// Cách duy nhất không phụ thuộc vào việc thoát ký tự cho đúng: giá trị không đi
// qua trình phân tích cú pháp nữa. Nó đi qua BIẾN MÔI TRƯỜNG; script chỉ đọc
// `$env:MCP_ARG_<TÊN>`, mà nội dung biến môi trường thì PowerShell không bao
// giờ diễn dịch lại.
const ARG_PREFIX = "MCP_ARG_";

function buildParamPrelude(params) {
  const env = {};
  const lines = [];
  for (const [name, value] of Object.entries(params)) {
    if (!/^[A-Za-z][A-Za-z0-9_]*$/.test(name)) {
      throw new Error(`Tên tham số PowerShell không hợp lệ: ${name}`);
    }
    const key = ARG_PREFIX + name.toUpperCase();
    env[key] = value === undefined || value === null ? "" : String(value);
    // Không nháy, không nội suy: vế phải là một truy cập biến, không phải chuỗi.
    lines.push(`$${name} = $env:${key}`);
  }
  return { env, prelude: lines.length ? lines.join("\n") + "\n" : "" };
}

/**
 * @param {string} command  Script PowerShell. Tham chiếu tham số bằng TÊN BIẾN
 *                          (`$path`), tuyệt đối không nội suy `${path}` vào đây.
 * @param {object} [params] Cặp tên→giá trị, truyền qua biến môi trường.
 */
export function runPowerShell(command, params = null) {
  try {
    if (params) {
      const { env, prelude } = buildParamPrelude(params);
      return runPowerShellEncoded(prelude + command, env);
    }
    return runPowerShellEncoded(command, null);
  } catch (error) {
    console.error("[CMD-POWERSHELL-ERROR]", error.message);
    return { success: false, error: error.message };
  }
}

function runPowerShellEncoded(command, extraEnv) {
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
        maxBuffer: 10 * 1024 * 1024, // 10MB buffer for large outputs
        env: extraEnv ? { ...process.env, ...extraEnv } : process.env
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

    // powershell.exe thoát với mã 1 bất cứ khi nào câu lệnh cuối đặt $? = False
    // — kể cả khi lỗi đã bị `-ErrorAction SilentlyContinue` nuốt. "Không tìm
    // thấy sự kiện nào" vì thế đi ra ngoài y hệt một lỗi thật, và execFileSync
    // ném ngoại lệ cho cả hai. Kết quả: một truy vấn rỗng hợp lệ bị báo là FAIL.
    //
    // Quy tắc phân đôi: nếu PowerShell không nói gì (stdout rỗng, stderr rỗng)
    // thì đó là một kết quả RỖNG, không phải một lỗi. Nếu nó có nói gì ở stderr
    // thì đó là lỗi thật, và thông báo đó chính là nguyên nhân.
    //
    // Rỗng ở đây vẫn chưa phân biệt được "đã nhìn, sạch" với "không nhìn được";
    // câu hỏi đó thuộc về scripts/sensor_probe.py, không thuộc về lớp truyền.
    const stderrText = unwrapClixml(error.stderr);
    const stdoutText = (error.stdout || "").trim();
    if (!stderrText && !stdoutText && error.code !== "ENOBUFS"
        && error.signal !== "SIGTERM" && error.code !== "ETIMEDOUT") {
      console.error("[CMD-POWERSHELL-EMPTY] Thoát khác 0 nhưng không có thông báo nào — coi là rỗng");
      return { success: true, data: "" };
    }

    return { success: false, error: describePowerShellFailure(error) };
  }
}

// PowerShell ghi lỗi ra stderr dưới dạng CLIXML khi stdout bị chuyển hướng.
// Không gỡ ra thì mọi lỗi đọc như một đống thẻ XML.
function unwrapClixml(text) {
  if (!text || text.indexOf("#< CLIXML") === -1) return (text || "").trim();
  const parts = [];
  const re = /<S S="Error">([\s\S]*?)<\/S>/g;
  let match;
  while ((match = re.exec(text)) !== null) {
    parts.push(match[1]
      .replace(/_x000D_/g, "")
      .replace(/_x000A_/g, "\n")
      .replace(/&lt;/g, "<").replace(/&gt;/g, ">")
      .replace(/&quot;/g, '"').replace(/&amp;/g, "&"));
  }
  return parts.join("").trim();
}

// error.message của execFileSync là "Command failed: powershell ... <base64>".
// Chuỗi base64 nuốt trọn thông báo và đẩy nguyên nhân thật ra ngoài giới hạn
// cắt chuỗi ở mọi nơi khác — 16 tool hỏng trong Sprint 8 ban đầu đều báo về
// một dòng lỗi không phân biệt được với nhau. Nguyên nhân thật nằm ở stderr.
function describePowerShellFailure(error) {
  const stderr = unwrapClixml(error.stderr);
  if (stderr) return stderr;
  if (error.code === "ENOBUFS") {
    return "ENOBUFS: script sinh nhiều dữ liệu hơn maxBuffer (10MB) — thu hẹp truy vấn hoặc giảm -Depth của ConvertTo-Json";
  }
  if (error.signal === "SIGTERM" || error.code === "ETIMEDOUT") {
    return `Hết giờ sau ${COMMAND_TIMEOUT}ms`;
  }
  const stdout = (error.stdout || "").trim();
  if (stdout) return stdout.substring(0, 500);
  return `${error.code || "lỗi"}: PowerShell thoát với mã ${error.status}`;
}

// INJ-01. `runCmd` đi qua `cmd.exe /d /s /c`, nên `&`, `&&`, `|`, `^` trong
// tham số là TOÁN TỬ chứ không phải dữ liệu: `ping({ host: "127.0.0.1 & whoami" })`
// chạy hai lệnh. Không có cách nào thoát cho đúng một cách đáng tin trên cmd.exe
// — nên đừng dựng dòng lệnh nữa.
//
// `execFileSync` không có shell: `args` tới thẳng tiến trình con dưới dạng mảng
// đối số tách rời. Một `host` chứa `& whoami` khi đó là một tên máy sai, và
// `ping` trả về "không phân giải được" — đúng như phải thế.
export function runCmdArgs(file, args = []) {
  const shown = `${file} ${args.join(" ")}`;
  try {
    console.error("[CMD-EXECFILE] Starting:", shown.substring(0, 100));
    const startTime = Date.now();

    const output = execFileSync(file, args, {
      encoding: "utf8",
      stdio: ["pipe", "pipe", "pipe"],
      timeout: COMMAND_TIMEOUT,
      maxBuffer: 10 * 1024 * 1024
    });

    console.error(`[CMD-EXECFILE-OK] ${Date.now() - startTime}ms, ${output.length} bytes`);
    return { success: true, data: output };
  } catch (error) {
    console.error("[CMD-EXECFILE-ERROR]", {
      file,
      code: error.code,
      signal: error.signal,
      status: error.status,
      stderr: error.stderr ? String(error.stderr).substring(0, 300) : null
    });

    // ping/tracert/nslookup thoát khác 0 cho một kết quả HỢP LỆ (host không
    // phản hồi, tên không phân giải được). Thông tin nằm ở stdout; ném nó đi
    // rồi báo FAIL sẽ biến "đã đo, không tới được" thành "không đo được".
    const stdout = (error.stdout || "").toString().trim();
    const stderr = (error.stderr || "").toString().trim();
    if (stdout && error.signal !== "SIGTERM" && error.code !== "ETIMEDOUT") {
      return { success: true, data: stdout };
    }
    if (error.signal === "SIGTERM" || error.code === "ETIMEDOUT") {
      return { success: false, error: `Hết giờ sau ${COMMAND_TIMEOUT}ms` };
    }
    return { success: false, error: stderr || error.message };
  }
}

// Ràng buộc dùng chung cho mọi tham số "host" đi vào một lệnh mạng.
// Không phải để chặn injection — `runCmdArgs` đã chặn ở lớp dưới — mà để một
// giá trị vô nghĩa bị từ chối tại biên với thông báo đọc được, thay vì đi tới
// tận `ping` rồi quay về dưới dạng lỗi của Windows.
export const hostSchema = z.string()
  .trim()
  .min(1, "host rỗng")
  .max(253, "host dài quá 253 ký tự")
  .regex(/^[A-Za-z0-9._:-]+$/,
         "host chỉ được chứa chữ, số, dấu chấm, gạch ngang, gạch dưới, hai chấm (IPv6)");

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
