#!/usr/bin/env python3
"""
SENTINELOPS INTELLIGENCE PIPELINE ORCHESTRATOR (Phase N.4)
Automatically updates all asset, service, and security intelligence
Runs all collectors and intelligence extractors in sequence
Outputs: Comprehensive state/ updates and daily brief
"""

import io
import json
import sys
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Import atomic write functions for file safety (TD-L3-001, TD-L3-002, TD-L3-003)
from state_manager import write_state_atomic, read_state_safe

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
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')

    def run_stage(self, stage_name, script_path, description):
        """Run a single pipeline stage"""
        self.log(f'▶ Starting: {description}')
        stage_start = time.time()

        try:
            child_env = dict(os.environ)
            child_env['PYTHONIOENCODING'] = 'utf-8'

            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.project_root),
                env=child_env,
                capture_output=True,
                text=True,
                # encoding/errors là bắt buộc: text=True dùng codec của locale
                # (cp1252 trên máy này), còn script con in JSON UTF-8 có tiếng
                # Việt. Khi giải mã hỏng, Python 3.7 không báo UnicodeDecodeError
                # mà ném "IndexError: list index out of range" từ luồng đọc - một
                # thông báo không liên quan gì tới nguyên nhân thật.
                encoding='utf-8',
                errors='replace',
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

        # Risk level đọc từ engine chuẩn, không tự tính lại.
        #
        # Trước đây dòng này lấy trung bình crypto + WAAP rồi tự xếp hạng - một
        # engine rủi ro thứ tư, sống sót qua cả Sprint 6 (vốn đã xoá risk_engine.py
        # và bộ chấm điểm riêng của Daily Brief). Nó in ra HIGH trong khi
        # state/risk_score.json ghi MEDIUM, và đây là dòng con người thực sự đọc
        # ở cuối mỗi lần chạy.
        risk_state = self.load_state_file('risk_score.json')
        if isinstance(risk_state, dict) and risk_state.get('risk_level'):
            risk_level = risk_state['risk_level']
            risk_score_val = risk_state.get('overall_score')
        else:
            risk_level = 'UNKNOWN'
            risk_score_val = None

        # Display summary
        self.log(f'Assets:       {asset_count}')
        self.log(f'Services:     {service_count}')
        self.log(f'Crypto Score: {crypto_score}')
        self.log(f'WAAP Score:   {waap_score_val}')
        self.log(f'Risk Level:   {risk_level}' +
                 (f' (score {risk_score_val}/100)' if risk_score_val is not None else ''))
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

        # 8A. Trust scoring (Sprint 11)
        # asset_builder.py tồn tại từ lâu nhưng chưa bao giờ nằm trong pipeline,
        # và nó đọc khoá `all_assets` mà tệp sống không có — nên nó thoát ngay ở
        # dòng đầu và `trust_score` chưa từng xuất hiện trong assets.json. Mọi
        # nơi tiêu thụ đọc trường đó đều nhận về None và hiển thị "N/A" như thể
        # đó là một giá trị bình thường.
        #
        # Phải chạy SAU extract (extract ghi đè toàn bộ tồn kho từ Nessus, xoá
        # mọi trường làm giàu) và TRƯỚC shadow detection.
        ok, _ = self.run_stage(
            'Asset Trust Scoring',
            self.scripts_dir / 'asset_builder.py',
            'Scoring asset trust from observable evidence only'
        )
        success = success and ok

        # 8B. Shadow asset detection (Sprint 6.1)
        # Chạy ngay sau asset extraction vì nó đối chiếu kho tài sản vừa dựng với
        # bảng ARP thật; kết quả là đầu vào của correlation Rule 1 ở Phase 10.
        # Trước Sprint 6.1 script này không nằm trong pipeline, nên
        # state/shadow_assets.json đứng yên từ 2026-09-09.
        ok, _ = self.run_stage(
            'Shadow Asset Detection',
            self.scripts_dir / 'shadow_asset_detector.py',
            'Detecting unknown devices (ARP vs asset inventory)'
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

        # Stage 4 (Report Generation) moved to Phase 11 in Sprint 6: the Daily
        # Brief now reports the canonical risk score instead of computing its
        # own, so it has to run after Risk Assessment.

        # Stage 5 (Risk Assessment) moved to Phase 9B in Sprint 6: the canonical
        # engine now weights incident severity at 25%, so it has to run after the
        # Incident Engine or it would always score the previous cycle's incidents.

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

        # Stage 7: Timeline & Change Detection
        self.log('📅 PHASE 7: INCIDENT & CHANGE TIMELINE')
        self.log('-' * 50)

        # 15. Detect timeline events and changes
        ok, _ = self.run_stage(
            'Timeline Events',
            self.scripts_dir / 'collect_timeline_events.py',
            'Detecting changes in last 24 hours'
        )
        success = success and ok

        self.log('')

        # Stage 7B: Threat Hunting Integration (Phase N.9A)
        self.log('🎯 PHASE 7B: THREAT HUNTING DETECTION')
        self.log('-' * 50)

        # 15B. Hunt persistence indicators
        ok, _ = self.run_stage(
            'Persistence Hunting',
            self.scripts_dir / 'hunt_persistence_indicators.py',
            'Hunting for persistence indicators'
        )
        success = success and ok

        # 15C. Hunt suspicious processes
        ok, _ = self.run_stage(
            'Suspicious Process Hunting',
            self.scripts_dir / 'hunt_suspicious_processes.py',
            'Detecting suspicious process execution'
        )
        success = success and ok

        # 15D. Hunt lateral movement (Phase N.9B)
        ok, _ = self.run_stage(
            'Lateral Movement Hunting',
            self.scripts_dir / 'hunt_lateral_movement.py',
            'Detecting lateral movement indicators'
        )
        success = success and ok

        # 15E. Hunt credential dumping (Phase N.9B)
        ok, _ = self.run_stage(
            'Credential Dumping Hunting',
            self.scripts_dir / 'hunt_credential_dumping.py',
            'Detecting credential dumping attempts'
        )
        success = success and ok

        self.log('')

        # Stage 8: Triage Engine
        self.log('🎯 PHASE 8: TRIAGE ENGINE')
        self.log('-' * 50)

        # 16. Generate priority queue
        ok, _ = self.run_stage(
            'Priority Queue',
            self.scripts_dir / 'generate_priority_queue.py',
            'Generating TOP 5 priority items'
        )
        success = success and ok

        self.log('')

        # Stage 9: Incident Engine
        self.log('🚨 PHASE 9: INCIDENT ENGINE')
        self.log('-' * 50)

        # 17. Generate incidents
        ok, _ = self.run_stage(
            'Incident Detection',
            self.scripts_dir / 'generate_incidents.py',
            'Detecting and creating incidents'
        )
        success = success and ok

        self.log('')

        # Stage 9B: Risk Assessment (moved here from Phase 5 in Sprint 6)
        self.log('🎯 PHASE 9B: RISK ASSESSMENT')
        self.log('-' * 50)

        # 17B. Canonical risk engine - the only writer of state/risk_score.json
        ok, _ = self.run_stage(
            'Risk Score',
            self.scripts_dir / 'calculate_risk_score.py',
            'Calculating overall risk score (assets + incidents + hunting + telemetry)'
        )
        success = success and ok

        self.log('')

        # Stage 10: Executive Correlation (Sprint 5)
        self.log('🔗 PHASE 10: EXECUTIVE CORRELATION')
        self.log('-' * 50)

        # 18. Correlate shadow assets + incidents + hunting into executive findings
        ok, _ = self.run_stage(
            'Correlation Engine',
            self.scripts_dir / 'correlation_engine.py',
            'Correlating multi-source signals into executive findings'
        )
        success = success and ok

        self.log('')

        # Stage 11: Reporting (moved here from Phase 4 in Sprint 6)
        self.log('📝 PHASE 11: REPORT GENERATION')
        self.log('-' * 50)

        # 19. Daily brief - reports the canonical risk score, so it runs last
        ok, _ = self.run_stage(
            'Daily Brief',
            self.scripts_dir / 'generate_daily_brief.py',
            'Generating daily intelligence brief'
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
        write_state_atomic(results_file, self.pipeline_results, indent=2)

        self.log(f'📋 Results saved to: {results_file}')

        return 0 if success else 1


def _force_utf8_stdout():
    """Giu stdout o UTF-8 ke ca khi no bi chuyen huong ra file.

    Tren Windows, stdout gan vao console dung UTF-8, nhung stdout bi chuyen
    huong lai dung cp1252. Dong log dau tien cua pipeline co mot emoji, nen
    `python run_intelligence_pipeline.py > pipeline.log` chet ngay o dong log
    dau tien voi UnicodeEncodeError — truoc khi chay bat ky stage nao. Moi lan
    chay theo lich (ghi log ra file) deu roi vao duong nay.
    """
    for stream_name in ('stdout', 'stderr'):
        stream = getattr(sys, stream_name, None)
        encoding = (getattr(stream, 'encoding', '') or '').lower()
        if stream is None or encoding.replace('-', '') == 'utf8':
            continue
        try:
            setattr(sys, stream_name, io.TextIOWrapper(
                stream.buffer, encoding='utf-8', errors='replace',
                line_buffering=True))
        except (AttributeError, ValueError):
            pass


def main():
    _force_utf8_stdout()
    pipeline = IntelligencePipeline()
    exit_code = pipeline.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
