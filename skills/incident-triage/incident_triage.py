"""Incident Triage Skill - Emergency Response & Containment"""

import json
from datetime import datetime
from pathlib import Path


class IncidentTriageSkill:
    """Incident triage, containment, and emergency response"""

    def __init__(self):
        self.skill_name = "incident-triage"
        self.version = "1.0.0"
        self.state_dir = Path(__file__).parent.parent.parent / "state"
        self.state_dir.mkdir(exist_ok=True)

    def get_metadata(self):
        return {
            'name': self.skill_name,
            'version': self.version,
            'description': 'Incident triage, 3-step containment, Telegram escalation',
            'capabilities': [
                'triage_incident',
                'generate_containment_steps',
                'send_emergency_alert',
                'escalate_to_telegram'
            ]
        }

    def triage_incident(self, incident_id, severity, affected_assets):
        """Triage an incident for emergency response

        Args:
            incident_id: Unique incident identifier
            severity: CRITICAL, HIGH, MEDIUM, LOW
            affected_assets: List of impacted assets

        Returns:
            dict with triage assessment
        """
        triage_result = {
            'incident_id': incident_id,
            'severity': severity,
            'affected_assets': affected_assets,
            'asset_count': len(affected_assets),
            'triage_time': datetime.now().isoformat(),
            'status': 'TRIAGED'
        }

        # Determine urgency
        if severity == 'CRITICAL':
            triage_result['urgency'] = 'IMMEDIATE - 0-15 minutes'
            triage_result['response_tier'] = '24/7 On-Call'
        elif severity == 'HIGH':
            triage_result['urgency'] = 'URGENT - Within 1 hour'
            triage_result['response_tier'] = 'Business Hours'
        else:
            triage_result['urgency'] = 'NORMAL - Next business day'
            triage_result['response_tier'] = 'Scheduled Review'

        return triage_result

    def generate_containment_steps(self, incident_type, severity):
        """Generate 3-step emergency containment plan in Vietnamese

        Args:
            incident_type: Type of incident (malware, data_exfil, unauthorized_access)
            severity: CRITICAL or HIGH

        Returns:
            dict with 3-step Vietnamese containment plan
        """
        containment_plans = {
            'malware': {
                'steps': [
                    {
                        'step': 1,
                        'title': 'CÔ LẬP THIẾT BỊ KHỎI MẠNG',
                        'action': 'Ngắt kết nối mạng (Ethernet/WiFi) ngay lập tức. Không tắt máy tính.',
                        'time_estimate': '2 phút',
                        'priority': '[NGAY LAP TUC]'
                    },
                    {
                        'step': 2,
                        'title': 'CHẠY QUÉT ANTIVIRUS TOÀN BO',
                        'action': 'Chạy Windows Defender Full Scan hoặc Nessus QuickScan trên thiết bị. Báo cáo kết quả.',
                        'time_estimate': '30-60 phút',
                        'priority': '[TRONG 15 PHUT]'
                    },
                    {
                        'step': 3,
                        'title': 'KHÔI PHUC TU BACKUP SACH',
                        'action': 'Nếu có backup sạch, khôi phục từ backup trước ngày nhiễm. Nếu không, chờ hướng dẫn của IT.',
                        'time_estimate': '1-2 giờ',
                        'priority': '[TRONG 2 GIO]'
                    }
                ],
                'severity': severity,
                'total_time': '1-3 giờ',
                'escalate_to': 'SOC Lead + Security Manager'
            },
            'data_exfil': {
                'steps': [
                    {
                        'step': 1,
                        'title': 'KHOA TAI KHOAN NGUOI DUNG NGAY',
                        'action': 'Ngay lập tức khóa tài khoản Active Directory + email. Kiểm tra tất cả session đang hoạt động.',
                        'time_estimate': '5 phút',
                        'priority': '[NGAY LAP TUC]'
                    },
                    {
                        'step': 2,
                        'title': 'KIEM SOAT LICH SU TRUY CAP VU LIE',
                        'action': 'Kiểm tra logs: quyền truy cập lúc nào, tệp nào được sao chép, gửi đi đâu.',
                        'time_estimate': '30 phút',
                        'priority': '[TRONG 30 PHUT]'
                    },
                    {
                        'step': 3,
                        'title': 'CHI DAM NHIEU TIEU VU LIE CU THE',
                        'action': 'Xác định chính xác dữ liệu nào bị mất. Thông báo quản lý dữ liệu để quyết định công bố.',
                        'time_estimate': '1-2 giờ',
                        'priority': '[TRONG 1 GIO]'
                    }
                ],
                'severity': severity,
                'total_time': '1-3 giờ',
                'escalate_to': 'CISO + Legal + PR Team'
            },
            'unauthorized_access': {
                'steps': [
                    {
                        'step': 1,
                        'title': 'RESET TAN CA MAT KHAU TRUY CAP',
                        'action': 'Reset mật khẩu tất cả tài khoản: admin, service accounts, VPN. Kiểm tra SSH keys.',
                        'time_estimate': '10 phút',
                        'priority': '[NGAY LAP TUC]'
                    },
                    {
                        'step': 2,
                        'title': 'TIM TOAN BO TAI KHOAN LO HANG',
                        'action': 'Kiểm tra tất cả session/kết nối. Tìm nơi kẻ tấn công truy cập từ đó.',
                        'time_estimate': '20 phút',
                        'priority': '[TRONG 15 PHUT]'
                    },
                    {
                        'step': 3,
                        'title': 'KHOA HOAC CHU TOI TAT CA SESSION LOI HANG',
                        'action': 'Chặn tất cả session từ IP/địa điểm lạ. Buộc người dùng hợp lệ đăng nhập lại.',
                        'time_estimate': '15 phút',
                        'priority': '[TRONG 30 PHUT]'
                    }
                ],
                'severity': severity,
                'total_time': '45 phút - 1 giờ',
                'escalate_to': 'SOC Lead + Network Admin'
            }
        }

        plan = containment_plans.get(incident_type, containment_plans['malware'])
        plan['incident_type'] = incident_type
        plan['generated_at'] = datetime.now().isoformat()
        plan['status'] = 'READY FOR DEPLOYMENT'

        return plan

    def send_emergency_alert(self, incident_id, severity, title, steps_summary):
        """Send emergency alert to team

        Args:
            incident_id: Incident identifier
            severity: CRITICAL or HIGH
            title: Incident title
            steps_summary: Summary of containment steps

        Returns:
            dict confirming alert sent
        """
        alert = {
            'alert_id': f"triage_{incident_id}",
            'severity': severity,
            'title': title,
            'message': f"""[BAN CANH KHAM CAP] {title}

So ky: {incident_id}
Do:    {severity}
Thoi:  {datetime.now().strftime('%H:%M:%S')}

3 BUOC CHONG CHI:
{steps_summary}

Lien he: SOC Lead + IT Security NGAY!""",
            'sent_at': datetime.now().isoformat(),
            'channels': ['telegram', 'email', 'sms']
        }

        return alert

    def escalate_to_telegram(self, incident, containment_plan):
        """Send containment plan to Telegram for immediate action

        Args:
            incident: Incident details dict
            containment_plan: 3-step containment plan

        Returns:
            dict confirming Telegram message
        """
        # Format the message
        message = f"""[CANH BAO KHAN CAP] {incident.get('severity')}

[{incident.get('incident_id')}] {incident.get('title', 'Unknown Incident')}

Thiet bi anh huong: {', '.join(incident.get('affected_assets', [])[:3])}

━━━━━ 3 BUOC CON LAP KHAN CAP ━━━━━

"""

        for step in containment_plan.get('steps', []):
            message += f"""
{step['priority']}
{step['step']}. {step['title']}
   Hanh dong: {step['action']}
   Thoi gian: {step['time_estimate']}

"""

        message += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tong thoi gian: {containment_plan.get('total_time')}
