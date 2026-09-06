import { execSync } from "child_process";

const tools = [
  // Round 3: Remaining uncovered tools
  { name: "failedLogons", cmd: "Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4625} -MaxEvents 5 -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "successfulLogons", cmd: "Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624} -MaxEvents 5 -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "loggedOnUsers", cmd: "Get-Process -IncludeUserName -ErrorAction SilentlyContinue | Select-Object UserName -Unique | Measure-Object" },
  { name: "desktopFiles", cmd: "Get-ChildItem $env:PUBLIC\Desktop -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "processByPid", cmd: "Get-Process | Select-Object Id | Measure-Object" },
  { name: "processDetails", cmd: "Get-Process | Select-Object ProcessName, Path, Company | Measure-Object" },
  { name: "tasklist", cmd: "Get-Process | Measure-Object" },
  { name: "processMonitor", cmd: "Get-Process | Where-Object CPU -gt 0 | Measure-Object" },
  { name: "sharedFolders", cmd: "Get-SmbShare -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "inboundRules", cmd: "Get-NetFirewallRule -Direction Inbound -Enabled $true -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "outboundRules", cmd: "Get-NetFirewallRule -Direction Outbound -Enabled $true -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "checkHash", cmd: "Get-FileHash C:\Windows\System32\cmd.exe -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "fileMetadata", cmd: "Get-Item C:\Windows\System32\cmd.exe -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "serviceLogs", cmd: "Get-EventLog -LogName System -Source Service* -Newest 5 -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "servicesChecker", cmd: "Get-Service | Measure-Object" },
  { name: "huntCredentialDumping", cmd: "Get-Process | Where-Object Name -like '*lsass*' -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "huntSuspiciousTasks", cmd: "Get-ScheduledTask -TaskPath '\Microsoft\Windows\' -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "securityAudit", cmd: "Get-MpComputerStatus -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "persistenceAudit", cmd: "Get-Item HKCU:\Software\Microsoft\Windows\Run -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "defenderQuickScan", cmd: "Invoke-MpScan -ScanType QuickScan -ErrorAction SilentlyContinue | Measure-Object" }
];

let passed = 0, failed = 0, failures = [];

for (const tool of tools) {
  try {
    execSync(`powershell -NoProfile -Command "${tool.cmd.replace(/"/g, '\\"')}"`, {
      encoding: "utf-8",
      timeout: 7000,
      stdio: ["pipe", "pipe", "pipe"]
    });
    passed++;
  } catch (err) {
    failed++;
    const msg = err.message || "";
    let type = "UNKNOWN";
    if (msg.includes("ETIMEDOUT")) type = "TIMEOUT";
    if (msg.includes("Access denied")) type = "PERMISSION";
    
    failures.push({ tool: tool.name, type });
  }
}

console.log(`A2,${passed},${failed},${Math.round(passed/(passed+failed)*100)}`);
failures.slice(0, 3).forEach(f => console.log(`  FAIL: ${f.tool} (${f.type})`));
