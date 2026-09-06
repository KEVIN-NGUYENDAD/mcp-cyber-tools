import fs from 'fs/promises';
import path from 'path';
import { loadCase, saveCase } from '../cases/caseManager.js';

const KNOWLEDGE_DIR = 'knowledge';

async function ensureKnowledgeDir() {
  await fs.mkdir(KNOWLEDGE_DIR, { recursive: true });
}

async function lookupKnowledge(artifactName) {
  await ensureKnowledgeDir();

  const safeFileName = artifactName.toLowerCase().replace(/[^a-z0-9]/g, '-') + '.json';
  const filePath = path.join(KNOWLEDGE_DIR, safeFileName);

  try {
    return JSON.parse(await fs.readFile(filePath, 'utf-8'));
  } catch (e) {
    return null;
  }
}

// Public alias for lookupKnowledge
export const lookupArtifact = lookupKnowledge;

function enrichFindingWithKnowledge(finding, knowledge) {
  if (!knowledge) {
    return finding;
  }

  const cases = knowledge.cases || knowledge.casesObserved || [];

  return {
    ...finding,
    knowledgeContext: {
      seenBefore: true,
      seenCount: knowledge.seenCount,
      incidentCount: knowledge.incidentCount,
      confidence: knowledge.confidence,
      classification: knowledge.classification,
      casesObserved: cases.length
    },
    enhancedConfidence: Math.max(finding.confidence || 0, knowledge.confidence || 0),
    enhancedClassification: knowledge.classification || finding.classification
  };
}

function calculateConfidence(seenCount, incidentCount) {
  if (seenCount === 0) return 0;

  const incidentRatio = incidentCount / seenCount;

  // Confidence based on pattern: legitimate items have low incident ratio
  if (incidentRatio === 0) {
    // All observations were clean
    return Math.min(90 + Math.log10(seenCount + 1) * 5, 99);
  } else if (incidentRatio < 0.25) {
    // Most were clean
    return Math.min(75 + Math.log10(seenCount + 1) * 3, 90);
  } else if (incidentRatio < 0.75) {
    // Mixed
    return Math.min(50 + Math.log10(seenCount + 1) * 2, 75);
  } else {
    // Mostly incidents
    return Math.min(30 + Math.log10(seenCount + 1), 60);
  }
}

export async function learnArtifact(artifactName, classification, isIncident = false, caseId = null) {
  await ensureKnowledgeDir();

  const safeFileName = artifactName.toLowerCase().replace(/[^a-z0-9]/g, '-') + '.json';
  const filePath = path.join(KNOWLEDGE_DIR, safeFileName);
  const now = new Date().toISOString();

  let knowledge;
  try {
    knowledge = JSON.parse(await fs.readFile(filePath, 'utf-8'));
  } catch (e) {
    // New artifact
    knowledge = {
      artifact: artifactName,
      firstSeen: now,
      seenCount: 0,
      incidentCount: 0,
      classification: 'unknown',
      confidence: 0,
      cases: []
    };
  }

  // Update counts
  knowledge.seenCount += 1;
  if (isIncident) {
    knowledge.incidentCount += 1;
  }

  // Update classification (weighted towards legitimate if confidence is growing)
  if (classification === 'legitimate' && knowledge.classification !== 'malicious') {
    knowledge.classification = 'legitimate';
  } else if (classification === 'malicious') {
    knowledge.classification = 'malicious';
  }

  // Update timestamps
  knowledge.lastSeen = now;

  // Add case if provided and not already present
  if (caseId && !knowledge.cases.includes(caseId)) {
    knowledge.cases.push(caseId);
  }

  // Recalculate confidence
  knowledge.confidence = calculateConfidence(knowledge.seenCount, knowledge.incidentCount);

  // Persist
  await fs.writeFile(filePath, JSON.stringify(knowledge, null, 2));

  return knowledge;
}

export async function updateConfidence(artifactName) {
  const knowledge = await lookupKnowledge(artifactName);

  if (!knowledge) {
    return null;
  }

  await ensureKnowledgeDir();
  const safeFileName = artifactName.toLowerCase().replace(/[^a-z0-9]/g, '-') + '.json';
  const filePath = path.join(KNOWLEDGE_DIR, safeFileName);

  // Recalculate confidence based on current counts
  knowledge.confidence = calculateConfidence(knowledge.seenCount, knowledge.incidentCount);
  knowledge.updatedAt = new Date().toISOString();

  await fs.writeFile(filePath, JSON.stringify(knowledge, null, 2));

  return knowledge;
}

