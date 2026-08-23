import('./modules/shared.js').then(m => {
  console.log('🏆 E3: MCP Firewall Tools Validation');
  console.log('='.repeat(60));
  console.log();

  // Test 1: firewallStatus
  console.log('TEST 1: firewallStatus (Get-NetFirewallProfile)');
  console.log('-'.repeat(60));

  const statusCommand = `
    Get-NetFirewallProfile |
    Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction |
    ConvertTo-Json
  `;

  const statusResult = m.runPowerShell(statusCommand);
  console.log('Result success:', statusResult.success);
  console.log('Result data length:', statusResult.data?.length || 0);

  if (statusResult.success && statusResult.data?.length > 0) {
    try {
      const profiles = JSON.parse(statusResult.data);
      const profileArray = Array.isArray(profiles) ? profiles : [profiles];
      console.log('✅ firewallStatus WORKS');
      console.log('   Profiles found:', profileArray.length);
      profileArray.forEach((p, i) => {
        console.log(`   [${i+1}] ${p.Name} (Enabled: ${p.Enabled})`);
      });
    } catch (e) {
      console.log('❌ Failed to parse JSON:', e.message);
    }
  } else {
    console.log('❌ firewallStatus FAILED (no data)');
  }

  console.log();

  // Test 2: firewallRules
  console.log('TEST 2: firewallRules (Get-NetFirewallRule enabled only)');
  console.log('-'.repeat(60));

  const rulesCommand = `
    Get-NetFirewallRule -Enabled $true |
    Select-Object Name, DisplayName, Direction, Action, Enabled |
    Select-Object -First 10 |
    ConvertTo-Json
  `;

  const rulesResult = m.runPowerShell(rulesCommand);
  console.log('Result success:', rulesResult.success);
  console.log('Result data length:', rulesResult.data?.length || 0);

  if (rulesResult.success && rulesResult.data?.length > 0) {
    try {
      const rules = JSON.parse(rulesResult.data);
      const rulesArray = Array.isArray(rules) ? rules : [rules];
      console.log('✅ firewallRules WORKS');
      console.log('   Rules found (showing first 10):', rulesArray.length);
      rulesArray.slice(0, 3).forEach((r, i) => {
        console.log(`   [${i+1}] ${r.DisplayName} (${r.Direction})`);
      });
    } catch (e) {
      console.log('❌ Failed to parse JSON:', e.message);
    }
  } else {
    console.log('❌ firewallRules FAILED (no data)');
  }

  console.log();
  console.log('='.repeat(60));
  console.log('E3 HYPOTHESIS TEST COMPLETE');
  console.log();

  // Analyze results
  const statusWorks = statusResult.success && statusResult.data?.length > 0;
  const rulesWork = rulesResult.success && rulesResult.data?.length > 0;

  if (statusWorks && rulesWork) {
    console.log('✅ HYPOTHESIS CONFIRMED');
    console.log('   IC-001 Track B fix appears to have fixed Firewall tools');
    console.log('   This suggests a system-wide fix, not domain-specific');
    console.log();
    console.log('Impact Analysis:');
    console.log('  Accounts (localUsers, localAdmins):  0% → 100%');
    console.log('  Firewall (status, rules):            0% → 100%');
    console.log('  System Impact:                       MULTI-DOMAIN');
  } else if (!statusWorks && !rulesWork) {
    console.log('❌ HYPOTHESIS REJECTED');
    console.log('   Firewall tools still failing');
    console.log('   New defect or different root cause');
    console.log('   Continue IC-001 pattern investigation');
  } else {
    console.log('⚠️  PARTIAL RESULTS');
    console.log(`   firewallStatus: ${statusWorks ? '✅' : '❌'}`);
    console.log(`   firewallRules: ${rulesWork ? '✅' : '❌'}`);
    console.log('   Mixed results suggest different mechanisms');
  }
}).catch(err => {
  console.error('Error:', err.message);
});
