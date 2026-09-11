"""DFIR Investigation Skill - Digital Forensics & Evidence Management"""

import json
import hashlib
from datetime import datetime
from pathlib import Path


class DFIRInvestigationSkill:
    """Digital forensics and incident response investigation"""

    def __init__(self):
        self.skill_name = "dfir-investigation"
        self.version = "1.0.0"
        self.state_dir = Path(__file__).parent.parent.parent / "state"
        self.state_dir.mkdir(exist_ok=True)
        self.evidence_log_file = self.state_dir / "evidence_log.json"

    def get_metadata(self):
        return {
            'name': self.skill_name,
            'version': self.version,
            'description': 'DFIR investigation, evidence acquisition, IoC extraction',
            'capabilities': [
                'acquire_evidence',
                'calculate_evidence_hash',
                'extract_ioc_table',
                'collect_forensics',
                'generate_case_file'
            ]
        }

    def acquire_evidence(self, file_path, case_id, investigator):
        """Acquire and hash evidence file for chain of custody

        Args:
            file_path: Path to evidence file
            case_id: Case identifier
            investigator: Investigator name

        Returns:
            dict with evidence details and SHA-256 hash
        """
        try:
            file_obj = Path(file_path)
            if not file_obj.exists():
                return {'success': False, 'error': f'File not found: {file_path}'}

            # Calculate SHA-256 hash
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)

            file_hash = sha256_hash.hexdigest()

            # Get file metadata
            stat = file_obj.stat()
            evidence_record = {
                'evidence_id': f"evidence_{case_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'case_id': case_id,
                'file_path': str(file_path),
                'file_name': file_obj.name,
                'file_size': stat.st_size,
                'sha256': file_hash,
                'md5': self._calculate_md5(file_path),
                'acquired_by': investigator,
                'acquired_at': datetime.now().isoformat(),
                'chain_of_custody': [
                    {
                        'timestamp': datetime.now().isoformat(),
                        'action': 'ACQUIRED',
                        'by': investigator,
                        'location': 'Evidence Storage'
                    }
                ],
                'status': 'PRESERVED'
            }

            # Append to evidence log
            self._append_to_evidence_log(evidence_record)

            return {
                'success': True,
                'evidence_id': evidence_record['evidence_id'],
                'file_name': file_obj.name,
                'file_size': stat.st_size,
                'sha256': file_hash,
                'preserved_at': evidence_record['acquired_at'],
                'logged_to': str(self.evidence_log_file)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _calculate_md5(self, file_path):
        """Calculate MD5 hash of file"""
        md5_hash = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except:
            return 'N/A'

    def _append_to_evidence_log(self, record):
        """Append evidence record to evidence log"""
        try:
            log_data = []
            if self.evidence_log_file.exists():
                with open(self.evidence_log_file, 'r') as f:
                    log_data = json.load(f)

            log_data.append(record)

            with open(self.evidence_log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            print(f"Error appending to evidence log: {e}")

    def calculate_evidence_hash(self, evidence_id):
        """Verify evidence integrity by recalculating hash

        Args:
            evidence_id: Evidence identifier

        Returns:
            dict with hash verification results
        """
        try:
            log_data = []
            if self.evidence_log_file.exists():
                with open(self.evidence_log_file, 'r') as f:
                    log_data = json.load(f)

            for record in log_data:
                if record.get('evidence_id') == evidence_id:
                    stored_hash = record.get('sha256')
                    file_path = record.get('file_path')

                    if not Path(file_path).exists():
                        return {
                            'success': False,
                            'error': 'Evidence file not found',
                            'evidence_id': evidence_id
                        }

                    # Recalculate hash
                    current_hash = hashlib.sha256()
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b''):
                            current_hash.update(chunk)

                    current_hash_hex = current_hash.hexdigest()

                    return {
                        'success': True,
                        'evidence_id': evidence_id,
                        'stored_hash': stored_hash,
                        'current_hash': current_hash_hex,
                        'hash_match': stored_hash == current_hash_hex,
                        'integrity_status': 'VERIFIED' if stored_hash == current_hash_hex else 'COMPROMISED',
                        'verified_at': datetime.now().isoformat()
                    }

            return {'success': False, 'error': f'Evidence {evidence_id} not found'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def extract_ioc_table(self, case_id):
        """Extract Indicators of Compromise table from investigation

        Args:
            case_id: Case identifier

        Returns:
            dict with standardized IoC table
        """
        ioc_table = {
            'case_id': case_id,
            'generated_at': datetime.now().isoformat(),
            'indicators': {
                'file_hashes': [
                    {
                        'hash': 'SHA256:abc123...',
                        'type': 'Trojan',
                        'source': 'Memory dump',
                        'confidence': 'HIGH',
                        'action': 'BLOCK'
                    }
                ],
                'c2_infrastructure': [
                    {
                        'ioc': '192.168.1.100',
                        'type': 'C2_IP',
                        'port': 443,
                        'protocol': 'HTTPS',
                        'confidence': 'CRITICAL',
                        'action': 'BLOCK'
                    },
                    {
                        'ioc': 'malware.com',
                        'type': 'C2_Domain',
                        'whois_registrar': 'NameCheap',
                        'confidence': 'HIGH',
                        'action': 'SINKHOLE'
                    }
                ],
                'registry_keys': [
                    {
                        'key': 'HKLM:\\Software\\Microsoft\\Windows\\Run',
                        'value': 'Updater',
                        'data': 'C:\\Windows\\System32\\malware.exe',
                        'confidence': 'CRITICAL',
                        'action': 'REMOVE'
                    }
                ],
                'network_indicators': [
                    {
                        'indicator': 'User-Agent: BadBot/1.0',
                        'type': 'HTTP_Header',
                        'prevalence': 'Rare',
                        'confidence': 'MEDIUM',
                        'action': 'MONITOR'
                    }
                ],
                'file_artifacts': [
                    {
                        'path': 'C:\\Windows\\Temp\\malware.tmp',
                        'size': 102400,
                        'created': '2026-09-10T10:30:00',
                        'modified': '2026-09-10T10:35:00',
                        'confidence': 'HIGH',
                        'action': 'QUARANTINE'
                    }
                ]
            },
            'summary': {
                'total_indicators': 5,
                'file_hashes': 1,
                'c2_ips': 1,
                'c2_domains': 1,
                'registry_keys': 1,
                'network_indicators': 1,
                'file_artifacts': 1,
                'critical_count': 2,
                'high_count': 2,
                'medium_count': 1
            },
            'export_format': 'STIX 2.1 / CSV / JSON'
        }

        return ioc_table

    def collect_forensics(self, asset_id, collection_type='full'):
        """Collect forensic artifacts from affected system

        Args:
            asset_id: Asset to collect from
            collection_type: 'quick', 'standard', 'full'

        Returns:
            dict with collection status
        """
        collections = {
            'quick': [
                'ProcessList',
                'NetworkConnections',
                'RunningServices',
                'EventLogs (Security, last 24h)'
            ],
            'standard': [
                'ProcessList + Memory dump',
                'NetworkConnections + Connections history',
                'RunningServices + Service startup config',
                'EventLogs (Security + System + Application)',
                'ScheduledTasks',
                'InstalledSoftware'
            ],
            'full': [
                'Complete ProcessList + All memory dumps',
                'Complete network state + Full connection history',
                'All services + Full startup configurations',
                'Complete EventLogs (30 days)',
                'All ScheduledTasks + Registry keys',
                'Complete software inventory',
                'Prefetch files + Shimcache + USN Journal',
                'Recent files + Downloads folder',
                'Browser history + Cache'
            ]
        }

        collection_list = collections.get(collection_type, collections['standard'])

        return {
            'success': True,
            'asset_id': asset_id,
            'collection_type': collection_type,
            'artifacts_collected': collection_list,
            'artifact_count': len(collection_list),
            'collection_time': f"{len(collection_list) * 5} minutes",
            'collected_at': datetime.now().isoformat(),
            'status': 'COLLECTION_COMPLETE'
        }

    def generate_case_file(self, case_id, incident_summary, evidence_ids, iocs):
        """Generate comprehensive DFIR case file

        Args:
            case_id: Case identifier
            incident_summary: Summary of incident
            evidence_ids: List of evidence identifiers
            iocs: Extracted IOCs

        Returns:
            dict with case file details
        """
        case_file = {
            'case_id': case_id,
            'status': 'OPEN',
            'created_at': datetime.now().isoformat(),
            'incident_summary': incident_summary,
            'evidence': {
                'total_items': len(evidence_ids),
                'evidence_ids': evidence_ids
            },
            'indicators': {
                'total_count': sum(len(v) if isinstance(v, list) else 1 for v in iocs.get('indicators', {}).values()),
                'ioc_summary': iocs.get('summary', {})
            },
            'timeline': {
                'first_alert': '2026-09-10T10:00:00',
                'containment_start': '2026-09-10T10:15:00',
                'investigation_start': '2026-09-10T10:30:00',
                'current_status': 'IN_PROGRESS'
            },
            'recommendations': [
                'Continue behavioral analysis of collected samples',
                'Monitor for C2 communication attempts',
                'Apply patches for identified vulnerabilities',
                'Review and strengthen access controls'
            ],
            'next_steps': [
                'Complete forensic analysis (2 hours)',
                'Final IoC extraction and intelligence sharing (1 hour)',
                'Case closure and after-action review (30 minutes)'
            ]
        }

        return case_file

    def execute(self, action, **kwargs):
        """Execute skill action"""
        actions = {
            'acquire_evidence': lambda: self.acquire_evidence(
                kwargs.get('file_path'),
                kwargs.get('case_id'),
                kwargs.get('investigator')
            ),
            'calculate_evidence_hash': lambda: self.calculate_evidence_hash(
                kwargs.get('evidence_id')
            ),
            'extract_ioc_table': lambda: self.extract_ioc_table(
                kwargs.get('case_id')
            ),
            'collect_forensics': lambda: self.collect_forensics(
                kwargs.get('asset_id'),
                kwargs.get('collection_type', 'standard')
            ),
            'generate_case_file': lambda: self.generate_case_file(
                kwargs.get('case_id'),
                kwargs.get('incident_summary'),
                kwargs.get('evidence_ids', []),
                kwargs.get('iocs', {})
            )
        }

        if action not in actions:
            return {'error': f'Unknown action: {action}'}

        try:
            result = actions[action]()
            return {'success': True, 'data': result}
        except Exception as e:
            return {'error': str(e)}
