import fs from 'fs/promises';
import path from 'path';
import { loadCase } from '../cases/caseManager.js';

const KNOWLEDGE_DIR = 'knowledge';

async function ensureKnowledgeDir() {
  await fs.mkdir(KNOWLEDGE_DIR, { recursive: true });
}

function extractArtifacts(findings) {
  const artifacts = [];
  findings.forEach(finding => {
    const title = finding.title.trim();
    if (title && !artifacts.includes(title)) {
      artifacts.push({
        name: title,
        severity: finding.severity,
        source: finding.source,
        classification: finding.classification
      });
    }
  });
  return artifacts;
}

export async function recordArtifact(artifactName, caseId, isIncident = false) {
  await ensureKnowledgeDir();

  const safeFileName = artifactName.toLowerCase().replace(/[^a-z0-9]/g, '-') + '.json';
  const filePath = path.join(KNOWLEDGE_DIR, safeFileName);

  let record = {
    artifact: artifactName,
    firstSeen: new Date().toISOString(),
    lastSeen: new Date().toISOString(),
    seenCount: 1,
    incidentCount: isIncident ? 1 : 0,
    casesObserved: [caseId],
    classifications: {}
  };

  try {
    const existing = JSON.parse(await fs.readFile(filePath, 'utf-8'));
    record = {
      ...existing,
      lastSeen: new Date().toISOString(),
      seenCount: existing.seenCount + 1,
      incidentCount: existing.incidentCount + (isIncident ? 1 : 0),
      casesObserved: [...new Set([...existing.casesObserved, caseId])]
    };
  } catch (e) {
    // New artifact
  }

  // Calculate confidence
  record.confidence = Math.round(
    ((record.seenCount - record.incidentCount) / record.seenCount) * 100
  );

  await fs.writeFile(filePath, JSON.stringify(record, null, 2));
  return record;
}

export async function lookupArtifact(artifactName) {
  await ensureKnowledgeDir();

  const safeFileName = artifactName.toLowerCase().replace(/[^a-z0-9]/g, '-') + '.json';
  const filePath = path.join(KNOWLEDGE_DIR, safeFileName);

  try {
    const record = JSON.parse(await fs.readFile(filePath, 'utf-8'));
    return record;
  } catch (e) {
    return null;
  }
}

export async function learnFromCase(caseId) {
  const caseData = await loadCase(caseId);
  const isIncident = caseData.riskScore > 70;

  const learned = {
    caseId,
    timestamp: new Date().toISOString(),
    artifacts: [],
    newKnowledge: 0,
    confidenceImproved: 0
  };

  const artifacts = extractArtifacts(caseData.findings);

  for (const artifact of artifacts) {
    const existing = await lookupArtifact(artifact.name);
    const recorded = await recordArtifact(artifact.name, caseId, isIncident);

    if (!existing) {
      learned.newKnowledge++;
    } else if (recorded.confidence !== existing.confidence) {
      learned.confidenceImproved++;
    }

    learned.artifacts.push({
      name: artifact.name,
      isNew: !existing,
      confidence: recorded.confidence,
      seenCount: recorded.seenCount
    });
  }

  return learned;
}

export async function getKnowledgeStats() {
  await ensureKnowledgeDir();

  const files = await fs.readdir(KNOWLEDGE_DIR);
  const records = [];

  for (const file of files) {
    if (file.endsWith('.json')) {
      const data = JSON.parse(await fs.readFile(path.join(KNOWLEDGE_DIR, file), 'utf-8'));
      records.push(data);
    }
  }

  return {
    totalArtifacts: records.length,
    totalObservations: records.reduce((sum, r) => sum + r.seenCount, 0),
    highConfidence: records.filter(r => r.confidence >= 95).length,
    suspicious: records.filter(r => r.confidence < 50).length,
    artifacts: records.sort((a, b) => b.seenCount - a.seenCount).slice(0, 10)
  };
}

export const mcp_investigationMemory = {
  name: 'investigationMemory',
  description: 'Remember and learn from past investigations',
  methods: {
    recordArtifact,
    lookupArtifact,
    learnFromCase,
    getKnowledgeStats
  }
};
