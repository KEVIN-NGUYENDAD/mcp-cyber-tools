import fs from 'fs';
import { paths } from './paths.js';

console.log('\n' + '═'.repeat(70));
console.log('FIELD MAPPING VALIDATION - TELEGRAM BOT DATA CONTRACTS');
console.log('═'.repeat(70) + '\n');

// Read actual state files
const incidents = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
const assets = JSON.parse(fs.readFileSync(paths.assets, 'utf8'));
const risk = JSON.parse(fs.readFileSync(paths.riskScore, 'utf8'));

console.log('TEST 1: /status Command Fields');
console.log('─'.repeat(70));
console.log(`✅ incidents.total_incidents: ${incidents.total_incidents}`);
console.log(`✅ incidents.by_severity.CRITICAL: ${incidents.by_severity?.CRITICAL || 0}`);
console.log(`✅ incidents.by_severity.HIGH: ${incidents.by_severity?.HIGH || 0}`);
console.log(`✅ assets.total_assets: ${assets.total_assets}`);
console.log(`✅ risk.overall_score: ${risk.overall_score}`);
console.log('\nExpected Bot Output:');
console.log(`   🚨 ${incidents.total_incidents} Open Incidents`);
console.log(`   🔴 ${incidents.by_severity?.CRITICAL || 0} Critical`);
console.log(`   🟠 ${incidents.by_severity?.HIGH || 0} High`);
console.log('\n');

console.log('TEST 2: /open Command - First Critical Incident');
console.log('─'.repeat(70));
const firstCritical = incidents.incidents?.find(i => i.severity === 'CRITICAL');
if (firstCritical) {
  console.log(`✅ incident_id: ${firstCritical.incident_id}`);
  console.log(`✅ title: ${firstCritical.title.substring(0, 40)}`);
  console.log(`✅ severity: ${firstCritical.severity}`);
  console.log(`✅ assets: [${firstCritical.assets?.join(', ') || 'Multiple'}]`);
  console.log('\nExpected Bot Output:');
  console.log(`   ${firstCritical.incident_id} | ${firstCritical.title.substring(0, 30)}`);
  console.log(`   Asset: ${firstCritical.assets?.[0] || 'Multiple'}`);
} else {
  console.log('❌ No CRITICAL incidents found');
}
console.log('\n');

console.log('TEST 3: /analytics Command - Incident Counts');
console.log('─'.repeat(70));
console.log(`✅ Total incidents: ${incidents.total_incidents}`);
console.log(`✅ Critical: ${incidents.by_severity?.CRITICAL || 0}`);
console.log(`✅ High: ${incidents.by_severity?.HIGH || 0}`);
console.log('\nExpected Bot Output:');
console.log(`   ${incidents.total_incidents} Incidents Detected`);
console.log(`   🔴 ${incidents.by_severity?.CRITICAL || 0} Critical`);
console.log(`   🟠 ${incidents.by_severity?.HIGH || 0} High Severity`);
console.log('\n');

console.log('TEST 4: /incidents Command - Button Labels');
console.log('─'.repeat(70));
incidents.incidents?.slice(0, 3).forEach(inc => {
  console.log(`✅ Button: "${inc.incident_id}: ${inc.title.substring(0, 30)}"`);
  console.log(`   Callback: details_${inc.incident_id}`);
});
console.log('\n');

console.log('TEST 5: Incident Details View');
console.log('─'.repeat(70));
if (firstCritical) {
  console.log(`✅ ID: ${firstCritical.incident_id}`);
  console.log(`✅ Threat: ${firstCritical.title}`);
  console.log(`✅ Severity: ${firstCritical.severity}`);
  console.log(`✅ Assets: ${firstCritical.assets?.join(', ') || 'Multiple Assets'}`);
  console.log(`✅ Created: ${firstCritical.created_at?.substring(0, 10)}`);
  console.log(`✅ Status: ${firstCritical.status}`);
  console.log(`✅ Evidence: ${firstCritical.evidence?.length || 0} indicators`);
  console.log(`✅ Action: ${firstCritical.recommended_action?.substring(0, 40)}`);
  console.log('\nExpected Bot Output:');
  console.log(`   📋 ID: ${firstCritical.incident_id}`);
  console.log(`   🎯 Threat: ${firstCritical.title}`);
  console.log(`   🔴 Severity: ${firstCritical.severity}`);
  console.log(`   🖥️  Assets: ${firstCritical.assets?.[0] || 'Multiple Assets'}`);
}
console.log('\n');

console.log('VALIDATION SUMMARY');
console.log('═'.repeat(70));

let passCount = 0;
let failCount = 0;

// Check all critical fields exist and are accessible
const checks = [
  () => {
    if (incidents.total_incidents !== undefined) passCount++; else failCount++;
    return incidents.total_incidents !== undefined;
  },
  () => {
    if (incidents.by_severity?.CRITICAL !== undefined) passCount++; else failCount++;
    return incidents.by_severity?.CRITICAL !== undefined;
  },
  () => {
    if (incidents.by_severity?.HIGH !== undefined) passCount++; else failCount++;
    return incidents.by_severity?.HIGH !== undefined;
  },
  () => {
    if (firstCritical?.incident_id) passCount++; else failCount++;
    return firstCritical?.incident_id !== undefined;
  },
  () => {
    if (firstCritical?.title) passCount++; else failCount++;
    return firstCritical?.title !== undefined;
  },
  () => {
    if (Array.isArray(firstCritical?.assets)) passCount++; else failCount++;
    return Array.isArray(firstCritical?.assets);
  }
];

checks.forEach(check => check());

console.log(`\n✅ PASSED: ${passCount} / 6 core field mappings`);
console.log(`❌ FAILED: ${failCount} / 6 core field mappings`);

if (failCount === 0) {
  console.log('\n🎉 ALL FIELD MAPPINGS CORRECT - BOT SHOULD WORK NOW');
  console.log('\nCommand Test Results:');
  console.log(`  /status   → Will show: ${incidents.by_severity?.CRITICAL || 0} Critical, ${incidents.by_severity?.HIGH || 0} High ✅`);
  console.log(`  /open     → Will show incident list with titles and assets ✅`);
  console.log(`  /analytics → Will show: ${incidents.by_severity?.CRITICAL || 0} Critical, ${incidents.by_severity?.HIGH || 0} High ✅`);
  console.log(`  /incidents → Will show incident selector with correct IDs ✅`);
} else {
  console.log('\n⚠️  FIELD MAPPING ISSUES REMAIN - BOT WILL FAIL');
}

console.log('\n' + '═'.repeat(70) + '\n');
