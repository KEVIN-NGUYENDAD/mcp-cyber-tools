#!/usr/bin/env python3
"""
Nessus Pipeline Orchestrator - Run every 4 hours
Coordinates asset discovery, risk calculation, and patch queueing
"""

import os
import sys
import json
from datetime import datetime
import schedule
import time
import subprocess

class NessusPipeline:
    def __init__(self):
        self.state_dir = 'state'
        self.log_file = 'nessus_pipeline.log'
        self._ensure_state_dir()

    def _ensure_state_dir(self):
        """Ensure state directory exists"""
        if not os.path.exists(self.state_dir):
            os.makedirs(self.state_dir)
            print(f'[PIPELINE] Created {self.state_dir} directory')

    def log(self, message: str, level: str = 'INFO'):
        """Log message with timestamp"""
        timestamp = datetime.now().isoformat()
        # Replace emoji with ASCII equivalents for Windows compatibility
        message = message.replace('✅', '[OK]').replace('❌', '[FAIL]').replace('⚠️', '[WARN]').replace('⚡', '[FAST]')
        log_entry = f'[{timestamp}] [{level}] {message}'
        try:
            print(log_entry)
        except UnicodeEncodeError:
            print(log_entry.encode('ascii', 'ignore').decode('ascii'))

        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + '\n')
        except:
            pass

    def run_asset_discovery(self) -> bool:
        """Step 1: Discover assets from Nessus"""
        try:
            self.log('Step 1: Discovering assets from Nessus...')
            from asset_builder import AssetBuilder
            builder = AssetBuilder()
            assets = builder.build_assets()
            builder.save(os.path.join(self.state_dir, 'assets.json'))
            self.log(f'[OK] Discovered {assets["total_assets"]} assets', 'SUCCESS')
            return True
        except Exception as e:
            self.log(f'[FAIL] Asset discovery failed: {e}', 'ERROR')
            return False

    def run_risk_calculation(self) -> bool:
        """Step 2: Calculate risk scores"""
        try:
            self.log('Step 2: Calculating risk scores...')
            from risk_engine import RiskEngine
            engine = RiskEngine(os.path.join(self.state_dir, 'assets.json'))
            risks = engine.calculate_risks()
            engine.save(os.path.join(self.state_dir, 'risk_score.json'))
            self.log(f'[OK] Risk score: {risks["overall_score"]} ({risks["threat_level"]})', 'SUCCESS')
            return True
        except Exception as e:
            self.log(f'[FAIL] Risk calculation failed: {e}', 'ERROR')
            return False

    def run_patch_queue_building(self) -> bool:
        """Step 3: Build patch queue"""
        try:
            self.log('Step 3: Building patch queue...')
            from patch_queue import PatchQueueEngine
            engine = PatchQueueEngine(os.path.join(self.state_dir, 'assets.json'))
            engine.build_patch_queue()
            engine.save_patch_queue(os.path.join(self.state_dir, 'patch_queue.json'))
            self.log(f'[OK] Patch queue: {engine.patch_queue["total_patches_pending"]} pending', 'SUCCESS')

            engine.build_crypto_health()
            engine.save_crypto_health(os.path.join(self.state_dir, 'crypto_health.json'))
            self.log(f'[OK] Crypto health: {engine.crypto_health["health_score"]}/100', 'SUCCESS')
            return True
        except Exception as e:
            self.log(f'[FAIL] Patch queue building failed: {e}', 'ERROR')
            return False

    def generate_summary(self):
        """Generate and save pipeline summary"""
        try:
            assets_file = os.path.join(self.state_dir, 'assets.json')
            risk_file = os.path.join(self.state_dir, 'risk_score.json')

            summary = {
                'timestamp': datetime.now().isoformat(),
                'pipeline_status': 'COMPLETE',
                'state_files_updated': [
                    'assets.json',
                    'risk_score.json',
                    'patch_queue.json',
                    'crypto_health.json',
                ],
            }

            if os.path.exists(assets_file):
                with open(assets_file, 'r') as f:
                    assets = json.load(f)
                    summary['total_assets'] = assets.get('total_assets', 0)

            if os.path.exists(risk_file):
                with open(risk_file, 'r') as f:
                    risk = json.load(f)
                    summary['risk_score'] = risk.get('overall_score', 0)
                    summary['threat_level'] = risk.get('threat_level', 'UNKNOWN')

            # Save summary
            summary_file = os.path.join(self.state_dir, 'pipeline_summary.json')
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)

            self.log(f'Pipeline Summary: {summary["total_assets"]} assets, Risk {summary.get("risk_score", 0)}/100', 'INFO')
            return summary
        except Exception as e:
            self.log(f'⚠️  Summary generation failed: {e}', 'WARN')
            return None

    def commit_changes(self):
        """Commit state changes to git"""
        try:
            self.log('Committing state changes...')

            # Check if git is available
            result = subprocess.run(
                ['git', 'add', 'state/'],
                cwd=os.getcwd(),
                capture_output=True,
                timeout=10
            )

            if result.returncode == 0:
                subprocess.run(
                    ['git', 'commit', '-m', f'Auto: Nessus pipeline run {datetime.now().isoformat()}'],
                    cwd=os.getcwd(),
                    capture_output=True,
                    timeout=10
                )
                self.log('[OK] Changes committed to git', 'SUCCESS')
            else:
                self.log('[WARN] Git not available or no changes', 'WARN')
        except Exception as e:
            self.log(f'[WARN] Git commit failed: {e}', 'WARN')

    def run_full_pipeline(self):
        """Execute complete pipeline"""
        self.log('=' * 60)
        self.log('NESSUS PIPELINE START', 'START')
        self.log('=' * 60)

        start_time = datetime.now()

        # Run pipeline steps
        success = True
        success = success and self.run_asset_discovery()
        success = success and self.run_risk_calculation()
        success = success and self.run_patch_queue_building()

        # Generate summary
        self.generate_summary()

        # Commit changes
        if success:
            self.commit_changes()

        elapsed = (datetime.now() - start_time).total_seconds()
        self.log('=' * 60)
        if success:
            self.log(f'[OK] PIPELINE COMPLETE - {elapsed:.1f}s', 'SUCCESS')
        else:
            self.log(f'[FAIL] PIPELINE FAILED - {elapsed:.1f}s', 'ERROR')
        self.log('=' * 60)

        return success

    def schedule_pipeline(self, interval_hours: int = 4):
        """Schedule pipeline to run every N hours"""
        self.log(f'Pipeline scheduled to run every {interval_hours} hours')

        schedule.every(interval_hours).hours.do(self.run_full_pipeline)

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.log('Pipeline scheduler stopped', 'INFO')

if __name__ == '__main__':
    pipeline = NessusPipeline()

    # Run once immediately
    success = pipeline.run_full_pipeline()

    # Check for --schedule flag
    if '--schedule' in sys.argv:
        interval = 4  # Default 4 hours
        if '--interval' in sys.argv:
            try:
                idx = sys.argv.index('--interval')
                interval = int(sys.argv[idx + 1])
            except (IndexError, ValueError):
                pass

        pipeline.schedule_pipeline(interval)
    else:
        sys.exit(0 if success else 1)
