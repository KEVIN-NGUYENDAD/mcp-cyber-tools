"""
SENTINELOPS SKILLS LIBRARY
Unified skill framework for security operations

Installed Skills (Phase 1-3):
1. nessus-audit - Vulnerability scanning and reporting
2. waap-audit - WAF threat detection and analysis
3. asset-intelligence - Asset profiling and trust scoring
4. daily-soc - Daily security operations orchestration
5. git-governance - Repository authority management

Installed Skills (Sprint A - SOC Operational):
6. threat-hunting - Detection engineering & MITRE mapping
7. incident-triage - Emergency response & 3-step containment
8. dfir-investigation - Digital forensics & evidence management
"""

__version__ = "2.0.0"

import sys
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

# Import Phase 1-3 skills (handle hyphenated directory names)
try:
    # Threat Hunting Skill
    threat_hunting_path = Path(__file__).parent / 'threat-hunting' / 'threat_hunting.py'
    threat_hunting_spec = spec_from_file_location('threat_hunting', threat_hunting_path)
    threat_hunting_module = module_from_spec(threat_hunting_spec)
    threat_hunting_spec.loader.exec_module(threat_hunting_module)
    ThreatHuntingSkill = threat_hunting_module.ThreatHuntingSkill
except Exception as e:
    ThreatHuntingSkill = None
    print(f"Warning: Could not load ThreatHuntingSkill: {e}")

try:
    # Incident Triage Skill
    incident_triage_path = Path(__file__).parent / 'incident-triage' / 'incident_triage.py'
    incident_triage_spec = spec_from_file_location('incident_triage', incident_triage_path)
    incident_triage_module = module_from_spec(incident_triage_spec)
    incident_triage_spec.loader.exec_module(incident_triage_module)
    IncidentTriageSkill = incident_triage_module.IncidentTriageSkill
except Exception as e:
    IncidentTriageSkill = None
    print(f"Warning: Could not load IncidentTriageSkill: {e}")

try:
    # DFIR Investigation Skill
    dfir_path = Path(__file__).parent / 'dfir-investigation' / 'dfir_investigation.py'
    dfir_spec = spec_from_file_location('dfir_investigation', dfir_path)
    dfir_module = module_from_spec(dfir_spec)
    dfir_spec.loader.exec_module(dfir_module)
    DFIRInvestigationSkill = dfir_module.DFIRInvestigationSkill
except Exception as e:
    DFIRInvestigationSkill = None
    print(f"Warning: Could not load DFIRInvestigationSkill: {e}")

# Import existing skills (fallback if relative imports work)
try:
    from .nessus_audit import NessusAuditSkill
except ImportError:
    NessusAuditSkill = None

try:
    from .waap_audit import WaapAuditSkill
except ImportError:
    WaapAuditSkill = None

try:
    from .asset_intelligence import AssetIntelligenceSkill
except ImportError:
    AssetIntelligenceSkill = None

try:
    from .daily_soc import DailySocSkill
except ImportError:
    DailySocSkill = None

try:
    from .git_governance import GitGovernanceSkill
except ImportError:
    GitGovernanceSkill = None


class SkillRegistry:
    """Central skill registry and loader"""

    def __init__(self):
        self.skills = {}
        self._load_skills()

    def _load_skills(self):
        """Load all available skills"""
        # Phase 1-3 Skills
        if NessusAuditSkill:
            self.register(NessusAuditSkill())
        if WaapAuditSkill:
            self.register(WaapAuditSkill())
        if AssetIntelligenceSkill:
            self.register(AssetIntelligenceSkill())
        if DailySocSkill:
            self.register(DailySocSkill())
        if GitGovernanceSkill:
            self.register(GitGovernanceSkill())

        # Sprint A - SOC Operational Skills
        if ThreatHuntingSkill:
            self.register(ThreatHuntingSkill())
        if IncidentTriageSkill:
            self.register(IncidentTriageSkill())
        if DFIRInvestigationSkill:
            self.register(DFIRInvestigationSkill())

    def register(self, skill):
        """Register a skill"""
        metadata = skill.get_metadata()
        self.skills[metadata['name']] = skill

    def get_skill(self, skill_name):
        """Get skill by name"""
        return self.skills.get(skill_name)

    def list_skills(self):
        """List all available skills"""
        return {name: skill.get_metadata() for name, skill in self.skills.items()}

    def execute(self, skill_name, action, **kwargs):
        """Execute skill action"""
        skill = self.get_skill(skill_name)
        if not skill:
            return {'error': f'Skill not found: {skill_name}'}
        return skill.execute(action, **kwargs)


__all__ = [
    'SkillRegistry',
    # Phase 1-3 Skills
    'NessusAuditSkill',
    'WaapAuditSkill',
    'AssetIntelligenceSkill',
    'DailySocSkill',
    'GitGovernanceSkill',
    # Sprint A - SOC Operational Skills
    'ThreatHuntingSkill',
    'IncidentTriageSkill',
    'DFIRInvestigationSkill'
]
