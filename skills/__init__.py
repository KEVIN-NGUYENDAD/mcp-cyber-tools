"""
SENTINELOPS SKILLS LIBRARY
Unified skill framework for security operations

Installed Skills:
1. nessus-audit - Vulnerability scanning and reporting
2. waap-audit - WAF threat detection and analysis
3. asset-intelligence - Asset profiling and trust scoring
4. daily-soc - Daily security operations orchestration
5. git-governance - Repository authority management
"""

__version__ = "1.0.0"

try:
    from .nessus_audit import NessusAuditSkill
    from .waap_audit import WaapAuditSkill
    from .asset_intelligence import AssetIntelligenceSkill
    from .daily_soc import DailySocSkill
    from .git_governance import GitGovernanceSkill
except ImportError:
    NessusAuditSkill = None
    WaapAuditSkill = None
    AssetIntelligenceSkill = None
    DailySocSkill = None
    GitGovernanceSkill = None


class SkillRegistry:
    """Central skill registry and loader"""

    def __init__(self):
        self.skills = {}
        self._load_skills()

    def _load_skills(self):
        """Load all available skills"""
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


__all__ = ['SkillRegistry', 'NessusAuditSkill', 'WaapAuditSkill', 'AssetIntelligenceSkill', 'DailySocSkill', 'GitGovernanceSkill']
