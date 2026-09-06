#!/usr/bin/env python3
"""
SENTINELOPS - COMPLETE DATA COLLECTION ORCHESTRATOR
Runs all collectors in sequence and generates integrated view
"""

import json
import sys
import subprocess
from datetime import datetime
from pathlib import Path


class SentinelOpsOrchestrator:
    def __init__(self):
        self.scripts_dir = Path(__file__).parent
        self.state_dir = self.scripts_dir.parent / 'state'
        self.state_dir.mkdir(exist_ok=True)

        self.collectors = [
            # Windows system (Node.js) - skipped here, run separately
            ('Nessus', 'collect_nessus_snapshot.py'),
            ('Domain', 'collect_domain_snapshot.py'),
            ('WAAP', 'collect_waap_snapshot.py'),
        ]

        self.results = {}
        self.errors = []

    def run_collector(self, name, script):
        """Run a single collector script"""
        print(f'  ▶ {name}...', end='', flush=True)

        try:
            result = subprocess.run(
                [sys.executable, str(self.scripts_dir / script)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                self.results[name.lower()] = data
                print(f' ✅')
                return True
            else:
                error = result.stderr if result.stderr else 'No output'
                self.errors.append(f'{name}: {error}')
                print(f' ❌')
                return False

        except subprocess.TimeoutExpired:
            error = f'{name}: Timeout (30s)'
            self.errors.append(error)
            print(f' ⏱️')
            return False

        except Exception as e:
            error = f'{name}: {str(e)}'
            self.errors.append(error)
            print(f' ❌')
            return False

    def collect_all(self):
        """Run all collectors"""
        print('\n📊 SENTINELOPS DATA COLLECTION')
        print('=' * 60)

        for name, script in self.collectors:
            self.run_collector(name, script)

        return len(self.errors) == 0

    def generate_summary(self):
        """Generate collection summary"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'collections': self.results,
            'errors': self.errors,
            'status': 'OK' if not self.errors else 'PARTIAL'
        }

        return summary

    def print_summary(self, summary):
        """Print collection summary"""
        print('\n' + '=' * 60)
        print('COLLECTION SUMMARY')
        print('=' * 60)

        if self.results:
            print(f'\n✅ Collected ({len(self.results)}):')
            for name in self.results:
                print(f'   • {name.upper()}')

        if self.errors:
            print(f'\n⚠️  Errors ({len(self.errors)}):')
            for error in self.errors:
                print(f'   • {error}')

        print(f'\nStatus: {summary["status"]}')
        print('=' * 60 + '\n')

    def save_summary(self, summary):
        """Save collection summary"""
        try:
            summary_file = self.state_dir / 'collection_summary.json'
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f'📁 Summary saved: {summary_file}')
        except Exception as e:
            print(f'⚠️  Failed to save summary: {e}')

    def run(self):
        """Main orchestration logic"""
        success = self.collect_all()
        summary = self.generate_summary()
        self.print_summary(summary)
        self.save_summary(summary)

        # Print example output
        if self.results:
            print('📋 SAMPLE DATA:\n')
            if 'nessus' in self.results:
                print('Nessus Status:')
                print(json.dumps(self.results['nessus'], indent=2)[:200] + '...\n')
            if 'domain' in self.results:
                print('Domain Status:')
                print(json.dumps(self.results['domain'], indent=2)[:200] + '...\n')
            if 'waap' in self.results:
                print('WAAP Status:')
                print(json.dumps(self.results['waap'], indent=2)[:200] + '...\n')

        return 0 if success else 1


def main():
    orchestrator = SentinelOpsOrchestrator()
    exit_code = orchestrator.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
