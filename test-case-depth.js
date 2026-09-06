#!/usr/bin/env node

import { investigatePersistence } from './src/playbooks/investigatePersistence.js';
import { incidentResponse } from './src/playbooks/incidentResponse.js';
import { calculateAndUpdateRisk } from './src/risk/riskEngine.js';
import { rankAndUpdateRecommendations } from './src/recommendations/rankingEngine.js';
import { renderTimeline, getTimelineMetrics } from './src/cases/timelineRenderer.js';
import { generateExecutiveSummary, generateMarkdownSummary } from './src/cases/summaryGenerator.js';
import { loadCase } from './src/cases/caseManager.js';
import fs from 'fs/promises';

async function demonstrateCaseDepth() {
  console.log('🎯 CASE DEPTH DEMONSTRATION\n');
  console.log('═'.repeat(60));

  try {
    // Create two different cases
    console.log('\n📋 PHASE 1: Create Investigation & Incident Cases\n');

    console.log('[A] Persistence Investigation...');
    const investigation = await investigatePersistence();
    console.log(`    ✅ ${investigation.caseId} - ${investigation.findings.length} findings\n`);

    console.log('[B] Critical Incident Response...');
    const incident = await incidentResponse('malware');
    console.log(`    ✅ ${incident.caseId} - Severity: ${incident.severity}\n`);

    const cases = [
      { id: investigation.caseId, name: 'Persistence Investigation' },
      { id: incident.caseId, name: 'Malware Incident' }
    ];

    // Apply depth engines
    console.log('📋 PHASE 2: Enhance Cases with Depth Engines\n');

    for (const caseInfo of cases) {
      console.log(`Processing ${caseInfo.name}...\n`);

      // Risk scoring
      console.log('  1. Calculating risk score...');
      const risk = await calculateAndUpdateRisk(caseInfo.id);
      console.log(`     Risk: ${risk.score}/100 (${risk.level})`);

      // Recommendation ranking
      console.log('  2. Ranking recommendations...');
      const ranked = await rankAndUpdateRecommendations(caseInfo.id);
      const recommended = ranked.filter(r => r.recommended);
      console.log(`     Recommended: ${recommended.length}/${ranked.length}`);

      // Timeline metrics
      console.log('  3. Generating timeline metrics...');
      const metrics = await getTimelineMetrics(caseInfo.id);
      console.log(`     Duration: ${metrics.durationSeconds}s, Events: ${metrics.totalEvents}`);

      // Executive summary
      console.log('  4. Generating executive summary...');
      const summary = await generateExecutiveSummary(caseInfo.id);
      console.log(`     Key Takeaway: ${summary.keyTakeaway}`);
      console.log();
    }

    // Display results
    console.log('═'.repeat(60));
    console.log('\n📊 PHASE 3: Formatted Case Output\n');

    for (const caseInfo of cases) {
      console.log(`\n${'─'.repeat(60)}`);
      console.log(`${caseInfo.name.toUpperCase()}`);
      console.log(`${'─'.repeat(60)}\n`);

      // Get summary
      const summary = await generateExecutiveSummary(caseInfo.id);

      console.log(`Case ID: ${summary.caseId}`);
      console.log(`Risk: ${summary.riskScore}/100 (${summary.riskLevel.toUpperCase()})`);
      console.log(`Status: ${summary.status}`);
      console.log();

      console.log('INTERPRETATION:');
      console.log(`  ${summary.interpretation}`);
      console.log();

      console.log('KEY FINDING:');
      console.log(`  ${summary.keyTakeaway}`);
      console.log();

      console.log('RECOMMENDED FIRST ACTION:');
      console.log(`  ${summary.recommendedAction}`);
      console.log();

      if (summary.topRecommendations.length > 0) {
        console.log('ALL RECOMMENDED ACTIONS:');
        summary.topRecommendations.forEach((rec, idx) => {
          console.log(`  [${idx + 1}] ${rec.title} (${rec.confidence}% confidence)`);
        });
        console.log();
      }

      console.log(`FINDINGS (${summary.findingCount} total):`);
      summary.findings.forEach(f => {
        console.log(`  • ${f.title} (${f.severity})`);
      });
      console.log();
    }

    console.log('═'.repeat(60));
    console.log('\n🏆 CASE DEPTH DEMONSTRATION: PASS ✅\n');
    console.log('Transformation Pipeline:');
    console.log('  Raw Case → Risk Scoring → Recommendation Ranking');
    console.log('           → Timeline Metrics → Executive Summary');
    console.log();
    console.log('From "we have a case" to "here is what you need to do"');
    console.log('Framework: Going from breadth (5 playbooks) to depth (usable cases)\n');

    return true;

  } catch (error) {
    console.error('\n❌ TEST FAILED:\n', error.message);
    console.error(error.stack);
    return false;
  }
}

const success = await demonstrateCaseDepth();
process.exit(success ? 0 : 1);
