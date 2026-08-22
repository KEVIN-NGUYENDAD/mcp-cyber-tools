import { validateMachine } from './validateMachine.js';
import { investigatePersistence } from './investigatePersistence.js';
import { threatHuntPowerShell } from './threatHuntPowerShell.js';

export const playbookRegistry = {
  // QA/Validation Playbooks
  validateMachine: {
    id: 'validateMachine',
    name: 'Validate Machine',
    category: 'validation',
    description: 'Validate system operational readiness and deployment status',
    trigger: 'User: "Validate this machine"',
    severity: 'info',
    execute: validateMachine,
    expectedOutput: {
      caseType: 'Validation',
      findings: ['Operational readiness status'],
      recommendations: ['Create baseline', 'Export evidence']
    }
  },

  // DFIR Investigation Playbooks
  investigatePersistence: {
    id: 'investigatePersistence',
    name: 'Investigate Persistence',
    category: 'investigation',
    description: 'Investigate persistence mechanisms including registry, tasks, services',
    trigger: 'User: "Investigate persistence"',
    severity: 'high',
    execute: investigatePersistence,
    expectedOutput: {
      caseType: 'Investigation',
      findings: ['Registry startup entries', 'Scheduled tasks', 'Services'],
      recommendations: ['Export report', 'Create baseline', 'Close case']
    }
  },

  // Threat Hunt Playbooks
  threatHuntPowerShell: {
    id: 'threatHuntPowerShell',
    name: 'Hunt PowerShell Activity',
    category: 'threat-hunt',
    description: 'Hunt for suspicious encoded PowerShell commands and execution patterns',
    trigger: 'User: "Investigate PowerShell activity"',
    severity: 'medium',
    execute: threatHuntPowerShell,
    expectedOutput: {
      caseType: 'Hunt',
      findings: ['PowerShell commands', 'Execution sources', 'Encoded payloads'],
      recommendations: ['Export timeline', 'Create hunt baseline']
    }
  },

  // Assessment Playbooks (Template)
  endpointHealthCheck: {
    id: 'endpointHealthCheck',
    name: 'Endpoint Health Assessment',
    category: 'assessment',
    description: 'Comprehensive security posture assessment across Defender, Firewall, Services, Persistence',
    trigger: 'User: "Assess system security"',
    severity: 'high',
    execute: null, // Not yet implemented
    expectedOutput: {
      caseType: 'Assessment',
      findings: ['Defender status', 'Firewall rules', 'Service anomalies'],
      recommendations: ['Remediate findings', 'Export assessment']
    }
  }
};

export async function getPlaybookList() {
  return Object.entries(playbookRegistry).map(([id, pb]) => ({
    id: pb.id,
    name: pb.name,
    category: pb.category,
    description: pb.description,
    severity: pb.severity,
    implemented: pb.execute !== null
  }));
}

export async function executePlaybook(playbookId) {
  const playbook = playbookRegistry[playbookId];

  if (!playbook) {
    throw new Error(`Playbook ${playbookId} not found`);
  }

  if (!playbook.execute) {
    throw new Error(`Playbook ${playbookId} not yet implemented`);
  }

  console.log(`\n🎬 Executing: ${playbook.name}`);
  console.log(`   Category: ${playbook.category}`);
  console.log(`   Severity: ${playbook.severity}`);
  console.log();

  return await playbook.execute();
}

export const mcp_playbookRegistry = {
  name: 'playbookRegistry',
  description: 'Registry of all available investigation playbooks',
  methods: {
    getPlaybookList,
    executePlaybook
  }
};
