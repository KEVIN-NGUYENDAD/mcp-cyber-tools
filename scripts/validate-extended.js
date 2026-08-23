import { execSync } from "child_process";

const tools = [
  // Priority 1: Host Visibility (host.js)
  { name: "systemInfo", cmd: "Get-ComputerInfo | Select-Object CsSystemType | Measure-Object" },
  { name: "hostname", cmd: "hostname" },
  { name: "userProfiles", cmd: "Get-ChildItem 'C:\Users' -Directory | Measure-Object" },
  
  // Priority 2: Process Visibility (process.js)
  { name: "runningProcesses", cmd: "Get-Process | Measure-Object" },
  { name: "processTree", cmd: "Get-Process | Select-Object ProcessName | Measure-Object" },
  { name: "topProcesses", cmd: "Get-Process | Sort-Object -Descending CPU | Select-Object -First 5 | Measure-Object" },
  
  // Priority 3: Service Visibility (services.js)
  { name: "runningServices", cmd: "Get-Service | Where-Object Status -eq 'Running' | Measure-Object" },
  { name: "stoppedServices", cmd: "Get-Service | Where-Object Status -eq 'Stopped' | Measure-Object" },
  
  // Priority 4: Network Visibility (network.js)
  { name: "ipconfig", cmd: "Get-NetIPConfiguration | Measure-Object" },
  { name: "netstat", cmd: "Get-NetTCPConnection | Measure-Object" },
  { name: "activeConnections", cmd: "Get-NetTCPConnection -State Established | Measure-Object" },
  
  // Priority 5: Security (defender.js)
  { name: "defenderStatus", cmd: "Get-MpComputerStatus | Select-Object -Property RealTimeProtectionEnabled" },
  { name: "defenderThreats", cmd: "Get-MpThreatDetection | Measure-Object" },
  
  // Priority 6: Firewall (firewall.js)
  { name: "firewallStatus", cmd: "Get-NetFirewallProfile -All | Measure-Object" },
  { name: "inboundRules", cmd: "Get-NetFirewallRule -Direction Inbound | Measure-Object" },
  
  // Priority 7: Event Logs (eventlogs.js)
  { name: "systemLogs", cmd: "Get-EventLog -LogName System -Newest 1 | Measure-Object" },
  { name: "applicationLogs", cmd: "Get-EventLog -LogName Application -Newest 1 | Measure-Object" },
  
  // Priority 8: Startup Items (persistence.js)
  { name: "startupPrograms", cmd: "Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Run | Measure-Object" }
];

console.log("\n════════════════════════════════════════════════════════════════");
console.log("TOOL VALIDATION TEST RESULTS");
console.log("════════════════════════════════════════════════════════════════\n");

let passed = 0, failed = 0, failures = [];

for (const tool of tools) {
  try {
    const cmd = `powershell -NoProfile -Command "${tool.cmd.replace(/"/g, '\\"')}"`;
    const result = execSync(cmd, { 
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "pipe"],
      timeout: 5000
    }).trim();
    
    console.log(`✅ ${tool.name.padEnd(20)} PASS`);
    passed++;
  } catch (err) {
    console.log(`❌ ${tool.name.padEnd(20)} FAIL - ${err.message.slice(0, 50)}`);
    failed++;
    failures.push({
      tool: tool.name,
      error: err.message.slice(0, 100),
      priority: "HIGH",
      recommendation: `Investigate why ${tool.name} failed. May be environmental or framework issue.`
    });
  }
}

console.log("\n════════════════════════════════════════════════════════════════");
console.log(`SUMMARY: ${passed} PASS, ${failed} FAIL (${Math.round(passed/(passed+failed)*100)}% pass rate)`);
console.log("════════════════════════════════════════════════════════════════\n");

if (failures.length > 0) {
  console.log("POTENTIAL IMPROVEMENT CYCLES IDENTIFIED:\n");
  failures.forEach((f, i) => {
    console.log(`IC-00${i+4}: ${f.tool.toUpperCase()}`);
    console.log(`  Problem: Tool execution failed`);
    console.log(`  Error: ${f.error}`);
    console.log(`  Action: Investigate and fix\n`);
  });
}

process.exit(failed > 0 ? 1 : 0);
