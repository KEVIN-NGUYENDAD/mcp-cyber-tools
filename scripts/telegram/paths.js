import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Project root is 2 levels up from /scripts/telegram/
const PROJECT_ROOT = path.resolve(__dirname, '../../');

// All paths are deterministic and DO NOT depend on process.cwd()
export const paths = {
  projectRoot: PROJECT_ROOT,
  stateDir: path.join(PROJECT_ROOT, 'state'),
  envFile: path.join(PROJECT_ROOT, '.env'),
  logsDir: path.join(PROJECT_ROOT, 'logs'),
  dailyBriefDir: path.join(PROJECT_ROOT, 'daily_brief'),

  // Common state files
  incidents: path.join(PROJECT_ROOT, 'state', 'incidents.json'),
  socIntelligence: path.join(PROJECT_ROOT, 'state', 'soc_intelligence.json'),
  assets: path.join(PROJECT_ROOT, 'state', 'assets.json'),
  riskScore: path.join(PROJECT_ROOT, 'state', 'risk_score.json'),
  waapStatus: path.join(PROJECT_ROOT, 'state', 'waap_status.json'),
  domainStatus: path.join(PROJECT_ROOT, 'state', 'domain_status.json'),
  notificationHistory: path.join(PROJECT_ROOT, 'state', 'notification_history.json'),
  processedIncidents: path.join(PROJECT_ROOT, 'state', 'processed_incidents.json'),
  approvalAudit: path.join(PROJECT_ROOT, 'state', 'approval_audit.json'),

  // Hunting & IOC files
  hunting_credential_dumping: path.join(PROJECT_ROOT, 'state', 'hunting_credential_dumping.json'),
  hunting_lateral_movement: path.join(PROJECT_ROOT, 'state', 'hunting_lateral_movement.json'),
  hunting_persistence: path.join(PROJECT_ROOT, 'state', 'hunting_persistence.json'),
  hunting_suspicious_processes: path.join(PROJECT_ROOT, 'state', 'hunting_suspicious_processes.json'),
  timeline: path.join(PROJECT_ROOT, 'state', 'timeline.json'),
};

console.log('[PATHS] Initialized with root:', paths.projectRoot);

export default paths;
