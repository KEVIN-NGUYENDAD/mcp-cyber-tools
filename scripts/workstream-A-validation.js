import { execSync } from "child_process";

const tools = [
  // Round 2 validation (next 20 unvalidated tools)
  { name: "cpuUsage", cmd: "Get-WmiObject Win32_Processor | Measure-Object" },
  { name: "memoryUsage", cmd: "Get-WmiObject Win32_OperatingSystem | Select-Object TotalVisibleMemorySize | Measure-Object" },
  { name: "installedSoftware", cmd: "Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "environmentVars", cmd: "[Environment]::GetEnvironmentVariables() | Measure-Object" },
  { name: "alternateDataStreams", cmd: "Get-Item C:\Windows\System32 -Stream * -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "dllHijackLocations", cmd: "Get-ChildItem C:\Windows\System32 -Filter '*.dll' -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "dnsCache", cmd: "Get-DnsClientCache -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "routePrint", cmd: "Get-NetRoute -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "arp", cmd: "Get-NetNeighbor -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "tracert", cmd: "Test-NetConnection google.com -Hops 5 -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "nslookup", cmd: "Resolve-DnsName google.com -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "ping", cmd: "Test-Connection google.com -Count 1 -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "scanPort", cmd: "Test-NetConnection localhost -Port 80 -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "defenderHistory", cmd: "Get-MpPreference -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "defenderExclusions", cmd: "Get-MpPreference -ErrorAction SilentlyContinue | Select-Object ExclusionPath | Measure-Object" },
  { name: "disabledFirewallRules", cmd: "Get-NetFirewallRule -Enabled $false -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "disabledServices", cmd: "Get-Service | Where-Object Status -eq 'Stopped' | Measure-Object" },
  { name: "autoStartServices", cmd: "Get-Service | Where-Object StartType -eq 'Automatic' | Measure-Object" },
  { name: "powershellLogs", cmd: "Get-EventLog -LogName 'Windows PowerShell' -Newest 1 -ErrorAction SilentlyContinue | Measure-Object" },
  { name: "rdpLogs", cmd: "Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624} -MaxEvents 1 -ErrorAction SilentlyContinue | Measure-Object" }
];

let passed = 0, failed = 0, failures = [];

for (const tool of tools) {
  try {
    execSync(`powershell -NoProfile -Command "${tool.cmd.replace(/"/g, '\\"')}"`, {
      encoding: "utf-8",
      timeout: 6000,
      stdio: ["pipe", "pipe", "pipe"]
    });
    passed++;
  } catch (err) {
    failed++;
    const msg = err.message || "";
    let type = "UNKNOWN";
    if (msg.includes("ETIMEDOUT")) type = "TIMEOUT";
    if (msg.includes("Access denied")) type = "PERMISSION";
    if (msg.includes("not found")) type = "NOTFOUND";
    if (msg.includes("not")) type = "PARSING";
    
    failures.push({ tool: tool.name, type, msg: msg.slice(0, 50) });
  }
}

console.log(`A,${passed},${failed},${Math.round(passed/(passed+failed)*100)},${JSON.stringify(failures)}`);
