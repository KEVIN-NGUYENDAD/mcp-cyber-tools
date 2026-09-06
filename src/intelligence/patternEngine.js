import fs from 'fs/promises';
import path from 'path';

const PATTERNS_DIR = 'patterns';

async function ensurePatternsDir() {
  await fs.mkdir(PATTERNS_DIR, { recursive: true });
}

function generatePatternId(sequence) {
  // Create deterministic ID from sequence
  const normalized = sequence.map(s => s.toLowerCase()).join('→');
  return `PATTERN-${Math.abs(normalized.split('').reduce((acc, c) => acc * 31 + c.charCodeAt(0), 0)) % 10000}`;
}

function getPatternFile(patternId) {
  return path.join(PATTERNS_DIR, `${patternId}.json`);
}

export async function recordPattern(sequence, confidence, caseIds = []) {
  if (!sequence || sequence.length < 2) {
    throw new Error('Pattern requires at least 2 steps in sequence');
  }

  await ensurePatternsDir();

  const patternId = generatePatternId(sequence);
  const filePath = getPatternFile(patternId);
  const now = new Date().toISOString();

  let pattern;
  try {
    pattern = JSON.parse(await fs.readFile(filePath, 'utf-8'));
    // Pattern exists, update
    pattern.occurrences += 1;
    pattern.lastSeen = now;
    pattern.casesObserved = [...new Set([...pattern.casesObserved, ...caseIds])];

    // Recalculate confidence based on occurrences
    pattern.confidence = Math.min(
      confidence + (pattern.occurrences - 1) * 1.5,
      99
    );
  } catch (e) {
    // New pattern
    pattern = {
      patternId,
      sequence,
      firstSeen: now,
      lastSeen: now,
      occurrences: 1,
      confidence,
      casesObserved: caseIds,
      type: categorizePattern(sequence),
      severity: estimateSeverity(sequence),
      description: generateDescription(sequence)
    };
  }

  await fs.writeFile(filePath, JSON.stringify(pattern, null, 2));
  return pattern;
}

function categorizePattern(sequence) {
  const joined = sequence.join(' ').toLowerCase();

  if (joined.includes('persistence') && joined.includes('privilege')) {
    return 'privilege-escalation-chain';
  }
  if (joined.includes('privilege') && joined.includes('lateral')) {
    return 'lateral-movement-chain';
  }
  if (joined.includes('lateral') && (joined.includes('exfil') || joined.includes('data'))) {
    return 'data-exfiltration-chain';
  }
  if (joined.includes('persistence') && joined.includes('lateral')) {
    return 'persistence-lateral-chain';
  }
  if (joined.includes('credential') && joined.includes('access')) {
    return 'credential-access-chain';
  }

  return 'generic-attack-chain';
}

function estimateSeverity(sequence) {
  const depth = sequence.length;
  const hasExfil = sequence.join(' ').toLowerCase().includes('exfil');
  const hasCred = sequence.join(' ').toLowerCase().includes('credential');
  const hasLateral = sequence.join(' ').toLowerCase().includes('lateral');

  if (hasExfil) return 'critical';
  if (hasCred && hasLateral) return 'high';
  if (depth >= 4) return 'high';
  if (depth === 3) return 'medium';
  if (depth === 2 && (sequence.join(' ').toLowerCase().includes('privilege'))) return 'medium';
  return 'low';
}

function generateDescription(sequence) {
  return `Attack progression: ${sequence.join(' → ')}`;
}

export async function getPattern(patternId) {
  await ensurePatternsDir();

  try {
    const filePath = getPatternFile(patternId);
    return JSON.parse(await fs.readFile(filePath, 'utf-8'));
  } catch (e) {
    return null;
  }
}

export async function getAllPatterns() {
  await ensurePatternsDir();

  const files = await fs.readdir(PATTERNS_DIR);
  const patterns = [];

  for (const file of files) {
    if (file.endsWith('.json')) {
      try {
        const data = JSON.parse(await fs.readFile(path.join(PATTERNS_DIR, file), 'utf-8'));
        patterns.push(data);
      } catch (e) {
        // Skip malformed files
      }
    }
  }

  return patterns.sort((a, b) => b.confidence - a.confidence);
}

export async function findPatternMatch(currentSequence) {
  const allPatterns = await getAllPatterns();

  // Look for patterns that start with current sequence
  const matches = [];

  for (const pattern of allPatterns) {
    // Check if current sequence matches the beginning of pattern
    const isPrefix = currentSequence.length <= pattern.sequence.length &&
      currentSequence.every((step, idx) =>
        step.toLowerCase() === pattern.sequence[idx].toLowerCase()
      );

    if (isPrefix) {
      matches.push({
        pattern,
        nextStep: pattern.sequence[currentSequence.length],
        remainingSteps: pattern.sequence.slice(currentSequence.length),
        matchConfidence: pattern.confidence,
        occurrences: pattern.occurrences
      });
    }
  }

  return matches.sort((a, b) => b.matchConfidence - a.matchConfidence);
}

export async function getPatternStatistics() {
  const patterns = await getAllPatterns();

  const stats = {
    totalPatterns: patterns.length,
    highConfidence: patterns.filter(p => p.confidence >= 80).length,
    criticalSeverity: patterns.filter(p => p.severity === 'critical').length,
    totalObservations: patterns.reduce((sum, p) => sum + p.occurrences, 0),
    averageConfidence: patterns.length > 0
      ? Math.round(patterns.reduce((sum, p) => sum + p.confidence, 0) / patterns.length)
      : 0,
    patternsByType: {},
    topPatterns: patterns.slice(0, 5)
  };

  // Count by type
  for (const pattern of patterns) {
    stats.patternsByType[pattern.type] = (stats.patternsByType[pattern.type] || 0) + 1;
  }

  return stats;
}

export async function recordComparisonAsPattern(comparison) {
  // Extract pattern from case comparison
  const sequence = [];

  // Add detected patterns as steps
  for (const pattern of comparison.patterns) {
    sequence.push(pattern.name);
  }

  if (sequence.length < 2) {
    return null;
  }

  const caseIds = [comparison.cases.case1.id, comparison.cases.case2.id];
  const confidence = comparison.patterns.length > 0
    ? Math.round(comparison.patterns.reduce((sum, p) => sum + p.confidence, 0) / comparison.patterns.length)
    : 75;

  return await recordPattern(sequence, confidence, caseIds);
}

export const mcp_patternEngine = {
  name: 'patternEngine',
  description: 'Record and recognize attack patterns from case comparisons',
  methods: {
    recordPattern,
    getPattern,
    getAllPatterns,
    findPatternMatch,
    getPatternStatistics,
    recordComparisonAsPattern
  }
};
