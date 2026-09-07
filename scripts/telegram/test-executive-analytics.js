import fs from 'fs';
import { paths } from './paths.js';

console.log('\n' + '═'.repeat(70));
console.log('TESTING EXECUTIVE & ANALYTICS HANDLERS');
console.log('═'.repeat(70) + '\n');

console.log('[TEST] paths.stateDir:', paths.stateDir);
console.log('[TEST] File existence checks:');
console.log('  - incidents:', fs.existsSync(paths.incidents));
console.log('  - assets:', fs.existsSync(paths.assets));
console.log('  - riskScore:', fs.existsSync(paths.riskScore));
console.log('  - waapStatus:', fs.existsSync(paths.waapStatus));
console.log('  - domainStatus:', fs.existsSync(paths.domainStatus));

console.log('\n' + '─'.repeat(70));
console.log('LOADING EXECUTIVE DATA');
console.log('─'.repeat(70) + '\n');

let incidents = { total_incidents: 0, by_severity: { CRITICAL: 0, HIGH: 0 } };
let assets = { total_assets: 0 };
let risk = { overall_score: 0 };
let waap = { health_score: 0, ssl_status: 'UNKNOWN', days_until_expiry: 0 };
let domain = { dns_health: 'N/A' };

if (fs.existsSync(paths.incidents)) {
  incidents = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
  console.log('[EXEC-INCIDENTS]', {
    total: incidents.total_incidents,
    critical: incidents.by_severity?.CRITICAL,
    high: incidents.by_severity?.HIGH
  });
} else {
  console.log('[ERROR] Incidents not found');
}

if (fs.existsSync(paths.assets)) {
  assets = JSON.parse(fs.readFileSync(paths.assets, 'utf8'));
  console.log('[EXEC-ASSETS]', { total: assets.total_assets });
} else {
  console.log('[ERROR] Assets not found');
}

if (fs.existsSync(paths.riskScore)) {
  risk = JSON.parse(fs.readFileSync(paths.riskScore, 'utf8'));
  console.log('[EXEC-RISK]', { score: risk.overall_score });
} else {
  console.log('[ERROR] Risk score not found');
}

if (fs.existsSync(paths.waapStatus)) {
  waap = JSON.parse(fs.readFileSync(paths.waapStatus, 'utf8'));
  console.log('[EXEC-WAAP]', { health: waap.health_score, ssl_status: waap.ssl_status });
} else {
  console.log('[ERROR] WAAP status not found');
}

if (fs.existsSync(paths.domainStatus)) {
  domain = JSON.parse(fs.readFileSync(paths.domainStatus, 'utf8'));
  console.log('[EXEC-DOMAIN]', { dns_health: domain.dns_health });
} else {
  console.log('[ERROR] Domain status not found');
}

console.log('\n[EXEC-WOULD-OUTPUT]');
console.log(`${incidents.total_incidents} Open Incidents`);
console.log(`  └ 🔴 ${incidents.by_severity?.CRITICAL || 0} Critical`);
console.log(`  └ 🟠 ${incidents.by_severity?.HIGH || 0} High Severity`);
console.log(`Score: ${risk.overall_score}/100`);
console.log(`DNS Health: ${domain.dns_health || 'N/A'}`);

console.log('\n' + '─'.repeat(70));
console.log('LOADING ANALYTICS DATA');
console.log('─'.repeat(70) + '\n');

// Reset for analytics
incidents = { total_incidents: 0, by_severity: { CRITICAL: 0, HIGH: 0 } };
assets = { total_assets: 0, assets: [] };
risk = { overall_score: 0 };
waap = { health_score: 0, security_summary: {} };
domain = { dns_complete: {} };

if (fs.existsSync(paths.incidents)) {
  incidents = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
  console.log('[ANALYTICS-INCIDENTS]', {
    total: incidents.total_incidents,
    critical: incidents.by_severity?.CRITICAL,
    high: incidents.by_severity?.HIGH
  });
}

if (fs.existsSync(paths.assets)) {
  assets = JSON.parse(fs.readFileSync(paths.assets, 'utf8'));
  console.log('[ANALYTICS-ASSETS]', { total: assets.total_assets, count: assets.assets?.length });
}

if (fs.existsSync(paths.riskScore)) {
  risk = JSON.parse(fs.readFileSync(paths.riskScore, 'utf8'));
  console.log('[ANALYTICS-RISK]', { score: risk.overall_score });
}

if (fs.existsSync(paths.waapStatus)) {
  waap = JSON.parse(fs.readFileSync(paths.waapStatus, 'utf8'));
  console.log('[ANALYTICS-WAAP]', {
    health: waap.health_score,
    ssl_valid: waap.security_summary?.ssl_valid,
    waf_active: waap.security_summary?.waf_active,
    cdn_active: waap.security_summary?.cdn_active,
    protection_active: waap.security_summary?.protection_active
  });
}

if (fs.existsSync(paths.domainStatus)) {
  domain = JSON.parse(fs.readFileSync(paths.domainStatus, 'utf8'));
  console.log('[ANALYTICS-DOMAIN]', { dns_complete: domain.dns_complete });
}

// Calculate vulnerabilities from assets
const totalVulnerabilities = (assets.assets || []).reduce((sum, asset) =>
  sum + (asset.vulnerability_count || 0), 0);

console.log('[ANALYTICS-VULNS]', { total: totalVulnerabilities });

// Calculate WAAP score
const waapScore = (
  (waap.security_summary?.ssl_valid ? 60 : 0) +
  (waap.security_summary?.waf_active ? 15 : 0) +
  (waap.security_summary?.cdn_active ? 15 : 0) +
  (waap.security_summary?.protection_active ? 10 : 0)
);

console.log('[ANALYTICS-WAAP-SCORE]', { calculated: waapScore });

// Calculate DNS health
const dnsChecks = domain.dns_complete || {};
const dnsHealthPercent = Math.round(
  ((Object.values(dnsChecks).filter(v => v === true).length || 0) / 5) * 100
);

console.log('[ANALYTICS-DNS-PERCENT]', { percent: dnsHealthPercent });

console.log('\n[ANALYTICS-WOULD-OUTPUT]');
console.log(`${totalVulnerabilities} Vulnerabilities Found`);
console.log(`${incidents.total_incidents} Issues Aggregated`);
console.log(`Scan Coverage: ${assets.total_assets} Assets`);
console.log(`${incidents.total_incidents} Incidents Detected`);
console.log(`🔴 ${incidents.by_severity?.CRITICAL || 0} Critical`);
console.log(`🟠 ${incidents.by_severity?.HIGH || 0} High Severity`);
console.log(`Score: ${risk.overall_score}/100`);
console.log(`WAAP Score: ${waapScore}/100`);
console.log(`DNS Health: ${dnsHealthPercent}%`);

console.log('\n' + '═'.repeat(70));
console.log('TEST COMPLETE');
console.log('═'.repeat(70) + '\n');
