#!/usr/bin/env python3
"""
AUTO-INVESTIGATION PLAYBOOK (Sprint 5)
Khi Incident Engine sinh ra sự cố mức CRITICAL, tự động chạy chuỗi 4 công cụ
săn lùng chuyên sâu, đóng gói kết quả thành hồ sơ điều tra và báo về Telegram.

Không tạo công cụ hunting mới - chỉ điều phối các script đã có trong scripts/.

Chuỗi điều tra:
  1. hunt_persistence_indicators.py   -> state/hunting_persistence.json
  2. hunt_suspicious_processes.py     -> state/hunting_suspicious_processes.json
  3. hunt_credential_dumping.py       -> state/hunting_credential_dumping.json
  4. collect_timeline_events.py       -> state/timeline.json

Outputs: state/investigation_reports/CASE_<INCIDENT_ID>.json

Usage:
  python scripts/auto_investigation_playbook.py                 # chạy thật
  python scripts/auto_investigation_playbook.py --dry-run       # không chạy hunt, không gửi Telegram
  python scripts/auto_investigation_playbook.py --no-telegram   # chạy hunt, không gửi
  python scripts/auto_investigation_playbook.py --incident INC-0032
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Atomic write / safe read (TD-L3-001, TD-L3-002, TD-L3-003)
from state_manager import write_state_atomic, read_state_safe

try:
    import requests
except ImportError:
    requests = None

PLAYBOOK_VERSION = '1.0.0'
TRIGGER_SEVERITY = 'CRITICAL'
HUNT_TIMEOUT = 300

# Chống gửi trùng: cùng một case không báo lại trong 30 phút.
# Cùng cửa sổ với scripts/telegram/alertDelivery.js để hai đường không đá nhau.
TELEGRAM_DEDUP_WINDOW = 30 * 60

# Chuỗi hunt. Mỗi mục: (nhãn, script, state file kết quả, khoá đếm)
HUNT_CHAIN = [
    ('hunt_persistence', 'hunt_persistence_indicators.py',
     'hunting_persistence.json', 'indicators'),
    ('hunt_suspicious_processes', 'hunt_suspicious_processes.py',
     'hunting_suspicious_processes.json', 'indicators'),
    ('hunt_credential_dumping', 'hunt_credential_dumping.py',
     'hunting_credential_dumping.json', 'indicators'),
    ('collect_timeline_events', 'collect_timeline_events.py',
     'timeline.json', 'events'),
]


# ----------------------------------------------------------------------
# TELEGRAM
# ----------------------------------------------------------------------

def load_credentials(project_root):
    """Đọc TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID từ biến môi trường hoặc .env."""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if bot_token and chat_id:
        return bot_token, chat_id

    env_file = Path(project_root) / '.env'
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('TELEGRAM_BOT_TOKEN=') and not bot_token:
                    bot_token = line.split('=', 1)[1].strip()
                elif line.startswith('TELEGRAM_CHAT_ID=') and not chat_id:
                    chat_id = line.split('=', 1)[1].strip()
    except IOError:
        return None, None

    if not bot_token or not chat_id:
        return None, None

    return bot_token, chat_id


def safe_send_message(message, project_root, dedup_key=None, dedup_state=None,
                      dry_run=False):
    """Gửi Telegram an toàn: không bao giờ ném exception ra ngoài playbook.

    An toàn ở đây gồm bốn lớp:
      - dry_run  : render nhưng không gọi API
      - dedup    : cùng dedup_key không gửi lại trong TELEGRAM_DEDUP_WINDOW
      - guard    : thiếu credential hoặc thiếu `requests` thì bỏ qua, báo lý do
      - no-raise : lỗi mạng/API trả về dict status thay vì làm hỏng hồ sơ điều tra

    Trả về dict {'status': ..., 'detail': ...}. Điều tra đã chạy xong rồi, nên
    lỗi gửi tin không được phép làm mất báo cáo.
    """
    if dry_run:
        return {'status': 'skipped', 'detail': 'dry-run: không gọi Telegram API',
                'rendered_chars': len(message)}

    if dedup_key and dedup_state is not None:
        last = dedup_state.get(dedup_key)
        if last is not None and (time.time() - last) < TELEGRAM_DEDUP_WINDOW:
            return {'status': 'deduplicated',
                    'detail': 'đã gửi cho {} trong {} phút gần đây'.format(
                        dedup_key, TELEGRAM_DEDUP_WINDOW // 60)}

    if requests is None:
        return {'status': 'unavailable', 'detail': 'thiếu thư viện requests'}

    bot_token, chat_id = load_credentials(project_root)
    if not bot_token or not chat_id:
        return {'status': 'unconfigured',
                'detail': 'thiếu TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID'}

    api_url = 'https://api.telegram.org/bot{}/sendMessage'.format(bot_token)
    payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}

    try:
        response = requests.post(api_url, json=payload, timeout=10)
        data = response.json()
        if response.status_code == 200 and data.get('ok'):
            if dedup_key and dedup_state is not None:
                dedup_state[dedup_key] = time.time()
            return {'status': 'sent',
                    'message_id': data.get('result', {}).get('message_id')}
        return {'status': 'failed',
                'detail': data.get('description', 'HTTP {}'.format(response.status_code))}
    except Exception as error:  # mạng, JSON hỏng, timeout - đều không được nổ
        return {'status': 'failed', 'detail': str(error)}


# ----------------------------------------------------------------------
# PLAYBOOK
# ----------------------------------------------------------------------

class AutoInvestigationPlaybook:
    def __init__(self, dry_run=False, send_telegram=True, incident_id=None):
        self.project_root = Path(__file__).parent.parent
        self.scripts_dir = self.project_root / 'scripts'
        self.state_dir = self.project_root / 'state'
        self.reports_dir = self.state_dir / 'investigation_reports'

        self.dry_run = dry_run
        self.send_telegram = send_telegram
        self.incident_filter = incident_id

        self._dedup_state = {}

    # ------------------------------------------------------------------

    def find_trigger_incidents(self):
        """Lấy các sự cố CRITICAL đang OPEN - điều kiện kích hoạt playbook."""
        data = read_state_safe(self.state_dir / 'incidents.json', dict)
        incidents = data.get('incidents')
        incidents = incidents if isinstance(incidents, list) else []

        triggers = []
        for incident in incidents:
            if incident.get('severity') != TRIGGER_SEVERITY:
                continue
            if incident.get('status') not in (None, 'OPEN'):
                continue
            if self.incident_filter and incident.get('incident_id') != self.incident_filter:
                continue
            triggers.append(incident)

        return triggers

    def run_hunt(self, label, script_name, state_file, count_key):
        """Chạy một công cụ hunt và đọc lại kết quả từ state/."""
        script_path = self.scripts_dir / script_name
        result = {
            'tool': label,
            'script': script_name,
            'state_file': state_file,
            'status': 'pending',
            'findings': 0,
            'by_severity': {},
            'details': [],
        }

        if not script_path.exists():
            result['status'] = 'missing'
            result['error'] = 'không tìm thấy {}'.format(script_path)
            return result

        if self.dry_run:
            # Không chạy lại hunt, chỉ đọc kết quả đang có trên đĩa.
            result['status'] = 'dry-run'
        else:
            started = time.time()
            try:
                hunt_env = dict(os.environ)
                hunt_env['PYTHONIOENCODING'] = 'utf-8'
                proc = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    # Cùng lý do như trong run_intelligence_pipeline: locale
                    # cp1252 không giải mã được JSON UTF-8 của script con.
                    encoding='utf-8',
                    errors='replace',
                    env=hunt_env,
                    timeout=HUNT_TIMEOUT,
                )
                result['duration'] = round(time.time() - started, 1)
                if proc.returncode == 0:
                    result['status'] = 'success'
                else:
                    result['status'] = 'failed'
                    result['error'] = (proc.stderr or '').strip()[:500]
            except subprocess.TimeoutExpired:
                result['status'] = 'timeout'
                result['error'] = 'quá {}s'.format(HUNT_TIMEOUT)
            except Exception as error:
                result['status'] = 'error'
                result['error'] = str(error)

        # Đọc kết quả kể cả khi hunt lỗi - dữ liệu cũ vẫn có giá trị điều tra.
        data = read_state_safe(self.state_dir / state_file, dict)
        items = data.get(count_key)
        items = items if isinstance(items, list) else []

        result['findings'] = len(items)
        result['data_timestamp'] = data.get('timestamp')
        # Sprint 6.1: hồ sơ điều tra phải nói rõ bằng chứng đến từ đâu. Một case
        # ghi "Mimikatz Activity" kèm lệnh "Ngắt mạng" mà không nói đó là dữ liệu
        # mô phỏng sẽ đẩy người trực ca đi cô lập một máy bình thường.
        result['data_source'] = data.get('data_source', 'UNKNOWN')

        by_severity = {}
        for item in items:
            severity = item.get('severity', 'UNKNOWN')
            by_severity[severity] = by_severity.get(severity, 0) + 1
        result['by_severity'] = by_severity

        # Chỉ giữ phần đáng chú ý để hồ sơ không phình ra vô ích.
        for item in items:
            if item.get('severity') in ('CRITICAL', 'HIGH'):
                result['details'].append({
                    'type': item.get('type') or item.get('category') or item.get('event'),
                    'severity': item.get('severity'),
                    'description': item.get('description'),
                    'process': item.get('process'),
                    'command_line': item.get('command_line'),
                    'evidence': item.get('evidence'),
                    'recommendation': item.get('recommendation'),
                })

        return result

    def run_hunt_chain(self):
        results = []
        for label, script, state_file, count_key in HUNT_CHAIN:
            results.append(self.run_hunt(label, script, state_file, count_key))
        return results

    # ------------------------------------------------------------------

    def summarize_hunting(self, hunt_results):
        """Rút gọn chuỗi hunt thành các dòng 'Phát hiện từ Hunting' cho Telegram."""
        lines = []
        for result in hunt_results:
            if result['findings'] == 0:
                continue
            severities = ', '.join(
                '{} {}'.format(count, sev)
                for sev, count in sorted(result['by_severity'].items()))
            top = result['details'][0]['type'] if result['details'] else None
            label = ' [MÔ PHỎNG]' if result.get('data_source') == 'SIMULATED' else ''
            line = '{}: {} phát hiện ({}){}'.format(
                result['tool'], result['findings'], severities, label)
            if top:
                line += ' - nổi bật: {}'.format(top)
            lines.append(line)
        return lines or ['Không có phát hiện nào từ chuỗi hunt']

    def resolve_target(self, incident):
        """Thiết bị liên quan tới sự cố. Rỗng nghĩa là IOC chưa được quy kết."""
        assets = incident.get('assets')
        if isinstance(assets, list) and assets:
            return ', '.join(str(a) for a in assets)
        return 'Chưa quy kết được (IOC không mang IP/hostname)'

    def evidence_quality(self, hunt_results):
        """REAL / SIMULATED / MIXED cho cả chuỗi hunt của một case."""
        sources = set(r.get('data_source', 'UNKNOWN')
                      for r in hunt_results if r['findings'])
        if not sources:
            return 'NONE'
        if sources == set(['SIMULATED']):
            return 'SIMULATED'
        if 'SIMULATED' in sources:
            return 'MIXED'
        return 'REAL'

    def build_telegram_message(self, incident, hunt_results):
        hunting_lines = self.summarize_hunting(hunt_results)
        quality = self.evidence_quality(hunt_results)

        # Giữ nguyên bố cục bốn dòng theo đặc tả Sprint 5; chỉ chèn thêm một dòng
        # cảnh báo khi bằng chứng không phải quan sát thật.
        warning = ''
        if quality in ('SIMULATED', 'MIXED'):
            warning = ('\n⚠️ BẰNG CHỨNG {}: chuỗi hunt trả về dữ liệu hardcode '
                       'trong script, chưa nối với MCP hunting tool. '
                       'KHÔNG cô lập thiết bị dựa trên case này.').format(quality)

        return (
            '🚨 TỰ ĐỘNG ĐIỀU TRA SỰ CỐ {}\n'
            '• Thiết bị: {}\n'
            '• Phát hiện từ Hunting: {}\n'
            '• Kịch bản cô lập đề xuất: 1. Ngắt mạng | 2. Quét Defender | 3. Khôi phục{}'
        ).format(
            incident.get('incident_id', 'UNKNOWN'),
            self.resolve_target(incident),
            '; '.join(hunting_lines),
            warning,
        )

    def build_case_report(self, incident, hunt_results, telegram_result, message):
        total = sum(r['findings'] for r in hunt_results)
        by_severity = {}
        for result in hunt_results:
            for severity, count in result['by_severity'].items():
                by_severity[severity] = by_severity.get(severity, 0) + count

        return {
            'case_id': 'CASE_{}'.format(incident.get('incident_id', 'UNKNOWN')),
            'incident_id': incident.get('incident_id'),
            'playbook_version': PLAYBOOK_VERSION,
            'triggered_at': datetime.now().isoformat(),
            'trigger': {
                'severity': incident.get('severity'),
                'status': incident.get('status'),
                'title': incident.get('title'),
                'description': incident.get('description'),
                'created_at': incident.get('created_at'),
            },
            'target': {
                'assets': incident.get('assets') or [],
                'resolved': self.resolve_target(incident),
            },
            'mode': 'dry-run' if self.dry_run else 'live',
            'hunt_chain': hunt_results,
            'evidence_quality': self.evidence_quality(hunt_results),
            'summary': {
                'tools_run': len(hunt_results),
                'tools_succeeded': sum(
                    1 for r in hunt_results if r['status'] in ('success', 'dry-run')),
                'total_findings': total,
                'by_severity': by_severity,
            },
            'containment_plan': [
                '1. Ngắt mạng',
                '2. Quét Defender',
                '3. Khôi phục',
            ],
            'incident_evidence': incident.get('evidence') or [],
            'incident_recommended_action': incident.get('recommended_action'),
            'notification': telegram_result,
            'notification_message': message,
        }

    def save_case_report(self, report):
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        path = self.reports_dir / '{}.json'.format(report['case_id'])
        write_state_atomic(path, report, indent=2)
        return path

    # ------------------------------------------------------------------

    def run(self):
        triggers = self.find_trigger_incidents()

        if not triggers:
            return {
                'status': 'no_trigger',
                'reason': 'không có sự cố {} đang OPEN'.format(TRIGGER_SEVERITY),
                'cases': [],
            }

        # Chuỗi hunt chỉ chạy một lần cho cả đợt: 4 công cụ này quét toàn máy,
        # chạy lại cho từng sự cố trong số hàng chục CRITICAL là lãng phí và
        # còn làm nhiễu chính dữ liệu đang điều tra.
        hunt_results = self.run_hunt_chain()

        cases = []
        for incident in triggers:
            message = self.build_telegram_message(incident, hunt_results)

            if self.send_telegram:
                telegram_result = safe_send_message(
                    message,
                    self.project_root,
                    dedup_key=incident.get('incident_id'),
                    dedup_state=self._dedup_state,
                    dry_run=self.dry_run,
                )
            else:
                telegram_result = {'status': 'disabled',
                                   'detail': '--no-telegram'}

            report = self.build_case_report(incident, hunt_results,
                                            telegram_result, message)
            path = self.save_case_report(report)

            cases.append({
                'case_id': report['case_id'],
                'incident_id': report['incident_id'],
                'title': incident.get('title'),
                'findings': report['summary']['total_findings'],
                'notification': telegram_result['status'],
                'report': str(path),
            })

        return {
            'status': 'success',
            'mode': 'dry-run' if self.dry_run else 'live',
            'triggers': len(triggers),
            'hunt_chain': [
                {'tool': r['tool'], 'status': r['status'], 'findings': r['findings']}
                for r in hunt_results
            ],
            'cases': cases,
        }


def main():
    parser = argparse.ArgumentParser(
        description='Auto-investigation playbook cho sự cố CRITICAL')
    parser.add_argument('--dry-run', action='store_true',
                        help='Không chạy hunt và không gửi Telegram; chỉ dựng hồ sơ từ state hiện có')
    parser.add_argument('--no-telegram', action='store_true',
                        help='Chạy hunt nhưng không gửi thông báo')
    parser.add_argument('--incident', metavar='INC-XXXX',
                        help='Chỉ điều tra một sự cố cụ thể')
    args = parser.parse_args()

    playbook = AutoInvestigationPlaybook(
        dry_run=args.dry_run,
        send_telegram=not args.no_telegram,
        incident_id=args.incident,
    )
    result = playbook.run()

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] in ('success', 'no_trigger') else 1


if __name__ == '__main__':
    sys.exit(main())
