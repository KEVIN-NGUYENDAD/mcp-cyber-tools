#!/usr/bin/env python3
"""
TRIAGE ENGINE - Priority Queue Generator (Phase N.8)
Xác định TOP 5 vấn đề quan trọng nhất cần xử lý hôm nay
Populates: state/priority_queue.json

Nguồn dữ liệu:
- Recommended Actions (priority + severity)
- Risk Score (overall risk level + components)
- Assets (vulnerability counts)
- Timeline (recent incidents)
- MCP Status (Defender, Firewall, Health)
"""

import json
import sys
from datetime import datetime
from pathlib import Path

class TriageEngine:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.priority_queue = []
        self.priority_file = self.state_dir / 'priority_queue.json'

    def load_state(self, filename):
        fp = self.state_dir / filename
        return json.load(open(fp)) if fp.exists() else {}

    def analyze_actions(self):
        """Phân tích recommended actions"""
        actions = self.load_state('recommended_actions.json')
        items = []

        for action in actions.get('recommended_actions', []):
            severity_score = {'CRITICAL': 100, 'HIGH': 75, 'MEDIUM': 50}.get(
                action.get('priority'), 25
            )

            items.append({
                'source': 'action',
                'priority_score': severity_score,
                'title': action.get('title', 'Unknown'),
                'category': action.get('category', 'General'),
                'priority': action.get('priority'),
                'description': action.get('description', ''),
                'steps': action.get('steps', []),
                'time_estimate': action.get('time_estimate', 'N/A'),
                'impact': action.get('impact', ''),
                'reason': 'Recommended Action',
                'affected_assets': self.extract_assets_from_action(action)
            })

        return items

    def extract_assets_from_action(self, action):
        """Trích xuất asset liên quan từ action"""
        assets = []
        title = action.get('title', '').lower()

        if '192.168' in title:
            # Extract IP
            parts = title.split()
            for i, part in enumerate(parts):
                if part.startswith('192.168'):
                    assets.append(part.rstrip('()'))

        return assets

    def analyze_risk_factors(self):
        """Phân tích risk factors"""
        risk = self.load_state('risk_score.json')
        items = []

        risk_level = risk.get('risk_level', 'UNKNOWN')
        overall_score = risk.get('overall_score', 0)

        components = risk.get('component_scores', {})

        # Score thấp nhất → vấn đề lớn nhất
        low_components = sorted(
            components.items(),
            key=lambda x: x[1]
        )[:3]  # Top 3 lowest scoring

        for component, score in low_components:
            items.append({
                'source': 'risk',
                'priority_score': 100 - score,
                'title': f'Cải thiện {component.replace("_", " ").title()}',
                'category': 'Risk Management',
                'priority': 'HIGH' if score < 50 else 'MEDIUM',
                'description': f'{component} score chỉ {score}/100',
                'impact': f'Ảnh hưởng đến Risk Score: {overall_score}',
                'reason': f'{component} component weak',
                'affected_assets': [],
                'steps': ['Phân tích chi tiết', 'Lập kế hoạch cải thiện']
            })

        return items

    def analyze_vulnerable_assets(self):
        """Phân tích assets dễ bị tấn công"""
        assets = self.load_state('assets.json')
        items = []

        for asset in assets.get('assets', [])[:3]:  # Top 3 vulnerable
            critical = asset.get('critical', 0)
            high = asset.get('high', 0)
            total_vulns = asset.get('vulnerability_count', 0)

            if total_vulns > 0:
                items.append({
                    'source': 'asset',
                    'priority_score': critical * 20 + high * 10,
                    'title': f"Patch {asset.get('ip')} ({asset.get('device_type')})",
                    'category': 'Patch Management',
                    'priority': 'CRITICAL' if critical > 0 else 'HIGH',
                    'description': f'{critical} critical, {high} high vulnerabilities',
                    'impact': f'Device có {total_vulns} vulnerability',
                    'reason': 'High vulnerability count',
                    'affected_assets': [asset.get('ip')],
                    'time_estimate': '4-8 hours',
                    'steps': ['Identify patches', 'Test in staging', 'Apply patches']
                })

        return items

    def analyze_security_status(self):
        """Phân tích trạng thái bảo mật"""
        items = []

        # Defender check
        defender = self.load_state('defender_status.json')
        if not defender.get('enabled'):
            items.append({
                'source': 'mcp',
                'priority_score': 95,
                'title': 'Bật Microsoft Defender',
                'category': 'Security',
                'priority': 'CRITICAL',
                'description': 'Defender bị tắt - hệ thống không có bảo vệ chủ động',
                'impact': 'Tăng nguy cơ nhiễm malware',
                'reason': 'Defender disabled',
                'affected_assets': [],
                'time_estimate': '5 minutes',
                'steps': ['Open Windows Security', 'Enable real-time protection']
            })

        # Firewall check
        firewall = self.load_state('firewall_status.json')
        if not firewall.get('enabled'):
            items.append({
                'source': 'mcp',
                'priority_score': 95,
                'title': 'Bật Windows Firewall',
                'category': 'Network Security',
                'priority': 'CRITICAL',
                'description': 'Firewall bị tắt - hệ thống không có bảo vệ mạng',
                'impact': 'Tăng nguy cơ kết nối trái phép',
                'reason': 'Firewall disabled',
                'affected_assets': [],
                'time_estimate': '5 minutes',
                'steps': ['Open Windows Security', 'Enable firewall']
            })

        # System health check
        health = self.load_state('system_health.json')
        if health.get('disk_usage', 0) > 90:
            items.append({
                'source': 'mcp',
                'priority_score': 70,
                'title': f"Dọn dẹp đĩa ({health.get('disk_usage')}%)",
                'category': 'System Maintenance',
                'priority': 'HIGH',
                'description': 'Dung lượng đĩa gần đầy - ảnh hưởng hiệu năng',
                'impact': 'Có thể gây sự cố hệ thống',
                'reason': 'Disk usage critical',
                'affected_assets': [],
                'time_estimate': '30 minutes',
                'steps': ['Run Disk Cleanup', 'Remove old files', 'Empty Recycle Bin']
            })

        return items

    def analyze_incidents(self):
        """Phân tích timeline incidents"""
        timeline = self.load_state('timeline.json')
        items = []

        for event in timeline.get('events', [])[:3]:  # Top 3 recent
            if event.get('severity') in ['CRITICAL', 'HIGH']:
                items.append({
                    'source': 'timeline',
                    'priority_score': 90 if event.get('severity') == 'CRITICAL' else 75,
                    'title': f"Xử lý: {event.get('type')}",
                    'category': event.get('category', 'Incident'),
                    'priority': event.get('severity'),
                    'description': event.get('description', ''),
                    'impact': 'Recent incident detected',
                    'reason': event.get('type'),
                    'affected_assets': event.get('details', {}).get('ip', []) if isinstance(event.get('details', {}), dict) else [],
                    'time_estimate': '1-2 hours',
                    'steps': ['Investigate', 'Isolate if needed', 'Resolve']
                })

        return items

    def generate(self):
        """Tạo priority queue TOP 5"""
        # Collect all items
        all_items = []
        all_items.extend(self.analyze_actions())
        all_items.extend(self.analyze_risk_factors())
        all_items.extend(self.analyze_vulnerable_assets())
        all_items.extend(self.analyze_security_status())
        all_items.extend(self.analyze_incidents())

        # Sort by priority_score (cao nhất trước)
        all_items.sort(key=lambda x: x['priority_score'], reverse=True)

        # Take top 5
        top_5 = all_items[:5]

        # Assign priority 1-5
        for idx, item in enumerate(top_5):
            item['priority_rank'] = idx + 1

        output = {
            'timestamp': datetime.now().isoformat(),
            'question': 'Cái gì quan trọng nhất hôm nay?',
            'total_items_analyzed': len(all_items),
            'top_5_critical': top_5,
            'summary': {
                'critical_count': sum(1 for item in top_5 if item.get('priority') == 'CRITICAL'),
                'high_count': sum(1 for item in top_5 if item.get('priority') == 'HIGH'),
                'sources': {}
            }
        }

        # Count by source
        for item in top_5:
            source = item.get('source', 'unknown')
            output['summary']['sources'][source] = output['summary']['sources'].get(source, 0) + 1

        with open(self.priority_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return {
            'status': 'success',
            'total_analyzed': len(all_items),
            'top_5_generated': len(top_5),
            'critical_items': output['summary']['critical_count']
        }

if __name__ == '__main__':
    engine = TriageEngine()
    result = engine.generate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)
