"""Threat Hunting Skill - Detection Engineering & MITRE Mapping"""

import json
from datetime import datetime
from pathlib import Path


class ThreatHuntingSkill:
    """Threat hunting and detection engineering capabilities"""

    def __init__(self):
        self.skill_name = "threat-hunting"
        self.version = "1.0.0"
        self.state_dir = Path(__file__).parent.parent.parent / "state"
        self.state_dir.mkdir(exist_ok=True)

    def get_metadata(self):
        return {
            'name': self.skill_name,
            'version': self.version,
            'description': 'Threat hunting, detection engineering, MITRE mapping',
            'capabilities': [
                'map_mitre',
                'generate_sigma_rule',
                'generate_yara_rule',
                'hunt_persistence',
                'hunt_credential_dumping',
                'hunt_indicators'
            ]
        }

    def map_mitre(self, tactic, technique_id):
        """Map techniques to MITRE Enterprise framework

        Args:
            tactic: MITRE tactic (e.g., 'persistence', 'execution')
            technique_id: Technique ID (e.g., 'T1547')

        Returns:
            dict with MITRE mapping details
        """
        mitre_db = {
            'persistence': {
                'T1547': {'name': 'Boot or Logon Autostart Execution', 'category': 'Startup Items'},
                'T1547.001': {'name': 'Registry Run Keys / Startup Folder', 'category': 'Registry'},
                'T1547.013': {'name': 'XDG Autostart Entries', 'category': 'Linux'},
                'T1547.014': {'name': 'Active Setup', 'category': 'COM'},
            },
            'execution': {
                'T1059': {'name': 'Command and Scripting Interpreter', 'category': 'CLI'},
                'T1059.001': {'name': 'PowerShell', 'category': 'Scripting'},
                'T1059.003': {'name': 'Windows Command Shell', 'category': 'CLI'},
                'T1059.004': {'name': 'Unix Shell', 'category': 'Unix'},
            },
            'defense-evasion': {
                'T1140': {'name': 'Deobfuscate/Decode Files or Information', 'category': 'Obfuscation'},
                'T1036': {'name': 'Masquerading', 'category': 'Hide'},
                'T1027': {'name': 'Obfuscated Files or Information', 'category': 'Evasion'},
            },
            'credential-access': {
                'T1110': {'name': 'Brute Force', 'category': 'Authentication'},
                'T1187': {'name': 'Forced Authentication', 'category': 'Network'},
                'T1040': {'name': 'Network Sniffing', 'category': 'Network'},
            },
            'lateral-movement': {
                'T1570': {'name': 'Lateral Tool Transfer', 'category': 'Network'},
                'T1570': {'name': 'Exploitation of Remote Services', 'category': 'Network'},
                'T1021': {'name': 'Remote Services', 'category': 'Remote'},
            }
        }

        tactic_lower = tactic.lower().replace(' ', '-')
        if tactic_lower in mitre_db and technique_id in mitre_db[tactic_lower]:
            mapping = mitre_db[tactic_lower][technique_id]
            return {
                'success': True,
                'tactic': tactic,
                'technique_id': technique_id,
                'technique_name': mapping['name'],
                'category': mapping['category'],
                'mapped_at': datetime.now().isoformat()
            }

        return {
            'success': False,
            'error': f'Technique {technique_id} not found in {tactic}',
            'mapped_at': datetime.now().isoformat()
        }

    def generate_sigma_rule(self, rule_name, selection_criteria, filter_condition=None):
        """Generate Sigma detection rule (YAML format)

        Args:
            rule_name: Name of the detection rule
            selection_criteria: dict with detection logic
            filter_condition: Optional filter condition

        Returns:
            dict with YAML-formatted Sigma rule
        """
        rule_id = f"sigma_{rule_name.lower().replace(' ', '_')}"

        sigma_rule = {
            'title': rule_name,
            'id': rule_id,
            'status': 'experimental',
            'description': f'Detection rule for {rule_name}',
            'author': 'SentinelOps Threat Hunting',
            'date': datetime.now().strftime('%Y/%m/%d'),
            'modified': datetime.now().strftime('%Y/%m/%d'),
            'logsource': {
                'product': 'windows',
                'service': 'security'
            },
            'detection': {
                'selection': selection_criteria,
            },
            'falsepositives': [
                'Legitimate administrative activity'
            ],
            'level': 'medium',
            'tags': [
                'detection',
                'sigma',
                'sentinelops'
            ]
        }

        if filter_condition:
            sigma_rule['detection']['filter'] = filter_condition

        sigma_rule['detection']['condition'] = 'selection'

        # Save to file
        rule_file = self.state_dir / f"{rule_id}.sigma.json"
        with open(rule_file, 'w') as f:
            json.dump(sigma_rule, f, indent=2)

        return {
            'success': True,
            'rule_id': rule_id,
            'rule_name': rule_name,
            'saved_to': str(rule_file),
            'generated_at': datetime.now().isoformat()
        }

    def generate_yara_rule(self, rule_name, file_patterns, malware_family='unknown'):
        """Generate YARA detection rule for malware

        Args:
            rule_name: Name of the YARA rule
            file_patterns: List of file patterns to match
            malware_family: Malware family classification

        Returns:
            dict with YARA rule
        """
        rule_id = f"yara_{rule_name.lower().replace(' ', '_')}"

        strings_section = []
        for i, pattern in enumerate(file_patterns, 1):
            strings_section.append(f'    $pattern{i} = "{pattern}" ascii')

        yara_rule = f"""rule {rule_id} {{
    meta:
        author = "SentinelOps Threat Hunting"
        date = "{datetime.now().strftime('%Y-%m-%d')}"
        description = "Detection for {rule_name}"
        malware_family = "{malware_family}"
        severity = "high"
    strings:
{chr(10).join(strings_section)}
    condition:
        any of them
}}"""

        # Save to file
        rule_file = self.state_dir / f"{rule_id}.yar"
        with open(rule_file, 'w') as f:
            f.write(yara_rule)

        return {
            'success': True,
            'rule_id': rule_id,
            'rule_name': rule_name,
            'malware_family': malware_family,
            'pattern_count': len(file_patterns),
            'saved_to': str(rule_file),
            'generated_at': datetime.now().isoformat()
        }

    def hunt_persistence(self):
        """Hunt for persistence mechanisms using MCP tools"""
        return {
            'hunt_type': 'persistence',
            'tools_used': ['huntPersistence', 'registryRunKeys', 'scheduledTasks'],
            'description': 'Scan for persistence via registry, startup, scheduled tasks',
            'status': 'wired_to_mcp',
            'last_hunt': datetime.now().isoformat()
        }

    def hunt_credential_dumping(self):
        """Hunt for credential dumping indicators"""
        return {
            'hunt_type': 'credential_dumping',
            'tools_used': ['huntCredentialDumping', 'powershellLogs', 'eventLogs'],
            'description': 'Detect credential dumping attacks (Mimikatz, SAM registry)',
            'status': 'wired_to_mcp',
            'last_hunt': datetime.now().isoformat()
        }

    def hunt_indicators(self, ioc_list):
        """Hunt for Indicators of Compromise

        Args:
            ioc_list: List of IOCs (IPs, domains, file hashes)

        Returns:
            dict with hunt results
        """
        return {
            'hunt_type': 'ioc_matching',
            'tools_used': ['huntIndicators'],
            'ioc_count': len(ioc_list),
            'description': f'Match {len(ioc_list)} IOCs across network',
            'status': 'wired_to_mcp',
            'last_hunt': datetime.now().isoformat()
        }

    def execute(self, action, **kwargs):
        """Execute skill action"""
        actions = {
            'map_mitre': lambda: self.map_mitre(kwargs.get('tactic'), kwargs.get('technique_id')),
            'generate_sigma_rule': lambda: self.generate_sigma_rule(
                kwargs.get('rule_name'),
                kwargs.get('selection_criteria'),
                kwargs.get('filter_condition')
            ),
            'generate_yara_rule': lambda: self.generate_yara_rule(
                kwargs.get('rule_name'),
                kwargs.get('file_patterns'),
                kwargs.get('malware_family', 'unknown')
            ),
            'hunt_persistence': lambda: self.hunt_persistence(),
            'hunt_credential_dumping': lambda: self.hunt_credential_dumping(),
            'hunt_indicators': lambda: self.hunt_indicators(kwargs.get('ioc_list', []))
        }

        if action not in actions:
            return {'error': f'Unknown action: {action}'}

        try:
            result = actions[action]()
            return {'success': True, 'data': result}
        except Exception as e:
            return {'error': str(e)}
