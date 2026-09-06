import { runPowerShell, formatResponse } from "./modules/shared.js";

console.log("🏆 IC-001 Track B Validation Test");
console.log("=".repeat(60));
console.log();

// Test 1: localUsers
console.log("TEST 1: localUsers (Get-LocalUser)");
console.log("-".repeat(60));

const localUsersCommand = `
  Get-LocalUser | Select-Object Name, Enabled, LastLogon, Description | ConvertTo-Json
`;

const usersResult = runPowerShell(localUsersCommand);
console.log("Result success:", usersResult.success);
console.log("Result data length:", usersResult.data?.length || 0);

if (usersResult.success) {
  try {
    const users = JSON.parse(usersResult.data);
    const userArray = Array.isArray(users) ? users : [users];
    console.log("✅ Users parsed successfully");
    console.log("   User count:", userArray.length);
    userArray.forEach((u, i) => {
      console.log(`   [${i+1}] ${u.Name} (Enabled: ${u.Enabled})`);
    });
  } catch (e) {
    console.log("❌ Failed to parse users JSON");
    console.log("   Error:", e.message);
  }
} else {
  console.log("❌ localUsers failed");
  console.log("   Error:", usersResult.error);
}

console.log();

// Test 2: localAdmins
console.log("TEST 2: localAdmins (Get-LocalGroupMember)");
console.log("-".repeat(60));

const localAdminsCommand = `
  Get-LocalGroupMember -Group "Administrators" | Select-Object Name, ObjectClass | ConvertTo-Json
`;

const adminsResult = runPowerShell(localAdminsCommand);
console.log("Result success:", adminsResult.success);
console.log("Result data length:", adminsResult.data?.length || 0);

if (adminsResult.success) {
  try {
    const admins = JSON.parse(adminsResult.data);
    const adminArray = Array.isArray(admins) ? admins : [admins];
    console.log("✅ Admins parsed successfully");
    console.log("   Admin count:", adminArray.length);
    adminArray.forEach((a, i) => {
      console.log(`   [${i+1}] ${a.Name} (${a.ObjectClass})`);
    });
  } catch (e) {
    console.log("❌ Failed to parse admins JSON");
    console.log("   Error:", e.message);
  }
} else {
  console.log("❌ localAdmins failed");
  console.log("   Error:", adminsResult.error);
}

console.log();

// Test 3: formatResponse verification
console.log("TEST 3: formatResponse (MCP output format)");
console.log("-".repeat(60));

const formattedUsers = formatResponse(usersResult.success, usersResult.data, usersResult.error);
console.log("Formatted response structure:");
console.log("  - Has content array:", Array.isArray(formattedUsers.content));
console.log("  - Has text field:", !!formattedUsers.content[0]?.text);
console.log("  - Text length:", formattedUsers.content[0]?.text?.length || 0);
console.log("  - Text starts with '[' or '{':", /^[\[{]/.test(formattedUsers.content[0]?.text || ""));

if (formattedUsers.content[0]?.text?.includes("=== DEBUG ===")) {
  console.log("❌ DEBUG TEXT FOUND IN OUTPUT - Protocol corruption detected!");
} else {
  console.log("✅ No debug text in formatted response");
}

console.log();
console.log("=".repeat(60));
console.log("🏆 Validation complete");
