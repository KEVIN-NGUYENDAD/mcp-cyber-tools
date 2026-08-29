#!/usr/bin/env node
import { runPowerShell, formatResponse } from './modules/shared.js';
import { instrumentTool } from './modules/telemetry.js';
import fs from 'fs';

console.log('Testing real MCP tool execution...\n');

// Real tool from modules/host.js
const whoamiTool = async () => {
  const result = runPowerShell("[System.Security.Principal.WindowsIdentity]::GetCurrent().Name");
  return formatResponse(result.success, result.data, result.error);
};

// Wrap with telemetry (same as server.tool() does)
const wrappedWhoami = instrumentTool('whoami', whoamiTool);

// Execute it
console.log('Executing: whoami\n');
const result = await wrappedWhoami();
console.log('Result:', result);

// Check telemetry
console.log('\n---\n');
const telemetryFile = './telemetry/telemetry-2026-08-23.json';
const telemetry = JSON.parse(fs.readFileSync(telemetryFile, 'utf8'));

console.log('Telemetry records:', telemetry.length);
console.log('\nLast 2 records:');
for (const record of telemetry.slice(-2)) {
  console.log(`  toolName: ${record.toolName}`);
  console.log(`  success: ${record.success}`);
  console.log(`  duration: ${record.duration}ms\n`);
}

// Verify
const hasRealTool = telemetry.some(r => r.toolName === 'whoami');
console.log(`✓ Real tool "whoami" recorded: ${hasRealTool}`);
