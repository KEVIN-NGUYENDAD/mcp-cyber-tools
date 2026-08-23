import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const improvementsDir = path.join(__dirname, '..', 'improvements');

try {
  const files = fs.readdirSync(improvementsDir).filter(f => f.endsWith('.json')).sort();

  console.log('\n' + '='.repeat(70));
  console.log('CYBER-TOOLS RECOMMENDATION FACTORY');
  console.log('='.repeat(70) + '\n');

  let totalGenerated = 0;
  let totalValidated = 0;

  files.forEach(file => {
    const data = JSON.parse(fs.readFileSync(path.join(improvementsDir, file), 'utf8'));

    console.log(`\n📋 ${data.cycle}: ${data.problem}`);
    console.log('-'.repeat(70));
    console.log(`   Cause: ${data.cause}`);
    console.log(`   Confidence: ${data.confidence}%`);
    console.log(`   Status: ${data.recommendation_status || 'PENDING'}\n`);

    if (data.recommended_actions && data.recommended_actions.length > 0) {
      console.log('   Recommended Actions:');
      data.recommended_actions.forEach((action, idx) => {
        const icon = action.priority === 'HIGH' ? '🔴' : action.priority === 'MEDIUM' ? '🟡' : '🟢';
        console.log(`   ${idx + 1}. ${icon} [${action.priority}] ${action.action}`);
        console.log(`      Effort: ${action.effort} | Expected Delta: +${action.expected_delta}%`);
      });
      totalGenerated += data.recommended_actions.length;

      if (data.recommendation_status === 'VALIDATED') {
        totalValidated += data.recommended_actions.length;
      }
    }
  });

  console.log('\n' + '='.repeat(70));
  console.log('FACTORY METRICS');
  console.log('='.repeat(70));
  console.log(`   Generated:  ${totalGenerated} recommendations`);
  console.log(`   Validated:  ${totalValidated} recommendations`);
  console.log(`   Success Rate: ${totalGenerated > 0 ? Math.round((totalValidated / totalGenerated) * 100) : 0}%\n`);
  console.log('='.repeat(70) + '\n');

  process.exit(0);
} catch (error) {
  console.error('Error:', error.message);
  process.exit(1);
}
