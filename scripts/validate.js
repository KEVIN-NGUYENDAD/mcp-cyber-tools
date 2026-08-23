import { execSync } from 'child_process';

console.log('\n' + '='.repeat(50));
console.log('CYBER-TOOLS VALIDATION RUNNER');
console.log('='.repeat(50) + '\n');

const validations = [
  {
    name: 'localUsers',
    cmd: 'powershell -NoProfile -Command "Get-LocalUser | Measure-Object | Select-Object -ExpandProperty Count"'
  },
  {
    name: 'localAdmins',
    cmd: 'powershell -NoProfile -Command "Get-LocalGroupMember -Group \\"Administrators\\" | Measure-Object | Select-Object -ExpandProperty Count"'
  },
  {
    name: 'firewallStatus',
    cmd: 'powershell -NoProfile -Command "Get-NetFirewallProfile | Measure-Object | Select-Object -ExpandProperty Count"'
  },
  {
    name: 'firewallRules',
    cmd: 'powershell -NoProfile -Command "Get-NetFirewallRule | Where-Object {$_.Enabled -eq 1} | Measure-Object | Select-Object -ExpandProperty Count"'
  },
  {
    name: 'securityLog',
    cmd: 'powershell -NoProfile -Command "Get-WinEvent -LogName Security -MaxEvents 1 -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count"'
  }
];

const results = [];
let passCount = 0;
let failCount = 0;

validations.forEach(validation => {
  try {
    const output = execSync(validation.cmd, {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    });

    const count = parseInt(output.trim());
    const status = count > 0 ? 'PASS' : 'FAIL';

    if (status === 'PASS') {
      passCount++;
    } else {
      failCount++;
    }

    results.push({
      name: validation.name,
      status,
      count
    });

    const icon = status === 'PASS' ? '✅' : '❌';
    console.log(`${validation.name.padEnd(20)} ${status.padEnd(6)} ${icon}`);
  } catch (error) {
    failCount++;
    results.push({
      name: validation.name,
      status: 'FAIL',
      error: error.message.substring(0, 80)
    });

    console.log(`${validation.name.padEnd(20)} FAIL     ❌`);
  }
});

console.log('\n' + '-'.repeat(50));
console.log(`Results: ${passCount} PASS, ${failCount} FAIL`);
const overallStatus = failCount === 0 ? 'PASS' : 'FAIL';
console.log(`Overall Status: ${overallStatus}`);
console.log('='.repeat(50) + '\n');

process.exit(failCount > 0 ? 1 : 0);
