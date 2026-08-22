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

function enrichFindingWithKnowledge(finding, knowledge) {
  if (!knowledge) {
    return finding;
  }

  return {
    ...finding,
    knowledgeContext: {
      seenBefore: true,
      seenCount: knowledge.seenCount,
      incidentCount: knowledge.incidentCount,
      confidence: knowledge.confidence,
      classification: knowledge.classification,
      casesObserved: knowledge.casesObserved.length
    },
    enhancedConfidence: Math.max(finding.confidence || 0, knowledge.confidence || 0),
    enhancedClassification: knowledge.classification || finding.classification
  };
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

  return {
    artifact: knowledge.artifact,
    firstSeen: knowledge.firstSeen,
    lastSeen: knowledge.lastSeen,
    seenCount: knowledge.seenCount,
    incidentCount: knowledge.incidentCount,
    confidence: knowledge.confidence,
    classification: knowledge.classification,
    observedInCases: knowledge.casesObserved,
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

export const mcp_knowledgeLayer = {
  name: 'knowledgeLayer',
  description: 'Apply historical knowledge to improve case analysis',
  methods: {
    applyKnowledgeLayer,
    getArtifactHistory,
    getKnowledgeInsights,
    buildCorrelationFromKnowledge
  }
};
