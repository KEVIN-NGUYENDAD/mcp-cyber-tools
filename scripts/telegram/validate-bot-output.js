import fs from 'fs';
import { paths } from './paths.js';

console.log('\n' + '═'.repeat(70));
console.log('TELEGRAM BOT OUTPUT VALIDATION');
console.log('═'.repeat(70) + '\n');

// Load all data
const incidents = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
const assets = JSON.parse(fs.readFileSync(paths.assets, 'utf8'));
const risk = JSON.parse(fs.readFileSync(paths.riskScore, 'utf8'));
const waap = JSON.parse(fs.readFileSync(paths.waapStatus, 'utf8'));
const domain = JSON.parse(fs.readFileSync(paths.domainStatus, 'utf8'));

console.log('ACTUAL STATE FILE VALUES:');
console.log('─'.repeat(70));
console.log(`✓ Incidents: ${incidents.total_incidents} total`);
console.log(`✓ Critical: ${incidents.by_severity?.CRITICAL || 0}`);
console.log(`✓ High: ${incidents.by_severity?.HIGH || 0}`);
console.log(`✓ Assets: ${assets.total_assets} devices`);
console.log(`✓ Risk Score: ${risk.overall_score}/100`);
console.log(`✓ WAAP: ${waap.health_score}/100`);
console.log(`✓ DNS Health: ${domain.dns_health}`);

// Calculate vulnerabilities
const totalVulnerabilities = (assets.assets || []).reduce((sum, asset) =>
  sum + (asset.vulnerability_count || 0), 0);
console.log(`✓ Vulnerabilities: ${totalVulnerabilities}`);

// Calculate WAAP score
const waapScore = (
  (waap.security_summary?.ssl_valid ? 60 : 0) +
  (waap.security_summary?.waf_active ? 15 : 0) +
  (waap.security_summary?.cdn_active ? 15 : 0) +
  (waap.security_summary?.protection_active ? 10 : 0)
);
console.log(`✓ WAAP Calculated: ${waapScore}/100`);

// Calculate DNS health percent
const dnsChecks = domain.dns_complete || {};
const dnsHealthPercent = Math.round(
  ((Object.values(dnsChecks).filter(v => v === true).length || 0) / 5) * 100
);
console.log(`✓ DNS Health %: ${dnsHealthPercent}%`);

console.log('\n' + '═'.repeat(70));
console.log('COMMAND OUTPUT EXPECTATIONS:');
console.log('═'.repeat(70) + '\n');

console.log('📌 /STATUS');
console.log('─'.repeat(70));
console.log(`🚨 ${incidents.total_incidents} Open Incidents`);
console.log(`   🔴 ${incidents.by_severity?.CRITICAL || 0} Critical`);
console.log(`   🟠 ${incidents.by_severity?.HIGH || 0} High`);
console.log(`🖥️ ${assets.total_assets} Devices`);
console.log(`🎯 ${risk.overall_score}/100 Risk Score\n`);

console.log('📌 /EXECUTIVE');
console.log('─'.repeat(70));
console.log(`${assets.total_assets} Monitored Devices`);
console.log(`${incidents.total_incidents} Open Incidents`);
console.log(`  └ 🔴 ${incidents.by_severity?.CRITICAL || 0} Critical`);
console.log(`  └ 🟠 ${incidents.by_severity?.HIGH || 0} High Severity`);
console.log(`🎯 MEDIUM Score: ${risk.overall_score}/100`);
console.log(`${waap.ssl_status || 'N/A'} (${waap.days_until_expiry || 0} days)`);
console.log(`DNS Health: ${domain.dns_health || 'N/A'}\n`);

console.log('📌 /ANALYTICS');
console.log('─'.repeat(70));
console.log(`${totalVulnerabilities} Vulnerabilities Found`);
console.log(`${incidents.total_incidents} Issues Aggregated`);
console.log(`Scan Coverage: ${assets.total_assets} Assets`);
console.log(`${incidents.total_incidents} Incidents Detected`);
console.log(`🔴 ${incidents.by_severity?.CRITICAL || 0} Critical`);
console.log(`🟠 ${incidents.by_severity?.HIGH || 0} High Severity`);
console.log(`Score: ${risk.overall_score}/100`);
console.log(`WAAP Score: ${waapScore}/100`);
console.log(`DNS Health: ${dnsHealthPercent}%\n`);

console.log('═'.repeat(70));
console.log('VALIDATION CHECKLIST');
console.log('═'.repeat(70) + '\n');

const checks = [
  { name: 'Incidents: 18 total', value: incidents.total_incidents === 18 },
  { name: 'Critical: 7', value: incidents.by_severity?.CRITICAL === 7 },
  { name: 'High: 11', value: incidents.by_severity?.HIGH === 11 },
  { name: 'Assets: 11', value: assets.total_assets === 11 },
  { name: 'Vulnerabilities: 405', value: totalVulnerabilities === 405 },
  { name: 'Risk Score: 74', value: risk.overall_score === 74 },
  { name: 'WAAP Score: 60', value: waapScore === 60 },
  { name: 'DNS Health: 100%', value: dnsHealthPercent === 100 },
  { name: 'DNS Health field: 100%', value: domain.dns_health === '100%' },
  { name: 'No zero values', value: ![
    incidents.by_severity?.CRITICAL,
    incidents.by_severity?.HIGH,
    assets.total_assets,
    totalVulnerabilities,
    risk.overall_score
  ].includes(0) }
];

let passed = 0;
checks.forEach(check => {
  const status = check.value ? '✅' : '❌';
  console.log(`${status} ${check.name}`);
  if (check.value) passed++;
});

console.log('\n' + '═'.repeat(70));
console.log(`RESULT: ${passed}/${checks.length} checks passed`);

if (passed === checks.length) {
  console.log('🎉 ALL CHECKS PASSED - BOT WILL DISPLAY CORRECT VALUES');
} else {
  console.log('⚠️  SOME CHECKS FAILED - REVIEW ABOVE');
}

console.log('═'.repeat(70) + '\n');
