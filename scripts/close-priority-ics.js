import fs from "fs";

// Load all ICs and identify priority for closure
const ics = fs.readdirSync("improvements")
  .filter(f => f.startsWith("ic-") && f.endsWith(".json"))
  .map(f => {
    const data = JSON.parse(fs.readFileSync(`improvements/${f}`));
    return {
      id: f.replace(".json", ""),
      ...data
    };
  });

// Prioritize for closure
const openICs = ics.filter(ic => ic.recommendation_status === "PENDING");
const prioritized = openICs
  .map(ic => ({
    ...ic,
    roi: (ic.expected_delta || 50) * (ic.confidence / 100) / (ic.recommended_actions[0]?.effort === "LOW" ? 1 : 2)
  }))
  .sort((a, b) => b.roi - a.roi);

console.log(`\n╔════════════════════════════════════════════════════════════════╗`);
console.log(`║           PRIORITY CLOSURE PLAN - ORCHESTRATOR                ║`);
console.log(`╚════════════════════════════════════════════════════════════════╝\n`);

console.log(`Open ICs: ${openICs.length} (LIMIT: 10)`);
console.log(`Closed ICs: ${ics.filter(ic => ic.recommendation_status === "VALIDATED").length}\n`);

console.log(`TOP 5 HIGHEST ROI FOR IMMEDIATE CLOSURE:\n`);

prioritized.slice(0, 5).forEach((ic, i) => {
  console.log(`${i+1}. ${ic.id.toUpperCase()}: ${ic.title}`);
  console.log(`   Problem: ${ic.problem.slice(0, 60)}`);
  console.log(`   ROI: ${ic.roi.toFixed(1)} | Confidence: ${ic.confidence}% | Expected Delta: +${ic.expected_delta}%`);
  console.log(`   Effort: ${ic.recommended_actions[0]?.effort} | Priority: ${ic.recommended_actions[0]?.priority}`);
  console.log();
});

console.log(`\n╔════════════════════════════════════════════════════════════════╗`);
console.log(`CLOSURE STRATEGY`);
console.log(`╚════════════════════════════════════════════════════════════════╝\n`);

console.log(`PHASE 1: Close Top 2 High-ROI ICs`);
console.log(`  ${prioritized[0].id}: ${prioritized[0].title}`);
console.log(`  ${prioritized[1].id}: ${prioritized[1].title}`);
console.log(`  Expected Impact: +${(prioritized[0].expected_delta + prioritized[1].expected_delta)}%\n`);

console.log(`PHASE 2: Reduce open ICs from 12 to 10`);
console.log(`  Close: IC-006 (registry permission pattern fix)`);
console.log(`  Close: IC-008 (registry access pattern fix)`);
console.log(`  Result: 10 open ICs (at limit)\n`);

console.log(`RULE ENFORCEMENT:`);
console.log(`  ✓ Stop creating new ICs`);
console.log(`  ✓ No discovery until closed ICs > 5`);
console.log(`  ✓ Focus on closure velocity, not discovery velocity`);
console.log(`  ✓ KPI: Closed ICs Per Week\n`);
