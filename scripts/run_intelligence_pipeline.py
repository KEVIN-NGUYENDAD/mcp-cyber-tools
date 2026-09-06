#!/usr/bin/env python3
"""SentinelOps Intelligence Pipeline Orchestrator (Phase N.4)"""
import json, sys, os, subprocess, time
from datetime import datetime
from pathlib import Path

class IntelligencePipeline:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.scripts_dir = self.project_root / 'scripts'
        self.state_dir = self.project_root / 'state'
        self.logs_dir = self.project_root / 'logs'
        self.state_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.log_file = self.logs_dir / 'pipeline.log'
        self.start_time = time.time()
        self.results = {'timestamp': datetime.now().isoformat(), 'stages': [], 'status': 'running'}
    
    def log(self, msg):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entry = f'[{ts}] {msg}'
        print(entry)
        with open(self.log_file, 'a') as f:
            f.write(entry + '\n')
    
    def run_stage(self, name, script, desc):
        self.log(f'Starting: {desc}')
        try:
            r = subprocess.run([sys.executable, str(script)], cwd=str(self.project_root), capture_output=True, text=True, timeout=300)
            if r.returncode == 0:
                self.log(f'SUCCESS: {name}')
                self.results['stages'].append({'name': name, 'status': 'success'})
                return True
            else:
                self.log(f'FAILED: {name} - {r.stderr}')
                self.results['stages'].append({'name': name, 'status': 'failed'})
                return False
        except Exception as e:
            self.log(f'ERROR: {name} - {str(e)}')
            self.results['stages'].append({'name': name, 'status': 'error'})
            return False
    
    def run(self):
        self.log('Starting SentinelOps Intelligence Pipeline')
        success = True
        
        self.log('PHASE 1: DATA COLLECTION')
        success &= self.run_stage('Nessus', self.scripts_dir / 'collect_nessus_snapshot.py', 'Collecting Nessus data')
        success &= self.run_stage('Domain', self.scripts_dir / 'collect_domain_snapshot.py', 'Collecting domain data')
        success &= self.run_stage('WAAP', self.scripts_dir / 'collect_waap_snapshot.py', 'Collecting WAAP data')
        
        self.log('PHASE 2: INTELLIGENCE EXTRACTION')
        success &= self.run_stage('Assets', self.scripts_dir / 'extract_asset_intelligence.py', 'Extracting assets')
        success &= self.run_stage('Services', self.scripts_dir / 'collect_service_intelligence.py', 'Extracting services')
        success &= self.run_stage('Crypto', self.scripts_dir / 'collect_crypto_inventory.py', 'Analyzing crypto')
        
        self.log('PHASE 3: RISK SCORING')
        success &= self.run_stage('WAAP Score', self.scripts_dir / 'calculate_waap_score.py', 'Calculating WAAP score')
        success &= self.run_stage('Risk Score', self.scripts_dir / 'calculate_risk_score.py', 'Calculating overall risk score')

        self.log('PHASE 3B: CONTROL BASELINE COMPARISON (Phase N.10A)')
        success &= self.run_stage('Control Baseline', self.scripts_dir / 'baseline_controls.py', 'Detecting control drift')
        success &= self.run_stage('Drift Events', self.scripts_dir / 'collect_drift_events.py', 'Collecting drift events')

        self.log('PHASE 9: INCIDENT ENGINE')
        success &= self.run_stage('Incidents', self.scripts_dir / 'generate_incidents.py', 'Generating incidents from control drift')
        success &= self.run_stage('Priority Queue', self.scripts_dir / 'generate_priority_queue.py', 'Generating priority queue from incidents')
        success &= self.run_stage('Threat Hunting', self.scripts_dir / 'generate_threat_hunting_results.py', 'Generating threat hunting results')

        self.log('PHASE 10: TRUST LAYER (N.10B + N.10C)')
        success &= self.run_stage('System Health', self.scripts_dir / 'collect_system_health.py', 'Collecting system health metrics')
        success &= self.run_stage('Data Freshness', self.scripts_dir / 'track_data_freshness.py', 'Tracking data freshness and age')
        success &= self.run_stage('Leak Guard', self.scripts_dir / 'leak_guard.py', 'Scanning for data leaks')

        self.log('PHASE 4: REPORTING & RELEASE')
        success &= self.run_stage('Alerts', self.scripts_dir / 'generate_alerts.py', 'Generating security alerts')
        success &= self.run_stage('SOC Scorecard', self.scripts_dir / 'generate_soc_scorecard.py', 'Calculating SOC scorecard')
        success &= self.run_stage('Weekly Report', self.scripts_dir / 'generate_weekly_report.py', 'Generating weekly executive report')
        success &= self.run_stage('Brief', self.scripts_dir / 'generate_daily_brief.py', 'Generating daily brief')
        
        self.results['status'] = 'success' if success else 'failed'
        self.log(f'Pipeline completed: {self.results["status"]}')
        
        total = time.time() - self.start_time
        self.log(f'Total time: {total:.1f}s')
        
        return 0 if success else 1

if __name__ == '__main__':
    pipeline = IntelligencePipeline()
    sys.exit(pipeline.run())
