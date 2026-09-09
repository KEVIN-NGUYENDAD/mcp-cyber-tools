"""
WAAP AUDIT SKILL
Web Application Firewall auditing and threat detection

Capabilities:
- Analyze WAF logs
- Detect attack patterns
- Generate WAF reports
- Recommend rules
"""

__version__ = "1.0.0"

from .waap_audit import WaapAuditSkill

__all__ = ['WaapAuditSkill']
