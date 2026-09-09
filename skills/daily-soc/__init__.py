"""
DAILY SOC SKILL
Daily security operations orchestration

Capabilities:
- Generate daily brief
- Compile threat summary
- Prioritize incidents
- Send alerts
"""

__version__ = "1.0.0"

from .daily_soc import DailySocSkill

__all__ = ['DailySocSkill']
