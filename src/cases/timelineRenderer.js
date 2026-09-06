import { loadCase } from './caseManager.js';

const eventIcons = {
  'CASE_CREATED': '📝',
  'FINDING_ADDED': '🔍',
  'RECOMMENDATION_GENERATED': '💡',
  'RECOMMENDATION_APPROVED': '✅',
  'ACTION_EXECUTED': '⚡',
  'STATUS_CHANGED': '🔄',
  'APPROVAL_RECORDED': '👤'
};

const eventLabels = {
  'CASE_CREATED': 'Case Created',
  'FINDING_ADDED': 'Finding Extracted',
  'RECOMMENDATION_GENERATED': 'Recommendations Generated',
  'RECOMMENDATION_APPROVED': 'Action Approved',
  'ACTION_EXECUTED': 'Action Executed',
  'STATUS_CHANGED': 'Status Changed',
  'APPROVAL_RECORDED': 'Approval Recorded'
};

function formatTime(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour12: true,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

function formatDate(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric'
  });
}

function describeEvent(event) {
  if (event.type === 'FINDING_ADDED') {
    return `${event.payload.title} (${event.payload.severity})`;
  } else if (event.type === 'RECOMMENDATION_APPROVED') {
    return `Approved: ${event.payload.title}`;
  } else if (event.type === 'ACTION_EXECUTED') {
    return `Executed: ${event.payload.title} - ${event.payload.result}`;
  } else if (event.type === 'STATUS_CHANGED') {
    return `${event.payload.from} → ${event.payload.to}`;
  } else if (event.type === 'RECOMMENDATION_GENERATED') {
    return `${event.payload.count} recommendations generated`;
  }
  return '';
}

export async function renderTimeline(caseId) {
  const caseData = await loadCase(caseId);

  let timeline = `\n# Investigation Timeline: ${caseId}\n\n`;
  timeline += `**Started**: ${formatDate(caseData.createdAt)} at ${formatTime(caseData.createdAt)}\n`;
  timeline += `**Status**: ${caseData.status}\n`;
  timeline += `**Risk**: ${caseData.risk.toUpperCase()}\n\n`;

  timeline += '## Event Sequence\n\n';

  caseData.events.forEach((event, idx) => {
    const icon = eventIcons[event.type] || '•';
    const label = eventLabels[event.type] || event.type;
    const time = formatTime(event.timestamp);
    const description = describeEvent(event);

    timeline += `${icon} **${time}** | ${label}\n`;
    if (description) {
      timeline += `   └─ ${description}\n`;
    }
    timeline += '\n';
  });

  timeline += '## Summary\n\n';
  timeline += `- **Total Events**: ${caseData.events.length}\n`;
  timeline += `- **Findings**: ${caseData.findings.length}\n`;
  timeline += `- **Recommendations**: ${caseData.recommendations.length}\n`;
  timeline += `- **Duration**: ${Math.round((new Date(caseData.updatedAt) - new Date(caseData.createdAt)) / 1000)}s\n`;

  return timeline;
}

export async function getTimelineMetrics(caseId) {
  const caseData = await loadCase(caseId);

  const createdAt = new Date(caseData.createdAt);
  const updatedAt = new Date(caseData.updatedAt);
  const duration = (updatedAt - createdAt) / 1000;

  const eventCounts = {};
  caseData.events.forEach(e => {
    eventCounts[e.type] = (eventCounts[e.type] || 0) + 1;
  });

  return {
    caseId,
    startTime: caseData.createdAt,
    endTime: caseData.updatedAt,
    durationSeconds: duration,
    totalEvents: caseData.events.length,
    eventBreakdown: eventCounts,
    findingCount: caseData.findings.length,
    recommendationCount: caseData.recommendations.length,
    approvedCount: caseData.recommendations.filter(r => r.approved).length,
    executedCount: caseData.recommendations.filter(r => r.executed).length
  };
}

export const mcp_timelineRenderer = {
  name: 'timelineRenderer',
  description: 'Render case timeline and metrics',
  methods: {
    renderTimeline,
    getTimelineMetrics
  }
};