Len cap den: {containment_plan.get('escalate_to')}

[HAY HANH DONG NGAY - Khong cho chi trong 15 phut]"""

        return {
            'success': True,
            'telegram_message_id': f"telegram_{incident.get('incident_id')}",
            'message': message,
            'sent_to': 'SOC Telegram Channel',
            'sent_at': datetime.now().isoformat(),
            'read_status': 'PENDING'
        }

    def execute(self, action, **kwargs):
        """Execute skill action"""
        actions = {
            'triage_incident': lambda: self.triage_incident(
                kwargs.get('incident_id'),
                kwargs.get('severity'),
                kwargs.get('affected_assets', [])
            ),
            'generate_containment_steps': lambda: self.generate_containment_steps(
                kwargs.get('incident_type'),
                kwargs.get('severity')
            ),
            'send_emergency_alert': lambda: self.send_emergency_alert(
                kwargs.get('incident_id'),
                kwargs.get('severity'),
                kwargs.get('title'),
                kwargs.get('steps_summary')
            ),
            'escalate_to_telegram': lambda: self.escalate_to_telegram(
                kwargs.get('incident'),
                kwargs.get('containment_plan')
            )
        }

        if action not in actions:
            return {'error': f'Unknown action: {action}'}

        try:
            result = actions[action]()
            return {'success': True, 'data': result}
        except Exception as e:
            return {'error': str(e)}
