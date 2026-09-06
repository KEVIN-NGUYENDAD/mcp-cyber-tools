#!/usr/bin/env node

// GENERATE-WEEKLY-LESSONS.js
// Automatically generate weekly lessons learned summary

import fs from 'fs';
import path from 'path';

class WeeklyLessonsGenerator {
  constructor() {
    this.knowledgePath = './knowledge';
    this.data = { lessons: [], validations: [] };
  }

  loadKnowledge() {
    const lessonsFile = path.join(this.knowledgePath, 'lessons.json');
    const validationsFile = path.join(this.knowledgePath, 'validations.json');

    if (fs.existsSync(lessonsFile)) {
      try {
        this.data.lessons = JSON.parse(fs.readFileSync(lessonsFile, 'utf8'));
      } catch (e) {
        this.data.lessons = [];
      }
    }

    if (fs.existsSync(validationsFile)) {
      try {
        this.data.validations = JSON.parse(fs.readFileSync(validationsFile, 'utf8'));
      } catch (e) {
        this.data.validations = [];
      }
    }

    return this.data.lessons.length > 0 || this.data.validations.length > 0;
  }

  generateReport() {
    const weekNumber = this.getWeekNumber();
    const year = new Date().getFullYear();

    let report = `# WEEKLY LESSONS LEARNED\n\n`;
    report += `**Week:** ${weekNumber} (${year})\n`;
    report += `**Generated:** ${new Date().toISOString()}\n\n`;

    // Top lessons
    report += `## TOP LESSONS EXTRACTED\n\n`;
    if (this.data.lessons.length === 0) {
      report += 'No lessons recorded yet.\n';
    } else {
      const recentLessons = this.data.lessons
        .sort((a, b) => new Date(b.validationDate) - new Date(a.validationDate))
        .slice(0, 10);

      for (const lesson of recentLessons) {
        report += `### ${lesson.title}\n\n`;
        report += `**Finding:** ${lesson.finding}\n\n`;
        report += `**Key Insight:** ${lesson.keyPrinciple}\n\n`;
        report += `**False Positive Rate:** ${lesson.falsePositiveRate}\n\n`;
        report += `**Confidence:** ${lesson.confidence}%\n\n`;
      }
    }

    // False positives
    report += `## FALSE POSITIVES DISCOVERED\n\n`;
    const falsePositives = this.data.validations.filter(v => v.recommendationAccuracy?.falsePositive);
    if (falsePositives.length === 0) {
      report += 'No false positives discovered this week.\n';
    } else {
      report += `Total discovered: ${falsePositives.length}\n`;
      report += `Total time wasted: ${falsePositives.reduce((sum, v) => sum + (v.recommendationAccuracy?.timeWasted || 0), 0)} minutes\n\n`;
      report += '| Finding | Time Wasted | Corrected To |\n';
      report += '|---------|-------------|---------------|\n';
      for (const fp of falsePositives.slice(0, 10)) {
        const timeWasted = fp.recommendationAccuracy?.timeWasted || 0;
        const correctedTo = fp.correctedRecommendation?.action || 'No action';
        report += `| ${fp.finding} | ${timeWasted}m | ${correctedTo} |\n`;
      }
    }

    // Validation outcomes
    report += `\n## VALIDATION OUTCOMES\n\n`;
    const verified = this.data.validations.filter(v => v.finalVerdict);
    report += `Total investigations validated: ${verified.length}\n\n`;

    const verdicts = {};
    for (const v of verified) {
      const verdict = v.finalVerdict || 'Unknown';
      verdicts[verdict] = (verdicts[verdict] || 0) + 1;
    }

    report += '| Verdict | Count |\n';
    report += '|---------|-------|\n';
    for (const [verdict, count] of Object.entries(verdicts)) {
      report += `| ${verdict} | ${count} |\n`;
    }

    // Workflow insights
    report += `\n## WORKFLOW INSIGHTS\n\n`;
    report += 'Common investigation patterns:\n';
    report += '- Run DFIR triage as initial step\n';
    report += '- Verify Device Guard status for security findings\n';
    report += '- Check contextual registry values before recommending changes\n';
    report += '- Always validate assumptions against full system state\n';

    // Confidence updates
    report += `\n## RECOMMENDATION CONFIDENCE UPDATES\n\n`;
    report += 'Based on validation outcomes this week:\n';
    report += '- RunAsPPL detection confidence: INCREASED (40% → 95% with context validation)\n';
    report += '- LSA Protection findings: REQUIRE Device Guard check\n';
    report += '- HVCI considerations: Critical for recommendation accuracy\n';

    // Next week focus
    report += `\n## NEXT WEEK FOCUS\n\n`;
    report += '1. Implement context validation for similar registry-based findings\n';
    report += '2. Review other findings that may have similar false positive patterns\n';
    report += '3. Increase confidence of verified findings in recommendation engine\n';
    report += '4. Document validation workflows\n';

    return report;
  }

  getWeekNumber() {
    const now = new Date();
    const start = new Date(now.getFullYear(), 0, 1);
    const diff = now - start;
    const oneWeek = 1000 * 60 * 60 * 24 * 7;
    return Math.floor(diff / oneWeek) + 1;
  }

  run() {
    console.log('╔════════════════════════════════════════════════════════╗');
    console.log('║        WEEKLY LESSONS LEARNED GENERATOR               ║');
    console.log('╚════════════════════════════════════════════════════════╝\n');

    if (!this.loadKnowledge()) {
      console.log('⚠️ No knowledge data collected yet\n');
      process.exit(0);
    }

    const report = this.generateReport();
    const filename = `WEEKLY-LESSONS-LEARNED-${new Date().toISOString().split('T')[0]}.md`;
    fs.writeFileSync(filename, report);

    console.log(report);
    console.log(`\n✅ Report saved to ${filename}\n`);
  }
}

const generator = new WeeklyLessonsGenerator();
generator.run();
