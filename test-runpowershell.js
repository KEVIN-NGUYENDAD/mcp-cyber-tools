// Direct test of runPowerShell() with Get-WinEvent
// Purpose: See what data actually comes back

import { runPowerShell } from './modules/shared.js';

console.log("\n========== TEST: runPowerShell with Get-WinEvent ==========\n");

const result = runPowerShell(
  'Get-WinEvent -LogName Security -MaxEvents 5 | ConvertTo-Json -Depth 5'
);

console.log("RESULT OBJECT:");
console.log(JSON.stringify(result, null, 2));

console.log("\n========== ANALYSIS ==========\n");

if (result.success) {
  console.log("✅ SUCCESS: true");
  console.log("Data length:", result.data.length);
  console.log("First 500 chars:", result.data.substring(0, 500));

  if (result.data.length > 0) {
    console.log("\n✅ DATA FOUND - runPowerShell() works!");
    console.log("Issue is in collector wrapper, not runPowerShell()");
  } else {
    console.log("\n❌ SUCCESS but empty data - wrapper returns blank");
  }
} else {
  console.log("❌ SUCCESS: false");
  console.log("Error:", result.error);

  if (result.error.includes("UnauthorizedAccessException")) {
    console.log("\n→ Permission issue: Non-admin cannot read Security logs");
  } else if (result.error.includes("Windows PowerShell")) {
    console.log("\n→ Shell opened but command didn't execute");
  }
}

console.log("\n========== END TEST ==========\n");
