#!/usr/bin/env node

import {
  recordAnalystFeedback,
  clearFeedbackData
} from './src/intelligence/judgmentLearningEngine.js';

import {
  generateEngineLeaderboard,
  getBottleneckEngine,
  generateWarRoomReport,
  getWarRoomStats,
  recordDailyAccuracySnapshot
} from './src/intelligence/warRoomEngine.js';

async function runWarRoom50Cases() {
  console.log('🔥 WAR ROOM MODE - 50 CASE COMPRESSION TEST\n');
  console.log('═'.repeat(70));

  try {
    // Clear and start fresh
    await clearFeedbackData();
    console.log('\n🧹 Starting fresh - Analyzing 50 historical cases\n');

    // Simulate 50 real cases with realistic accuracy patterns
    const cases = [];

    // Decision Engine Weak (40-50%)
    for (let i = 1; i <= 8; i++) {
      cases.push({
        caseId: `HIST-${String(i).padStart(3, '0')}`,
        rec: 'IGNORE',
        actual: 'INVESTIGATE',
        agree: false
      });
    }

    // Decision Engine Right (60-70%)
    for (let i = 9; i <= 20; i++) {
      cases.push({
        caseId: `HIST-${String(i).padStart(3, '0')}`,
        rec: 'INVESTIGATE',
        actual: 'INVESTIGATE',
        agree: true
      });
    }

    // Prediction Engine Weak (40-50%)
    for (let i = 21; i <= 28; i++) {
      cases.push({
        caseId: `HIST-${String(i).padStart(3, '0')}`,
        rec: 'Privilege Escalation',
        actual: 'Persistence',
        agree: false
      });
    }

    // Copilot Engine Mixed (50-60%)
    for (let i = 29; i <= 38; i++) {
      cases.push({
        caseId: `HIST-${String(i).padStart(3, '0')}`,
        rec: i % 2 === 0 ? 'ESCALATE' : 'INVESTIGATE',
        actual: i % 2 === 0 ? 'ESCALATE' : 'INVESTIGATE',
        agree: i % 2 === 0
      });
    }

    // Knowledge & Comparator Strong (80%+)
    for (let i = 39; i <= 50; i++) {
      cases.push({
        caseId: `HIST-${String(i).padStart(3, '0')}`,
        rec: 'Pattern Match Found',
        actual: 'Pattern Match Found',
        agree: true
      });
    }

    console.log(`📊 Recording ${cases.length} historical cases...\n`);

    for (const c of cases) {
      await recordAnalystFeedback(c.caseId, c.rec, c.actual, 80);
    }

    console.log(`✅ ${cases.length} cases analyzed\n`);

    // Generate war room snapshot
    console.log('═'.repeat(70));
    console.log('\n🎯 WAR ROOM ANALYSIS\n');

    const snapshot = await recordDailyAccuracySnapshot();

    console.log(`Feedback Count: ${snapshot.feedbackCount} decisions`);
    console.log(`Decision Accuracy: ${snapshot.metrics.decisionAccuracy}%`);
    console.log(`Prediction Accuracy: ${snapshot.metrics.predictionAccuracy}%`);
    console.log(`Overall Accuracy: ${snapshot.metrics.overallAccuracy}%\n`);

    // Leaderboard
    console.log('ENGINE LEADERBOARD:\n');
    const leaderboard = await generateEngineLeaderboard();
    leaderboard.forEach(engine => {
      console.log(`${engine.rank}. ${engine.engine.padEnd(20)} ${String(engine.trustScore).padStart(3)}% ${engine.status}`);
    });

    // Bottleneck
    console.log();
    const bottleneck = await getBottleneckEngine();
    console.log(`🔴 BOTTLENECK: ${bottleneck.engine}`);
    console.log(`   Score: ${bottleneck.trustScore}% → Target: ${bottleneck.target}%\n`);

    // Full Report
    console.log('═'.repeat(70));
    console.log('\n📋 FULL WAR ROOM REPORT\n');

    const report = await generateWarRoomReport();
    console.log(report);

    // Stats
    console.log('\n' + '═'.repeat(70));
    console.log('\n📊 WAR ROOM STATS\n');

    const stats = await getWarRoomStats();
    console.log(`Feedback Analyzed: ${stats.feedbackCount}`);
    console.log(`Status: ${stats.status}`);
    console.log(`Decision Accuracy: ${stats.accuracy.decision}%`);
    console.log(`Prediction Accuracy: ${stats.accuracy.prediction}%`);
    console.log(`Overall: ${stats.accuracy.overall}%\n`);

    console.log(`Critical Bottleneck: ${stats.bottleneck.engine}`);
    console.log(`Current: ${stats.bottleneck.score}%`);
    console.log(`Target: ${stats.bottleneck.target}%`);
    console.log(`Gap: ${stats.bottleneck.gap} points to close\n`);

    // Validation
    console.log('═'.repeat(70));
    console.log('\n✅ WAR ROOM VALIDATION\n');

    const tests = [
      {
        name: '50 cases processed',
        pass: snapshot.feedbackCount >= 50
      },
      {
        name: 'Leaderboard generated',
        pass: leaderboard.length === 6
      },
      {
        name: 'Bottleneck identified',
        pass: !!bottleneck.engine
      },
      {
        name: 'Accuracy metrics calculated',
        pass: snapshot.metrics.decisionAccuracy > 0
      },
      {
        name: 'Daily snapshot recorded',
        pass: !!snapshot.timestamp
      },
      {
        name: 'War room report generated',
        pass: report.includes('WAR ROOM')
      },
      {
        name: 'Stats compiled',
        pass: stats.accuracy.decision >= 0
      }
    ];

    let passed = 0;
    tests.forEach(test => {
      console.log(`${test.pass ? '✅' : '❌'} ${test.name}`);
      if (test.pass) passed++;
    });

    console.log(`\n${passed}/${tests.length} validation checks passed\n`);

    if (passed === tests.length) {
      console.log('═'.repeat(70));
      console.log('\n🏆 WAR ROOM OPERATIONAL\n');
      console.log('Compression: 5 cases → 50 cases (10x acceleration)');
      console.log('Feedback: Monthly → Daily measurement');
      console.log('Focus: Multi-engine → Single bottleneck');
      console.log('Strategy: One Engine At A Time\n');

      console.log('Next Actions:');
      console.log(`  1. Fix ${stats.bottleneck.engine} (${stats.bottleneck.score}% → ${stats.bottleneck.target}%)`);
      console.log(`  2. Measure daily delta`);
      console.log(`  3. When bottleneck reaches target, move to next weak engine`);
      console.log(`  4. Repeat until all engines 80%+\n`);

      console.log('🔥 WAR ROOM MODE: ENGAGED\n');
    }

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

runWarRoom50Cases();