export async function applyKnowledgeLayer(caseId) {
  const caseData = await loadCase(caseId);

  if (!caseData.findings || caseData.findings.length === 0) {
    return { enhanced: 0, insights: [] };
  }

  const insights = [];
  let enhancedCount = 0;

  for (const finding of caseData.findings) {
    const knowledge = await lookupKnowledge(finding.title);

    if (knowledge) {
      const enriched = enrichFindingWithKnowledge(finding, knowledge);

      // Update the finding in the case
      const index = caseData.findings.indexOf(finding);
      caseData.findings[index] = enriched;
      enhancedCount++;

      insights.push({
        artifact: finding.title,
        knownGood: knowledge.classification === 'legitimate',
        seenBefore: knowledge.seenCount,
        incidents: knowledge.incidentCount,
        confidence: knowledge.confidence
      });
    }
  }

  // Add knowledge layer metadata to case
  caseData.knowledgeEnrichment = {
    appliedAt: new Date().toISOString(),
    enhancedFindings: enhancedCount,
    insights
  };

  await saveCase(caseId, caseData);

  return { enhanced: enhancedCount, insights };
}

export async function getArtifactHistory(artifactName) {
  const knowledge = await lookupKnowledge(artifactName);

  if (!knowledge) {
    return null;
  }

  const cases = knowledge.cases || knowledge.casesObserved || [];

  return {
    artifact: knowledge.artifact,
    firstSeen: knowledge.firstSeen,
    lastSeen: knowledge.lastSeen,
    seenCount: knowledge.seenCount,
    incidentCount: knowledge.incidentCount,
    confidence: knowledge.confidence,
    classification: knowledge.classification,
    observedInCases: cases,
    recommendation: knowledge.confidence >= 95
      ? 'Known Good - Skip detailed analysis'
      : knowledge.confidence <= 50
      ? 'Suspicious - Escalate for review'
      : 'Standard Analysis'
  };
}

export async function getKnowledgeInsights(caseId) {
  const caseData = await loadCase(caseId);

  if (!caseData.knowledgeEnrichment) {
    return { message: 'No knowledge enrichment applied' };
  }

  const insights = caseData.knowledgeEnrichment.insights;
  const knownGood = insights.filter(i => i.knownGood).length;
  const suspicious = insights.filter(i => !i.knownGood && i.incidents > 0).length;

  return {
    totalEnhanced: caseData.knowledgeEnrichment.enhancedFindings,
    knownGood,
    suspicious,
    insights,
    summary: `${knownGood} known good artifacts, ${suspicious} suspicious patterns detected from history`
  };
}

export async function buildCorrelationFromKnowledge(caseId) {
  const caseData = await loadCase(caseId);
  const correlations = [];

  if (!caseData.knowledgeEnrichment || caseData.knowledgeEnrichment.insights.length === 0) {
    return correlations;
  }

  const insights = caseData.knowledgeEnrichment.insights;

  // Look for patterns in knowledge
  const softwareStack = insights.filter(i => i.knownGood);
  if (softwareStack.length >= 2) {
    correlations.push({
      pattern: 'Known Software Stack',
      confidence: 90 + Math.min(softwareStack.length * 2, 9),
      evidence: softwareStack.map(i => i.artifact),
      type: 'legitimate'
    });
  }

  const suspicious = insights.filter(i => !i.knownGood && i.incidents > 0);
  if (suspicious.length >= 2) {
    correlations.push({
      pattern: 'Suspicious Activity Pattern',
      confidence: 85,
      evidence: suspicious.map(i => i.artifact),
      type: 'malicious'
    });
  }

  return correlations;
}

// Public alias for getArtifactHistory
export const getHistory = getArtifactHistory;

export async function learnFromCase(caseId) {
  const caseData = await loadCase(caseId);

  if (!caseData.findings || caseData.findings.length === 0) {
    return { learned: 0, artifacts: [] };
  }

  const isIncident = caseData.riskScore > 70;
  let learned = 0;
  const artifacts = [];

  for (const finding of caseData.findings) {
    const classification = finding.classification || 'unknown';

    const knowledge = await learnArtifact(finding.title, classification, isIncident, caseId);
    artifacts.push({
      name: finding.title,
      classification,
      confidence: knowledge.confidence,
      seenCount: knowledge.seenCount
    });
    learned++;
  }

  caseData.events.push({
    type: 'CASE_LEARNED',
    payload: {
      artifactsLearned: learned
    },
    timestamp: new Date().toISOString()
  });

  await saveCase(caseId, caseData);

  return { learned, artifacts };
}

export const mcp_knowledgeLayer = {
  name: 'knowledgeLayer',
  description: 'Apply historical knowledge to improve case analysis',
  methods: {
    lookupArtifact,
    learnArtifact,
    updateConfidence,
    getHistory,
    learnFromCase,
    applyKnowledgeLayer,
    getKnowledgeInsights,
    buildCorrelationFromKnowledge
  }
};
