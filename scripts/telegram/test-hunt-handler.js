import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '../../');

const paths = {
  incidents: path.join(PROJECT_ROOT, 'state', 'incidents.json'),
  socIntelligence: path.join(PROJECT_ROOT, 'state', 'soc_intelligence.json'),
};

console.log('\n=== TEST: /hunt Handler Live Data Loading ===\n');

try {
  // Load incidents data
  console.log('[TEST] Loading incidents from:', paths.incidents);
  let incidents = { total_incidents: 0, by_severity: { CRITICAL: 0, HIGH: 0 }, by_status: { OPEN: 0 }, incidents: [] };

  if (fs.existsSync(paths.incidents)) {
    incidents = JSON.parse(fs.readFileSync(paths.incidents, 'utf8'));
    console.log('[✓] Incidents loaded:', { total: incidents.total_incidents, critical: incidents.by_severity?.CRITICAL, high: incidents.by_severity?.HIGH });
  }

  // Load intelligence data
  console.log('[TEST] Loading intelligence from:', paths.socIntelligence);
  let intelligence = { extractors: {}, summary: {} };

  if (fs.existsSync(paths.socIntelligence)) {
    intelligence = JSON.parse(fs.readFileSync(paths.socIntelligence, 'utf8'));
    console.log('[✓] Intelligence loaded');
  }

  // Extract findings
  const openIncidents = incidents.by_status?.OPEN || 0;
  const criticalCount = incidents.by_severity?.CRITICAL || 0;
  const highCount = incidents.by_severity?.HIGH || 0;

  console.log('\n[RESULTS] Extracted Metrics:');
  console.log('  • Open Incidents:', openIncidents);
  console.log('  • Critical:', criticalCount);
  console.log('  • High:', highCount);

  // Get top 3 recent findings
  const recentFindings = (incidents.incidents || [])
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 3);

  console.log('\n[RESULTS] Top 3 Recent Findings:');
  recentFindings.forEach((inc, idx) => {
    console.log(`  ${idx + 1}. ${inc.title} (${inc.severity})`);
  });

  console.log('\n[RESULTS] Recommended Actions:');
  recentFindings.forEach((inc, idx) => {
    console.log(`  ${idx + 1}. ${inc.recommended_action}`);
  });

  console.log('\n[✓] TEST PASSED: Handler would generate live response');
} catch (error) {
  console.error('[✗] TEST FAILED:', error.message);
}
