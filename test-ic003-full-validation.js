import('./modules/shared.js').then(m => {
  console.log('🏆 IC-003c: FULL VALIDATION SUITE');
  console.log('='.repeat(70));
  console.log();

  // Test Group 1: IC-001 Regression (should still work)
  console.log('GROUP 1: IC-001 REGRESSION TESTS');
  console.log('-'.repeat(70));

  const localUsersCmd = `Get-LocalUser | Select-Object Name, Enabled, LastLogon, Description | ConvertTo-Json`;
  const localUsersResult = m.runPowerShell(localUsersCmd);

  console.log('✓ localUsers (IC-001):');
  console.log('  Success:', localUsersResult.success);
  if (localUsersResult.success && localUsersResult.data?.length > 0) {
    try {
      const users = JSON.parse(localUsersResult.data);
      const count = Array.isArray(users) ? users.length : 1;
      console.log('  Users returned:', count);
      console.log('  ✅ PASS - No regression');
    } catch (e) {
      console.log('  ❌ FAIL - Parse error:', e.message);
    }
  } else {
    console.log('  ❌ FAIL - No data returned');
  }

  console.log();

  const localAdminsCmd = `Get-LocalGroupMember -Group "Administrators" | Select-Object Name, ObjectClass | ConvertTo-Json`;
  const localAdminsResult = m.runPowerShell(localAdminsCmd);

  console.log('✓ localAdmins (IC-001):');
  console.log('  Success:', localAdminsResult.success);
  if (localAdminsResult.success && localAdminsResult.data?.length > 0) {
    try {
      const admins = JSON.parse(localAdminsResult.data);
      const count = Array.isArray(admins) ? admins.length : 1;
      console.log('  Admins returned:', count);
      console.log('  ✅ PASS - No regression');
    } catch (e) {
      console.log('  ❌ FAIL - Parse error:', e.message);
    }
  } else {
    console.log('  ❌ FAIL - No data returned');
  }

  console.log();
  console.log('GROUP 2: IC-003 NEW COVERAGE TESTS');
  console.log('-'.repeat(70));

  const firewallStatusCmd = `
    Get-NetFirewallProfile |
    Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction |
    ConvertTo-Json
  `;
  const statusResult = m.runPowerShell(firewallStatusCmd);

  console.log('✓ firewallStatus (IC-003):');
  console.log('  Success:', statusResult.success);
  if (statusResult.success && statusResult.data?.length > 0) {
    try {
      const profiles = JSON.parse(statusResult.data);
      const count = Array.isArray(profiles) ? profiles.length : 1;
      console.log('  Profiles returned:', count);
      console.log('  ✅ PASS - Framework fix works');
    } catch (e) {
      console.log('  ❌ FAIL - Parse error:', e.message);
    }
  } else {
    console.log('  ❌ FAIL - No data returned');
  }

  console.log();

  const firewallRulesCmd = `
    Get-NetFirewallRule |
    Where-Object {$_.Enabled -eq 1} |
    Select-Object Name, DisplayName, Direction, Action, Enabled |
    Select-Object -First 10 |
    ConvertTo-Json
  `;
  const rulesResult = m.runPowerShell(firewallRulesCmd);

  console.log('✓ firewallRules (IC-003):');
  console.log('  Success:', rulesResult.success);
  if (rulesResult.success && rulesResult.data?.length > 0) {
    try {
      const rules = JSON.parse(rulesResult.data);
      const count = Array.isArray(rules) ? rules.length : 1;
      console.log('  Rules returned:', count);
      console.log('  ✅ PASS - Framework fix works');
    } catch (e) {
      console.log('  ❌ FAIL - Parse error:', e.message);
    }
  } else {
    console.log('  ❌ FAIL - No data returned');
  }

  console.log();
  console.log('='.repeat(70));
  console.log('IC-003c VALIDATION SUMMARY');
  console.log();

  const regressionPass = localUsersResult.success && localAdminsResult.success;
  const newCoveragePass = statusResult.success && rulesResult.success;

  if (regressionPass && newCoveragePass) {
    console.log('✅ COMPREHENSIVE SUCCESS');
    console.log('   IC-001 tools (regression): PASS');
    console.log('   IC-003 tools (new): PASS');
    console.log('   Framework delta: 0% → 100% (multi-line PowerShell)');
  } else if (regressionPass && !newCoveragePass) {
    console.log('⚠️  PARTIAL SUCCESS');
    console.log('   IC-001 tools (regression): PASS');
    console.log('   IC-003 tools (new): FAIL');
    console.log('   Issue: Fix works for single-line but not multi-line');
  } else {
    console.log('❌ REGRESSION DETECTED');
    console.log('   IC-001 broken: Must rollback fix');
  }
}).catch(err => console.error('Error:', err.message));
