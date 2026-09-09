"""
GIT GOVERNANCE SKILL
Repository authority and branch management

Capabilities:
- Enforce branch policies
- Manage source of truth
- Audit access control
- Archive deprecated branches
"""

__version__ = "1.0.0"

from .git_governance import GitGovernanceSkill

__all__ = ['GitGovernanceSkill']
