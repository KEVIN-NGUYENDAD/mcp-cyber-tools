// IC-002 Pre-remediation Test (Node.js version)
import { execSync } from 'child_process';
import fs from 'fs';

console.log('\n🔬 IC-002 PRE-REMEDIATION TEST\n');
console.log('='.repeat(70));

const results = {};

// Test 1: Check SeSecurityPrivilege status
console.log('\n[1] Checking SeSecurityPrivilege...');
try {
  const privOutput = execSync('powershell -NoProfile -Command "whoami /priv"', {
    encoding: 'utf8'
  });

  if (privOutput.includes('SeSecurityPrivilege')) {
    console.log('    ✅ SeSecurityPrivilege FOUND');
    results.SeSecurityPrivilege = 'ENABLED';
  } else {
    console.log('    ❌ SeSecurityPrivilege NOT FOUND');
    results.SeSecurityPrivilege = 'DISABLED';
  }
} catch (e) {
  console.log('    ⚠️  Error checking privilege:', e.message.substring(0, 60));
  results.SeSecurityPrivilege = 'ERROR';
}

// Test 2: Try to access Security Event Log
console.log('\n[2] Testing Security Event Log access...');
try {
  const logOutput = execSync(
    'powershell -NoProfile -Command "Get-WinEvent -LogName Security -MaxEvents 1 -ErrorAction Stop | ConvertTo-Json"',
    {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    }
  );

  if (logOutput.trim()) {
    console.log('    ✅ Security log ACCESSIBLE');
    results.SecurityLog = 'ACCESSIBLE';
    results.SecurityLogEventCount = 1;
  }
} catch (e) {
  console.log('    ❌ Security log BLOCKED (access denied)');
  results.SecurityLog = 'BLOCKED';
  results.SecurityLogEventCount = 0;
}

// Test 3: Try failedLogons (EventID 4625)
console.log('\n[3] Testing failed logons (EventID 4625)...');
try {
  const failedOutput = execSync(
    'powershell -NoProfile -Command "Get-WinEvent -LogName Security -FilterXPath \\\"*[System[EventID=4625]]\\\" -MaxEvents 1 -ErrorAction Stop | ConvertTo-Json"',
    {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    }
  );

  if (failedOutput.trim()) {
    console.log('    ✅ Failed logons ACCESSIBLE');
    results.FailedLogons = 'ACCESSIBLE';
  }
} catch (e) {
  console.log('    ❌ Failed logons BLOCKED');
  results.FailedLogons = 'BLOCKED';
}

// Test 4: Try successfulLogons (EventID 4624)
console.log('\n[4] Testing successful logons (EventID 4624)...');
try {
  const successOutput = execSync(
    'powershell -NoProfile -Command "Get-WinEvent -LogName Security -FilterXPath \\\"*[System[EventID=4624]]\\\" -MaxEvents 1 -ErrorAction Stop | ConvertTo-Json"',
    {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    }
  );

  if (successOutput.trim()) {
    console.log('    ✅ Successful logons ACCESSIBLE');
    results.SuccessfulLogons = 'ACCESSIBLE';
  }
} catch (e) {
  console.log('    ❌ Successful logons BLOCKED');
  results.SuccessfulLogons = 'BLOCKED';
}

// Calculate visibility
const accessible = [
  results.SecurityLog,
  results.FailedLogons,
  results.SuccessfulLogons
].filter(x => x === 'ACCESSIBLE').length;

const visibility = Math.round((accessible / 3) * 100);
results.AuthenticationVisibility = `${visibility}%`;
results.Timestamp = new Date().toISOString();

// Display summary
console.log('\n' + '='.repeat(70));
console.log('\n📊 PRE-REMEDIATION SUMMARY\n');
console.log(`SeSecurityPrivilege:        ${results.SeSecurityPrivilege}`);
console.log(`Security Log Access:        ${results.SecurityLog}`);
console.log(`Failed Logons Access:       ${results.FailedLogons}`);
console.log(`Successful Logons Access:   ${results.SuccessfulLogons}`);
console.log(`\nAuthentication Visibility:  ${results.AuthenticationVisibility}`);
console.log(`\nTimestamp: ${results.Timestamp}`);

// Save results
const filePath = 'ic002_pre_validation_node.json';
fs.writeFileSync(filePath, JSON.stringify(results, null, 2));
console.log(`\n✅ Results saved to: ${filePath}\n`);

if (visibility === 0) {
  console.log('⚠️  CURRENT STATE: Authentication visibility is 0%');
  console.log('    Security Event Log is BLOCKED (permission denied)');
  console.log('\n🔧 REMEDIATION NEEDED:');
  console.log('    Administrator must grant SeSecurityPrivilege to current user:');
  console.log('    1. Run as admin: ntrights +r SeSecurityPrivilege -u <username>');
  console.log('    2. User must log off and log back on');
  console.log('    3. Re-run test to verify access restored');
} else if (visibility === 100) {
  console.log('✅ CURRENT STATE: Authentication visibility is 100%');
  console.log('   All security event log queries are accessible!');
} else {
  console.log(`⚠️  CURRENT STATE: Authentication visibility is ${visibility}%`);
  console.log('    Some but not all security queries are accessible');
}

console.log();
