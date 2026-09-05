#!/usr/bin/env python3
"""
PHASE V: VNETWORK API DISCOVERY
Enumerate all accessible VNETWORK API endpoints and resources
Document capabilities without modifying existing collectors
Outputs: docs/VNETWORK_API_MAP.md
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    import requests
    from dotenv import load_dotenv
except ImportError as e:
    print(f'{{"error": "Missing dependencies. Install: pip install requests python-dotenv"}}', file=sys.stderr)
    sys.exit(1)


class VNETWORKDiscovery:
    """Discovers VNETWORK API endpoints and capabilities"""

    def __init__(self):
        self.docs_dir = Path(__file__).parent.parent / 'docs'
        self.docs_dir.mkdir(exist_ok=True)
        self.api_map_file = self.docs_dir / 'VNETWORK_API_MAP.md'

        self.base_url = None
        self.api_token = None
        self.session = requests.Session()
        self.endpoints = []
        self.resources = {}

        self.load_credentials()

    def load_credentials(self):
        """Load credentials from .env"""
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)

        self.api_token = os.environ.get('VNETWORK_API_TOKEN')
        self.base_url = os.environ.get('VNETWORK_BASE_URL', 'https://openapi.vnetwork.vn')

    def test_connectivity(self) -> Tuple[bool, str]:
        """Test basic API connectivity"""
        try:
            headers = {'Authorization': f'Bearer {self.api_token}'}
            resp = requests.head(self.base_url, headers=headers, timeout=5, verify=False)
            return True, f"Connected (HTTP {resp.status_code})"
        except requests.exceptions.ConnectionError:
            return False, "Connection refused - API may be offline"
        except requests.exceptions.Timeout:
            return False, "Connection timeout"
        except Exception as e:
            return False, str(e)

    def discover_endpoints(self) -> List[Dict]:
        """Attempt to discover API endpoints"""
        discovered = []

        # Common WAP/CDN/WAF endpoint patterns
        common_paths = [
            # Root and info endpoints
            ('GET', '/'),
            ('GET', '/api'),
            ('GET', '/api/v1'),
            ('GET', '/api/v2'),
            ('GET', '/health'),
            ('GET', '/status'),
            ('GET', '/info'),

            # Authentication endpoints
            ('POST', '/auth/login'),
            ('POST', '/auth/token'),
            ('GET', '/auth/verify'),

            # Domain/Asset endpoints
            ('GET', '/domains'),
            ('GET', '/assets'),
            ('GET', '/properties'),
            ('GET', '/sites'),
            ('POST', '/domains'),

            # SSL/Certificate endpoints
            ('GET', '/ssl'),
            ('GET', '/ssl/certificates'),
            ('GET', '/certificates'),
            ('POST', '/ssl/certificates'),

            # WAF endpoints
            ('GET', '/waf'),
            ('GET', '/waf/rules'),
            ('GET', '/waf/policies'),
            ('GET', '/waf/status'),
            ('POST', '/waf/rules'),

            # CDN endpoints
            ('GET', '/cdn'),
            ('GET', '/cdn/config'),
            ('GET', '/cdn/cache'),
            ('GET', '/cdn/rules'),

            # DNS endpoints
            ('GET', '/dns'),
            ('GET', '/dns/records'),
            ('GET', '/dns/zones'),
            ('POST', '/dns/records'),

            # Security/Monitoring endpoints
            ('GET', '/security'),
            ('GET', '/security/threats'),
            ('GET', '/security/alerts'),
            ('GET', '/monitoring'),
            ('GET', '/logs'),
            ('GET', '/events'),

            # Reporting endpoints
            ('GET', '/reports'),
            ('GET', '/analytics'),
            ('GET', '/metrics'),

            # User/Account endpoints
            ('GET', '/account'),
            ('GET', '/users'),
            ('GET', '/permissions'),

            # Settings/Config endpoints
            ('GET', '/settings'),
            ('GET', '/config'),
            ('GET', '/preferences'),
        ]

        headers = {'Authorization': f'Bearer {self.api_token}'}

        for method, path in common_paths:
            try:
                url = f"{self.base_url}{path}"

                if method == 'GET':
                    resp = requests.get(url, headers=headers, timeout=3, verify=False)
                else:
                    resp = requests.post(url, headers=headers, timeout=3, verify=False, json={})

                # Record all responses (success and failures give us info)
                discovered.append({
                    'method': method,
                    'path': path,
                    'status': resp.status_code,
                    'content_type': resp.headers.get('content-type', 'unknown'),
                    'sample_response': self._safe_response(resp),
                    'is_accessible': resp.status_code < 500
                })

            except requests.exceptions.Timeout:
                discovered.append({
                    'method': method,
                    'path': path,
                    'status': None,
                    'error': 'timeout',
                    'is_accessible': False
                })
            except Exception as e:
                discovered.append({
                    'method': method,
                    'path': path,
                    'status': None,
                    'error': str(type(e).__name__),
                    'is_accessible': False
                })

        self.endpoints = discovered
        return discovered

    def _safe_response(self, resp) -> Optional[str]:
        """Safely extract sample response"""
        try:
            if resp.status_code < 400:
                # Only capture successful responses
                if resp.headers.get('content-type', '').startswith('application/json'):
                    data = resp.json()
                    # Truncate large responses
                    resp_str = json.dumps(data)
                    return resp_str[:500] if len(resp_str) > 500 else resp_str
                else:
                    text = resp.text[:200] if resp.text else None
                    return text
        except:
            pass
        return None

    def analyze_resources(self):
        """Analyze discovered endpoints to identify resource types"""
        resources = {
            'domains': [],
            'ssl_certificates': [],
            'waf': [],
            'cdn': [],
            'dns': [],
            'security': [],
            'monitoring': [],
            'account': [],
            'unknown': []
        }

        for endpoint in self.endpoints:
            if endpoint['status'] and endpoint['status'] < 400:
                path = endpoint['path'].lower()

                if 'domain' in path or 'asset' in path or 'site' in path or 'property' in path:
                    resources['domains'].append(endpoint)
                elif 'ssl' in path or 'cert' in path:
                    resources['ssl_certificates'].append(endpoint)
                elif 'waf' in path:
                    resources['waf'].append(endpoint)
                elif 'cdn' in path:
                    resources['cdn'].append(endpoint)
                elif 'dns' in path:
                    resources['dns'].append(endpoint)
                elif 'security' in path or 'threat' in path or 'alert' in path:
                    resources['security'].append(endpoint)
                elif 'monitoring' in path or 'log' in path or 'event' in path or 'metric' in path or 'analytics' in path:
                    resources['monitoring'].append(endpoint)
                elif 'account' in path or 'user' in path or 'permission' in path or 'setting' in path:
                    resources['account'].append(endpoint)
                else:
                    resources['unknown'].append(endpoint)

        self.resources = resources
        return resources

    def generate_api_map(self) -> str:
        """Generate comprehensive API map documentation"""
        doc = []
        doc.append("# VNETWORK API DISCOVERY MAP")
        doc.append("")
        doc.append(f"**Discovery Date**: {datetime.now().isoformat()}")
        doc.append(f"**Status**: Phase V Discovery")
        doc.append(f"**Base URL**: {self.base_url}")
        doc.append(f"**Authentication**: Bearer Token (API Token)")
        doc.append("")
        doc.append("---")
        doc.append("")

        # Connectivity status
        connected, conn_msg = self.test_connectivity()
        doc.append("## Connectivity Status")
        doc.append("")
        status_icon = "OK" if connected else "FAILED"
        doc.append(f"- **Status**: {status_icon}")
        doc.append(f"- **Message**: {conn_msg}")
        doc.append("")

        # Summary
        accessible = len([e for e in self.endpoints if e.get('is_accessible')])
        total = len(self.endpoints)
        doc.append("## Discovery Summary")
        doc.append("")
        doc.append(f"- **Total Endpoints Tested**: {total}")
        doc.append(f"- **Accessible Endpoints**: {accessible}")
        doc.append(f"- **Success Rate**: {accessible}/{total} ({int(accessible/total*100)}%)")
        doc.append("")

        # Resource types found
        doc.append("## Identified Resource Types")
        doc.append("")
        for resource_type, endpoints in self.resources.items():
            if endpoints:
                doc.append(f"### {resource_type.replace('_', ' ').title()}")
                doc.append("")
                doc.append(f"**Endpoints Found**: {len(endpoints)}")
                doc.append("")
                for ep in endpoints:
                    doc.append(f"- `{ep['method']} {ep['path']}` (Status: {ep.get('status', 'N/A')})")
                doc.append("")

        # Detailed endpoint documentation
        doc.append("---")
        doc.append("")
        doc.append("## Detailed Endpoint Documentation")
        doc.append("")

        accessible_endpoints = [e for e in self.endpoints if e.get('is_accessible')]

        for ep in sorted(accessible_endpoints, key=lambda x: (x['path'], x['method'])):
            doc.append(f"### `{ep['method']} {ep['path']}`")
            doc.append("")
            doc.append(f"**Status Code**: {ep.get('status', 'N/A')}")
            doc.append(f"**Content-Type**: {ep.get('content_type', 'N/A')}")

            if ep.get('sample_response'):
                doc.append("")
                doc.append("**Sample Response**:")
                doc.append("")
                doc.append("```json")
                doc.append(ep['sample_response'])
                doc.append("```")

            # Value to SentinelOps
            value = self._assess_value(ep)
            doc.append("")
            doc.append(f"**Value to SentinelOps**: {value}")
            doc.append("")

        # Recommendations
        doc.append("---")
        doc.append("")
        doc.append("## Integration Recommendation")
        doc.append("")

        if accessible == 0:
            doc.append("### RECOMMENDATION: DEFER")
            doc.append("")
            doc.append("**Reason**: No accessible endpoints discovered.")
            doc.append("")
            doc.append("**Action**: ")
            doc.append("1. Verify VNETWORK API token is valid")
            doc.append("2. Verify VNETWORK_BASE_URL is correct (currently: `%s`)" % self.base_url)
            doc.append("3. Verify API is online and accessible from network")
            doc.append("4. Retry discovery once API connectivity confirmed")
            doc.append("")
        else:
            waf_endpoints = self.resources.get('waf', [])
            ssl_endpoints = self.resources.get('ssl_certificates', [])
            cdn_endpoints = self.resources.get('cdn', [])

            if waf_endpoints or ssl_endpoints or cdn_endpoints:
                doc.append("### RECOMMENDATION: INTEGRATE NOW (Phase 2)")
                doc.append("")
                doc.append("**Reason**: Multiple valuable resources discoverable from VNETWORK API.")
                doc.append("")
                doc.append("**Available Resources**:")
                if waf_endpoints:
                    doc.append(f"- **WAF Protection**: {len(waf_endpoints)} endpoint(s) available")
                if ssl_endpoints:
                    doc.append(f"- **SSL Certificates**: {len(ssl_endpoints)} endpoint(s) available")
                if cdn_endpoints:
                    doc.append(f"- **CDN Configuration**: {len(cdn_endpoints)} endpoint(s) available")
                doc.append("")
                doc.append("**Next Steps**:")
                doc.append("1. Update `scripts/collect_waap_snapshot.py` to query VNETWORK endpoints")
                doc.append("2. Add WAF status polling (currently reports 'unknown')")
                doc.append("3. Add CDN status detection (currently reports 'unknown')")
                doc.append("4. Validate new data in state/waap_status.json")
                doc.append("5. Update WAAP health score to include WAF/CDN factors")
                doc.append("")
            else:
                doc.append("### RECOMMENDATION: DEFER")
                doc.append("")
                doc.append("**Reason**: Limited relevant resources discovered for WAAP monitoring.")
                doc.append("")
                doc.append("**Action**: ")
                doc.append("1. Review VNETWORK API documentation")
                doc.append("2. Confirm endpoint paths are correct")
                doc.append("3. Identify actual resource paths for your account")
                doc.append("4. Update discovery with correct paths")
                doc.append("")

        doc.append("---")
        doc.append("")
        doc.append("## Raw Endpoint Data")
        doc.append("")
        doc.append("```json")
        doc.append(json.dumps(self.endpoints, indent=2))
        doc.append("```")

        return "\n".join(doc)

    def _assess_value(self, endpoint: Dict) -> str:
        """Assess the value of an endpoint to SentinelOps"""
        path = endpoint['path'].lower()

        if 'waf' in path:
            return "**HIGH** - WAF status and rule configuration critical for WAAP scoring"
        elif 'cdn' in path:
            return "**HIGH** - CDN configuration and cache rules essential for CDN detection"
        elif 'ssl' in path or 'cert' in path:
            return "**MEDIUM** - SSL certificate data overlaps with existing WAAP collector"
        elif 'dns' in path:
            return "**MEDIUM** - DNS data overlaps with existing Domain collector"
        elif 'domain' in path or 'asset' in path or 'site' in path:
            return "**MEDIUM** - Domain inventory for multi-domain monitoring"
        elif 'security' in path or 'threat' in path or 'alert' in path:
            return "**HIGH** - Security threats and alerts valuable for incident detection"
        elif 'monitoring' in path or 'log' in path or 'event' in path or 'metric' in path:
            return "**MEDIUM-HIGH** - Monitoring and event data useful for baseline tracking"
        elif 'account' in path or 'user' in path:
            return "**LOW** - Account/user information less critical for WAAP health"
        else:
            return "**UNKNOWN** - Requires manual review"

    def save_api_map(self, content: str) -> bool:
        """Save API map to docs directory"""
        try:
            with open(self.api_map_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving API map: {e}", file=sys.stderr)
            return False

    def discover(self) -> Dict:
        """Execute full discovery"""
        print(f"Starting VNETWORK API Discovery...")
        print(f"Base URL: {self.base_url}")
        print()

        # Test connectivity
        connected, msg = self.test_connectivity()
        print(f"[*] Connectivity: {msg}")

        if not connected:
            print("[!] API not accessible, proceeding with endpoint discovery...")

        # Discover endpoints
        print(f"[*] Discovering endpoints...")
        self.discover_endpoints()
        print(f"[+] Discovered {len(self.endpoints)} endpoints")

        # Analyze resources
        print(f"[*] Analyzing resources...")
        self.analyze_resources()

        # Count accessible
        accessible = len([e for e in self.endpoints if e.get('is_accessible')])
        print(f"[+] Found {accessible} accessible endpoints")

        # Generate documentation
        print(f"[*] Generating API map documentation...")
        api_map_content = self.generate_api_map()

        # Save
        print(f"[*] Saving to {self.api_map_file}...")
        if self.save_api_map(api_map_content):
            print(f"[+] API map saved successfully")
        else:
            print(f"[!] Failed to save API map")

        return {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'connected': connected,
            'total_endpoints_tested': len(self.endpoints),
            'accessible_endpoints': accessible,
            'resources': {k: len(v) for k, v in self.resources.items()},
            'api_map_file': str(self.api_map_file),
            'recommendation': self._generate_recommendation()
        }

    def _generate_recommendation(self) -> str:
        """Generate final recommendation"""
        accessible = len([e for e in self.endpoints if e.get('is_accessible')])
        waf_count = len(self.resources.get('waf', []))
        ssl_count = len(self.resources.get('ssl_certificates', []))
        cdn_count = len(self.resources.get('cdn', []))

        if accessible == 0:
            return "DEFER - No accessible endpoints"
        elif (waf_count > 0 or cdn_count > 0) and accessible >= 5:
            return "INTEGRATE NOW (Phase 2)"
        else:
            return "DEFER - Limited relevant resources"


def main():
    discovery = VNETWORKDiscovery()
    result = discovery.discover()

    print()
    print("=" * 60)
    print("DISCOVERY RESULTS")
    print("=" * 60)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
