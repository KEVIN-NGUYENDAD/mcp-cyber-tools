import('./modules/shared.js').then(m => {
  console.log('🏆 IC-003a: EXACT COMMAND REPRODUCTION');
  console.log('='.repeat(70));
  console.log();

  // Exact command from firewall.js that fails
  const problematicCommand = `
    Get-NetFirewallProfile |
    Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction |
    ConvertTo-Json
  `;

  console.log('PROBLEMATIC COMMAND (raw):');
  console.log(JSON.stringify(problematicCommand));
  console.log();

  console.log('AFTER trim() (current IC-001 fix):');
  const trimmed = problematicCommand.trim();
  console.log(JSON.stringify(trimmed));
  console.log();

  console.log('FULL COMMAND SENT TO POWERSHELL:');
  const fullCommand = `powershell -NoProfile -Command "${trimmed}"`;
  console.log(fullCommand);
  console.log();

  console.log('TRYING TO EXECUTE...');
  console.log('-'.repeat(70));

  try {
    const { execSync } = require('child_process');
    const output = execSync(fullCommand, { encoding: 'utf8' });
    console.log('✅ SUCCESS (unexpected)');
    console.log('Output:', output.substring(0, 200));
  } catch (error) {
    console.log('❌ FAILED (as expected)');
    console.log('Error:', error.message.substring(0, 300));
  }

  console.log();
  console.log('='.repeat(70));
  console.log('CANDIDATE FIX: Normalize internal newlines');
  console.log();

  const normalized = problematicCommand
    .trim()
    .replace(/\n\s+/g, ' ');

  console.log('AFTER normalization (candidate fix):');
  console.log(JSON.stringify(normalized));
  console.log();

  console.log('FULL COMMAND WITH FIX:');
  const fixedCommand = `powershell -NoProfile -Command "${normalized}"`;
  console.log(fixedCommand);
  console.log();

  console.log('TESTING FIX...');
  console.log('-'.repeat(70));

  try {
    const { execSync } = require('child_process');
    const output = execSync(fixedCommand, { encoding: 'utf8' });
    console.log('✅ FIX WORKS');
    console.log('Output length:', output.length);
    console.log('Output preview:', output.substring(0, 200));
  } catch (error) {
    console.log('❌ FIX DOES NOT WORK');
    console.log('Error:', error.message.substring(0, 300));
  }
}).catch(err => console.error('Error:', err.message));
