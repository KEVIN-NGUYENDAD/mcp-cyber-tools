#!/usr/bin/env python3
"""Recommended Actions Generator (Phase N.5)"""
import json, sys
from datetime import datetime
from pathlib import Path

class ActionGenerator:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / "state"
        self.actions = []
    
    def load_state(self, filename):
        fp = self.state_dir / filename
        if fp.exists():
            try:
                with open(fp, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def generate_asset_actions(self):
        assets = self.load_state("assets.json")
        if not assets:
            return
        critical_assets = [a for a in assets.get("assets", []) if a.get("critical", 0) > 0 or a.get("high", 0) > 0]
        if critical_assets:
            critical_assets.sort(key=lambda x: x.get("critical", 0), reverse=True)
            top = critical_assets[0]
            action = {
                "priority": "CRITICAL",
                "category": "Patch Management",
                "title": f"Remediate {top.get('ip')} ({top.get('device_type')})",
                "description": f"{top.get('critical', 0)} critical, {top.get('high', 0)} high vulnerabilities",
                "steps": ["1. Identify patches", "2. Test in staging", "3. Schedule window", "4. Apply patches", "5. Verify remediation"],
                "time_estimate": "4-8 hours",
                "impact": "Prevents system compromise"
            }
            self.actions.append(action)
    
    def generate_crypto_actions(self):
        crypto = self.load_state("crypto_inventory.json")
        if not crypto:
            return
        sb = crypto.get("severity_breakdown", {})
        if sb.get("CRITICAL", 0) > 0:
            self.actions.append({
                "priority": "CRITICAL",
                "category": "Cryptography",
                "title": "Fix broken cryptographic implementations",
                "description": f"{sb.get('CRITICAL')} critical crypto issues",
                "steps": ["1. Audit TLS/SSL", "2. Disable weak ciphers", "3. Enforce TLS 1.2+", "4. Implement pinning", "5. Review key management"],
                "time_estimate": "8-16 hours",
                "impact": "Restores encryption security"
            })
    
    def generate_waap_actions(self):
        waap = self.load_state("waap_score.json")
        if not waap:
            return
        if waap.get("status") in ["poor", "fair"]:
            self.actions.append({
                "priority": "HIGH",
                "category": "Web Application Security",
                "title": "Enhance WAAP protection rules",
                "description": f"WAAP posture: {waap.get('status')}",
                "steps": ["1. Review rules", "2. Identify patterns", "3. Enable protection", "4. Test traffic", "5. Rate limiting"],
                "time_estimate": "2-4 hours",
                "impact": "Blocks web attacks"
            })
    
    def generate(self):
        self.generate_asset_actions()
        self.generate_crypto_actions()
        self.generate_waap_actions()
        
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
        self.actions.sort(key=lambda x: priority_order.get(x.get("priority"), 99))
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "question": "What do I need to do right now?",
            "total_actions": len(self.actions),
            "by_priority": {
                "CRITICAL": len([a for a in self.actions if a.get("priority") == "CRITICAL"]),
                "HIGH": len([a for a in self.actions if a.get("priority") == "HIGH"])
            },
            "recommended_actions": self.actions
        }
        
        with open(self.state_dir / "recommended_actions.json", "w") as f:
            json.dump(output, f, indent=2)
        
        return {"status": "success", "total_actions": len(self.actions)}

if __name__ == "__main__":
    gen = ActionGenerator()
    result = gen.generate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") == "success" else 1)
