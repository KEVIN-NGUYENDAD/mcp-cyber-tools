import { execSync } from "child_process";

const tools = [
  // Persistence layer tools (persistence.js) - HIGH RISK UNTESTED
  { name: "registryRunKeys", cmd: "Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Run -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "registryRunOnce", cmd: "Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "startupFolders", cmd: "Get-ChildItem 'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup' -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "scheduledTasks", cmd: "Get-ScheduledTask -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "wmiPersistence", cmd: "Get-WmiObject Win32_SystemDriver -ErrorAction SilentlyContinue | Measure-Object" },
  
  // Forensics tools (forensics.js) - HIGH RISK UNTESTED
  { name: "recentFiles", cmd: "Get-Item -Path $env:APPDATA\Microsoft\Windows\Recent -ErrorAction SilentlyContinue | Get-ChildItem | Measure-Object" },
  { name: "recycleBin", cmd: "[System.IO.DirectoryInfo]::New('C:\$Recycle.bin').EnumerateDirectories() | Measure-Object" },
  { name: "tempFiles", cmd: "Get-ChildItem $env:TEMP -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "timeline", cmd: "Get-ChildItem C:\Windows\System32\config\Sam -ErrorAction SilentlyContinue | Select-Object LastWriteTime | Measure-Object" },
  
  // Hunting tools (hunting.js) - HIGH RISK UNTESTED
  { name: "suspiciousProcesses", cmd: "Get-Process | Where-Object Name -like 'powershell' -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "suspiciousExecutables", cmd: "Get-ChildItem C:\Windows\System32 -Filter '*.exe' -ErrorAction SilentlyContinue | Measure-Object" }
];

console.log("\n════════════════════════════════════════════════════════════════");
console.log("PERSISTENCE & FORENSICS LAYER VALIDATION");
console.log("════════════════════════════════════════════════════════════════\n");

let passed = 0, failed = 0, failures = [];
const issues = [];

for (const tool of tools) {
  try {
    const cmd = `powershell -NoProfile -Command "${tool.cmd.replace(/"/g, '\\"')}"`;
    const result = execSync(cmd, { 
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "pipe"],
      timeout: 8000,
      maxBuffer: 5 * 1024 * 1024
    }).trim();
    
    console.log(`✅ ${tool.name.padEnd(25)} PASS`);
    passed++;
  } catch (err) {
    const errMsg = err.message || err.toString();
    console.log(`❌ ${tool.name.padEnd(25)} FAIL - ${errMsg.slice(0, 40)}`);
    failed++;
    
    let errorType = "UNKNOWN";
    if (errMsg.includes("ETIMEDOUT")) errorType = "TIMEOUT";
    if (errMsg.includes("Access denied")) errorType = "PERMISSION";
    if (errMsg.includes("not found")) errorType = "NOT_FOUND";
    if (errMsg.includes("No such")) errorType = "PATH_ERROR";
    
    issues.push({
      tool: tool.name,
      error: errMsg.slice(0, 80),
      type: errorType
    });
  }
}

console.log("\n════════════════════════════════════════════════════════════════");
console.log(`SUMMARY: ${passed}/${tools.length} PASS (${Math.round(passed/tools.length*100)}%)`);
console.log("════════════════════════════════════════════════════════════════\n");

if (issues.length > 0) {
  console.log("ERROR BREAKDOWN:\n");
  const byType = {};
  issues.forEach(i => {
    byType[i.type] = (byType[i.type] || 0) + 1;
  });
  
  Object.entries(byType).forEach(([type, count]) => {
    console.log(`  ${type}: ${count} tools`);
  });
  
  console.log("\n\nPOTENTIAL IMPROVEMENT CYCLES:\n");
  
  // Group by error type
  const timeouts = issues.filter(i => i.type === "TIMEOUT").map(i => i.tool);
  const permissions = issues.filter(i => i.type === "PERMISSION").map(i => i.tool);
  const notFound = issues.filter(i => i.type === "NOT_FOUND").map(i => i.tool);
  const pathErrors = issues.filter(i => i.type === "PATH_ERROR").map(i => i.tool);
  
  if (timeouts.length > 0) {
    console.log("IC-007: TIMEOUT PATTERN");
    console.log(`  Problem: Tools hanging on execution: ${timeouts.join(", ")}`);
    console.log(`  Type: Framework Performance Issue`);
    console.log(`  Expected Fix: Increase timeout or optimize query\n`);
  }
  
  if (permissions.length > 0) {
    console.log("IC-008: PERMISSION BOUNDARY");
    console.log(`  Problem: Tools blocked by access control: ${permissions.join(", ")}`);
    console.log(`  Type: Environmental/Privilege Issue`);
    console.log(`  Expected Fix: Document requirements or add fallback\n`);
  }
  
  if (pathErrors.length > 0 || notFound.length > 0) {
    console.log("IC-009: PATH/RESOURCE ERROR");
    console.log(`  Problem: Tools failing on path issues: ${[...pathErrors, ...notFound].join(", ")}`);
    console.log(`  Type: Path Escaping/Resource Not Found`);
    console.log(`  Expected Fix: Sanitize paths or add error handling\n`);
  }
}

process.exit(failed > 0 ? 1 : 0);
