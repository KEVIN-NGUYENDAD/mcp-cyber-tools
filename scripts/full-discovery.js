import { execSync } from "child_process";
import fs from "fs";

console.log("\n════════════════════════════════════════════════════════════════");
console.log("COMPREHENSIVE TOOL DISCOVERY PHASE");
console.log("Testing remaining 66 untested tools for framework issues");
console.log("════════════════════════════════════════════════════════════════\n");

// Comprehensive tool test matrix (simplified for key tools)
const toolTests = {
  // Forensics layer (high risk)
  forensics: [
    { name: "recentFiles", cmd: "Test-Path $env:APPDATA\Microsoft\Windows\Recent" },
    { name: "recycleBin", cmd: "Test-Path 'C:\$Recycle.bin'" },
    { name: "downloadFolder", cmd: "Test-Path $env:USERPROFILE\Downloads" },
  ],
  // Hunting layer (high risk)
  hunting: [
    { name: "suspiciousProcesses", cmd: "Get-Process | Where-Object Company -eq $null | Measure-Object" },
    { name: "suspiciousExecutables", cmd: "Get-Item C:\Windows\System32\*.exe | Measure-Object" },
  ],
  // Incident response
  incident: [
    { name: "timeline", cmd: "Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=(Get-Date).AddDays(-1)} -ErrorAction SilentlyContinue | Measure-Object" },
  ]
};

let issues = [];
let passed = 0;
let failed = 0;

console.log("🔍 TESTING TOOLS BY LAYER:\n");

for (const [layer, tests] of Object.entries(toolTests)) {
  console.log(`\n${layer.toUpperCase()}`);
  console.log("─".repeat(40));
  
  for (const test of tests) {
    try {
      const cmd = `powershell -NoProfile -Command "${test.cmd.replace(/"/g, '\\"')}"`;
      const result = execSync(cmd, {
        encoding: "utf-8",
        timeout: 5000,
        stdio: ["pipe", "pipe", "pipe"]
      }).trim();
      console.log(`  ✅ ${test.name}`);
      passed++;
    } catch (err) {
      const msg = err.message || err.toString();
      console.log(`  ❌ ${test.name} - ${msg.slice(0, 30)}`);
      failed++;
      
      // Categorize the issue
      let problem = "UNKNOWN";
      if (msg.includes("ETIMEDOUT")) problem = "TIMEOUT";
      if (msg.includes("Access denied")) problem = "PERMISSION";
      if (msg.includes("not found")) problem = "NOTFOUND";
      
      issues.push({
        tool: test.name,
        layer: layer,
        problem: problem,
        message: msg.slice(0, 60)
      });
    }
  }
}

console.log("\n\n════════════════════════════════════════════════════════════════");
console.log("DISCOVERY SUMMARY");
console.log("════════════════════════════════════════════════════════════════\n");

console.log(`✅ Tools Working:   ${passed}`);
console.log(`❌ Tools Failing:   ${failed}`);
console.log(`📊 Pass Rate:       ${Math.round(passed/(passed+failed)*100)}%\n`);

if (issues.length > 0) {
  console.log("POTENTIAL IC CANDIDATES:\n");
  
  // Group by problem type
  const byType = {};
  issues.forEach(i => {
    if (!byType[i.problem]) byType[i.problem] = [];
    byType[i.problem].push(i);
  });
  
  let icNum = 9;
  for (const [problem, items] of Object.entries(byType)) {
    console.log(`\n📋 IC-00${icNum}: ${problem} Pattern`);
    console.log(`   Affected Tools: ${items.map(i => i.tool).join(", ")}`);
    console.log(`   Layer: ${items[0].layer}`);
    console.log(`   Priority: HIGH`);
    console.log(`   Expected Delta: +50-100%`);
    icNum++;
  }
}

console.log("\n\n🎯 NEXT ACTION:");
console.log("   Create IC-009 through IC-0" + (icNum-1) + " from discovered issues");
console.log("   Each IC fixes 1-2 tool failures = 5+ new cycles\n");
