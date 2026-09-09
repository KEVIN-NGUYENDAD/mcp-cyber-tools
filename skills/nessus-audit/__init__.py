"""
NESSUS AUDIT SKILL
Automated vulnerability scanning and reporting

Capabilities:
- Launch network discovery scans
- Target specific assets
- Generate risk reports
- Export scan results
"""

__version__ = "1.0.0"
__author__ = "SentinelOps"

from .nessus_audit import NessusAuditSkill

__all__ = ['NessusAuditSkill']
