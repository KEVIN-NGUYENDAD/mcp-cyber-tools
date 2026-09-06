#!/usr/bin/env python3
"""
SOC INTELLIGENCE COLLECTOR (Phase N)
Integrated runner for all intelligence extractors
Coordinates: Asset, Service, and Cryptographic intelligence extraction
Outputs: Complete intelligence layer for SentinelOps MVP

Execution flow:
1. Extract asset intelligence (devices, classifications, vuln summaries)
2. Extract service intelligence (ports, protocols, services)
3. Extract cryptographic intelligence (certificates, ciphers, TLS versions)
4. Generate comprehensive SOC intelligence report
5. Update event hub with intelligence changes
6. Prepare dashboard data
"""

import json
import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path

def run_intelligence_extractor(script_name, script_path):
    """Run an intelligence extractor script and return results"""
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        try:
            data = json.loads(result.stdout)
            return data
        except json.JSONDecodeError:
            return {'error': f'Failed to parse {script_name} output', 'raw': result.stdout}
    except subprocess.TimeoutExpired:
        return {'error': f'{script_name} timed out'}
    except Exception as e:
        return {'error': f'{script_name} failed: {str(e)}'}


def collect_all_intelligence():
    """Orchestrate all intelligence extraction"""
    scripts_dir = Path(__file__).parent
    state_dir = Path(__file__).parent.parent / 'state'
    state_dir.mkdir(exist_ok=True)

    report = {
        'timestamp': datetime.now().isoformat(),
        'phase': 'N - SOC Intelligence',
        'extractors': {},
        'summary': {
            'total_assets': 0,
            'total_services': 0,
            'total_certificates': 0,
            'total_cipher_suites': 0,
            'crypto_health_score': 0,
            'new_assets': 0,
            'new_services': 0,
            'closed_services': 0,
            'newly_expired_certs': 0
        },
        'status': 'collecting'
    }

    # 1. Asset Intelligence
    print('[1/3] Extracting asset intelligence...', file=sys.stderr)
    asset_result = run_intelligence_extractor(
        'Asset Intelligence Extractor',
        scripts_dir / 'extract_asset_intelligence.py'
    )
    report['extractors']['assets'] = asset_result
    if 'error' not in asset_result:
        report['summary']['total_assets'] = asset_result.get('total_assets', 0)
        report['summary']['new_assets'] = asset_result.get('new_assets', 0)

    # 2. Service Intelligence
    print('[2/3] Extracting service intelligence...', file=sys.stderr)
    service_result = run_intelligence_extractor(
        'Service Intelligence Extractor',
        scripts_dir / 'extract_service_intelligence.py'
    )
    report['extractors']['services'] = service_result
    if 'error' not in service_result:
        report['summary']['total_services'] = service_result.get('total_services', 0)
        report['summary']['new_services'] = service_result.get('new_services', 0)
        report['summary']['closed_services'] = service_result.get('closed_services', 0)

    # 3. Cryptographic Intelligence
    print('[3/3] Extracting cryptographic intelligence...', file=sys.stderr)
    crypto_result = run_intelligence_extractor(
        'Cryptographic Intelligence Extractor',
        scripts_dir / 'extract_crypto_intelligence.py'
    )
    report['extractors']['cryptography'] = crypto_result
    if 'error' not in crypto_result:
        report['summary']['total_certificates'] = crypto_result.get('certificate_count', 0)
        report['summary']['total_cipher_suites'] = crypto_result.get('cipher_suite_count', 0)
        report['summary']['crypto_health_score'] = crypto_result.get('health_score', 0)
        report['summary']['newly_expired_certs'] = crypto_result.get('newly_expired_certs', 0)

    # Determine overall status
    errors = [
        e for e in report['extractors'].values()
        if isinstance(e, dict) and 'error' in e
    ]

    if not errors:
        report['status'] = 'success'
    elif len(errors) < 3:
        report['status'] = 'partial'
    else:
        report['status'] = 'failed'

    report['errors_count'] = len(errors)

    return report


def save_intelligence_report(report):
    """Save comprehensive intelligence report"""
    state_dir = Path(__file__).parent.parent / 'state'
    report_file = state_dir / 'soc_intelligence.json'

    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        return True
    except Exception:
        return False


def main():
    print('SentinelOps SOC Intelligence Collector - Phase N', file=sys.stderr)
    print('=' * 60, file=sys.stderr)

    report = collect_all_intelligence()

    # Print to stdout
    print(json.dumps(report, indent=2))

    # Save report
    save_intelligence_report(report)

    # Exit with status
    sys.exit(0 if report['status'] in ['success', 'partial'] else 1)


if __name__ == '__main__':
    main()
