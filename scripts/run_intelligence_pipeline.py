#!/usr/bin/env python3
"""
SENTINELOPS INTELLIGENCE PIPELINE ORCHESTRATOR (Phase N.4)
Automatically updates all asset, service, and security intelligence
Runs all collectors and intelligence extractors in sequence
Outputs: Comprehensive state/ updates and daily brief
"""

import json
import sys
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict

try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass


class IntelligencePipeline:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.scripts_dir = self.project_root / 'scripts'
        self.state_dir = self.project_root / 'state'
        self.logs_dir = self.project_root / 'logs'
        self.daily_brief_dir = self.project_root / 'daily_brief'

        # Create directories if needed
        self.state_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.daily_brief_dir.mkdir(exist_ok=True)

        self.log_file = self.logs_dir / 'pipeline.log'
        self.pipeline_results = {
            'timestamp': datetime.now().isoformat(),
            'stages': [],
            'status': 'running',
            'summary': {}
        }
        self.start_time = time.time()

    def log(self, message):
        """Log message to both console and file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f'[{timestamp}] {message}'
        print(log_entry)
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')

    def run_stage(self, stage_name, script_path, description):
        """Run a single pipeline stage"""
        self.log(f'▶ Starting: {description}')
        stage_start = time.time()

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300
            )

            stage_duration = time.time() - stage_start

            if result.returncode == 0:
                self.log(f'✅ {stage_name} completed ({stage_duration:.1f}s)')

                # Try to parse output as JSON for results
                try:
                    output = json.loads(result.stdout)
                    self.pipeline_results['stages'].append({
                        'name': stage_name,
                        'status': 'success',
                        'duration': stage_duration,
                        'output': output
                    })
                    return True, output
                except:
                    self.pipeline_results['stages'].append({
                        'name': stage_name,
                        'status': 'success',
                        'duration': stage_duration
                    })
                    return True, None
            else:
                self.log(f'❌ {stage_name} failed')
                self.log(f'   Error: {result.stderr}')
                self.pipeline_results['stages'].append({
                    'name': stage_name,
                    'status': 'failed',
                    'duration': stage_duration,
                    'error': result.stderr
                })
                return False, None

        except subprocess.TimeoutExpired:
            self.log(f'⏱ {stage_name} timeout')
            self.pipeline_results['stages'].append({
                'name': stage_name,
                'status': 'timeout',
                'error': 'Execution timeout'
            })
            return False, None
        except Exception as e:
            self.log(f'⚠ {stage_name} exception: {str(e)}')
            self.pipeline_results['stages'].append({
                'name': stage_name,
                'status': 'error',
                'error': str(e)
            })
            return False, None

    def load_state_file(self, filename):
        """Load and parse a state JSON file"""
        filepath = self.state_dir / filename
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def generate_health_summary(self):
        """Generate and display health summary"""
        self.log('📊 HEALTH SUMMARY')
        self.log('=' * 50)

        # Load state files to gather metrics
        assets = self.load_state_file('assets.json')
        services = self.load_state_file('services.json')
        crypto = self.load_state_file('crypto_inventory.json')
        waap_score = self.load_state_file('waap_score.json')
        nessus = self.load_state_file('nessus_status.json')

        # Calculate counts
        asset_count = len(assets.get('assets', [])) if isinstance(assets, dict) else 0
        service_count = len(services.get('services', [])) if isinstance(services, dict) else 0

        crypto_score = 0
        if isinstance(crypto, dict) and 'findings' in crypto:
            # Crypto score based on absence of findings
            critical_count = sum(1 for f in crypto.get('findings', []) if f.get('severity') == 'CRITICAL')
            crypto_score = max(0, 100 - (critical_count * 10))
        elif isinstance(crypto, dict):
            crypto_score = crypto.get('score', 0)

        waap_score_val = waap_score.get('score', 0) if isinstance(waap_score, dict) else 0

        # Determine risk level
        avg_score = (crypto_score + waap_score_val) / 2 if crypto_score or waap_score_val else 50
        if avg_score >= 80:
            risk_level = 'LOW'
        elif avg_score >= 60:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'HIGH'

        # Display summary
        self.log(f'Assets:       {asset_count}')
        self.log(f'Services:     {service_count}')
        self.log(f'Crypto Score: {crypto_score}')
        self.log(f'WAAP Score:   {waap_score_val}')
        self.log(f'Risk Level:   {risk_level}')
        self.log('=' * 50)

        # Save summary
        self.pipeline_results['summary'] = {
            'assets': asset_count,
            'services': service_count,
            'crypto_score': crypto_score,
            'waap_score': waap_score_val,
            'risk_level': risk_level
        }

    def run(self):
        """Execute the complete pipeline"""
        self.log('🚀 Starting SentinelOps Intelligence Pipeline')
        self.log(f'   Project: {self.project_root.name}')
        self.log(f'   Started: {datetime.now().isoformat()}')
        self.log('')

        # Stage 1: Collectors
        self.log('📡 PHASE 1: DATA COLLECTION')
        self.log('-' * 50)

        success = True

        # 1. Nessus collection
        ok, _ = self.run_stage(
            'Nessus Collector',
            self.scripts_dir / 'collect_nessus_snapshot.py',
            'Collecting Nessus vulnerability scan data'
        )
        success = success and ok

        # 2. Domain collection
        ok, _ = self.run_stage(
            'Domain Collector',
            self.scripts_dir / 'collect_domain_snapshot.py',
            'Collecting domain security data'
        )
        success = success and ok

        # 3. WAAP collection
        ok, _ = self.run_stage(
            'WAAP Collector',
            self.scripts_dir / 'collect_waap_snapshot.py',
            'Collecting WAAP security posture'
        )
        success = success and ok

        self.log('')

        # Stage 1b: MCP Telemetry Collection (Phase N.6)
        self.log('🖥️ PHASE 1B: MCP TELEMETRY COLLECTION')
        self.log('-' * 50)

        # 4. System health
        ok, _ = self.run_stage(
            'System Health',
            self.scripts_dir / 'collect_system_health.py',
            'Collecting system health metrics'
        )
        success = success and ok

        # 5. Defender status
        ok, _ = self.run_stage(
            'Defender Status',
            self.scripts_dir / 'collect_defender_status.py',
            'Checking Defender protection'
        )
        success = success and ok

        # 6. Firewall status
        ok, _ = self.run_stage(
            'Firewall Status',
            self.scripts_dir / 'collect_firewall_status.py',
            'Checking Firewall status'
        )
        success = success and ok

        # 7. Security events
        ok, _ = self.run_stage(
            'Security Events',
            self.scripts_dir / 'collect_security_events.py',
            'Collecting security events from last 24 hours'
        )
        success = success and ok

        self.log('')

        # Stage 2: Intelligence Extraction
        self.log('🧠 PHASE 2: INTELLIGENCE EXTRACTION')
        self.log('-' * 50)

        # 8. Asset extraction
        ok, _ = self.run_stage(
            'Asset Intelligence',
            self.scripts_dir / 'extract_asset_intelligence.py',
            'Extracting asset inventory from Nessus'
        )
        success = success and ok

        # 9. Service extraction
        ok, _ = self.run_stage(
            'Service Intelligence',
            self.scripts_dir / 'collect_service_intelligence.py',
            'Extracting network services'
        )
        success = success and ok

        # 10. Crypto inventory
        ok, _ = self.run_stage(
            'Crypto Inventory',
            self.scripts_dir / 'collect_crypto_inventory.py',
            'Analyzing cryptographic material'
        )
        success = success and ok

        self.log('')

        # Stage 3: Scoring
        self.log('🎯 PHASE 3: RISK SCORING')
        self.log('-' * 50)

        # 11. WAAP score calculation
        ok, _ = self.run_stage(
            'WAAP Score',
            self.scripts_dir / 'calculate_waap_score.py',
            'Calculating WAAP risk score'
        )
        success = success and ok

        self.log('')

        # Stage 4: Reporting
        self.log('📝 PHASE 4: REPORT GENERATION')
        self.log('-' * 50)

        # 12. Daily brief generation
        ok, _ = self.run_stage(
            'Daily Brief',
            self.scripts_dir / 'generate_daily_brief.py',
            'Generating daily intelligence brief'
        )
        success = success and ok

        self.log('')

        # Stage 5: Risk Assessment
        self.log('🎯 PHASE 5: RISK ASSESSMENT')
        self.log('-' * 50)

        # 13. Calculate overall risk score (with MCP data)
        ok, _ = self.run_stage(
            'Risk Score',
            self.scripts_dir / 'calculate_risk_score.py',
            'Calculating overall risk score (with MCP telemetry)'
        )
        success = success and ok

        self.log('')

        # Stage 6: Decision Engine
        self.log('💡 PHASE 6: DECISION ENGINE')
        self.log('-' * 50)

        # 14. Generate recommended actions (with MCP decisions)
        ok, _ = self.run_stage(
            'Recommended Actions',
            self.scripts_dir / 'generate_recommended_actions.py',
            'Generating actionable decisions'
        )
        success = success and ok

        self.log('')

        # Final summary
        if success:
            self.pipeline_results['status'] = 'success'
            self.log('✅ PIPELINE COMPLETED SUCCESSFULLY')
        else:
            self.pipeline_results['status'] = 'failed'
            self.log('❌ PIPELINE COMPLETED WITH ERRORS')

        # Calculate total duration
        total_duration = time.time() - self.start_time
        self.log(f'   Total duration: {total_duration:.1f}s')

        # Generate health summary
        self.log('')
        self.generate_health_summary()

        # Save pipeline results
        results_file = self.logs_dir / 'pipeline_results.json'
        self.pipeline_results['duration'] = total_duration
        self.pipeline_results['end_time'] = datetime.now().isoformat()
        with open(results_file, 'w') as f:
            json.dump(self.pipeline_results, f, indent=2)

        self.log(f'📋 Results saved to: {results_file}')

        return 0 if success else 1


def main():
    pipeline = IntelligencePipeline()
    exit_code = pipeline.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
