import fs from 'fs';
import { paths } from './paths.js';

console.log('═'.repeat(60));
console.log('PATHS CONFIGURATION VERIFICATION');
console.log('═'.repeat(60) + '\n');

console.log('Project Root:', paths.projectRoot);
console.log('State Directory:', paths.stateDir);
console.log('');

const filesToCheck = [
  { name: 'Incidents', path: paths.incidents },
  { name: 'Assets', path: paths.assets },
  { name: 'Risk Score', path: paths.riskScore },
  { name: 'WAAP Status', path: paths.waapStatus },
  { name: 'Domain Status', path: paths.domainStatus },
  { name: 'Notification History', path: paths.notificationHistory },
  { name: 'Processed Incidents', path: paths.processedIncidents },
  { name: 'Approval Audit', path: paths.approvalAudit },
];

console.log('State Files Check:');
console.log('─'.repeat(60));

let allOk = true;
for (const file of filesToCheck) {
  const exists = fs.existsSync(file.path);
  const status = exists ? '✅' : '⚠️ ';
  console.log(`${status} ${file.name.padEnd(25)}: ${file.path}`);
  if (exists) {
    const data = JSON.parse(fs.readFileSync(file.path, 'utf8'));
    const size = JSON.stringify(data).length;
    console.log(`   └─ Size: ${size} bytes, Keys: ${Object.keys(data).length}`);
  } else {
    allOk = false;
  }
}

console.log('\n' + '─'.repeat(60));
if (allOk) {
  console.log('✅ ALL STATE FILES ACCESSIBLE - PATHS CONFIGURED CORRECTLY');
} else {
  console.log('⚠️  SOME STATE FILES MISSING - BOT MAY FAIL');
}
console.log('═'.repeat(60));

// Test reading actual data
console.log('\nSample Data Validation:');
console.log('─'.repeat(60));

try {
  const incidents = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
  console.log(`✅ Incidents: ${incidents.total_incidents || incidents.length || 0} total`);
  if (incidents.by_severity) {
    console.log(`   CRITICAL: ${incidents.by_severity.CRITICAL}, HIGH: ${incidents.by_severity.HIGH}`);
  }
} catch (e) {
  console.log('❌ Failed to read incidents');
}

try {
  const assets = JSON.parse(fs.readFileSync(paths.assets, 'utf8'));
  console.log(`✅ Assets: ${assets.total_assets || 0} devices`);
} catch (e) {
  console.log('❌ Failed to read assets');
}

try {
  const risk = JSON.parse(fs.readFileSync(paths.riskScore, 'utf8'));
  console.log(`✅ Risk Score: ${risk.overall_score || 0}/100`);
} catch (e) {
  console.log('❌ Failed to read risk score');
}

console.log('\n' + '═'.repeat(60));
console.log('VERIFICATION COMPLETE\n');
