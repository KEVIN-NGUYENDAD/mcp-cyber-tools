"""Real Windows Firewall Snapshot Collector (Firewall Disabled trigger).

Queries Windows Firewall via Get-NetFirewallProfile (the built-in
per-profile enabled state) and returns an entity map keyed by profile
name (Domain/Private/Public) -- ready for
baseline_store.save_snapshot("firewall_status", ...). A profile's
"enabled" flipping True->False is a field_toggled Change Detector
event: "Firewall Disabled".
"""
import json
import subprocess

PS_SCRIPT = r"""
Get-NetFirewallProfile -ErrorAction SilentlyContinue |
Select-Object Name, Enabled |
ConvertTo-Json -Depth 3 -Compress
"""


def collect_firewall_status() -> dict:
    """Return an entity map {profile_name: {"enabled": bool}} for the
    firewall_status baseline source."""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", PS_SCRIPT],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"PowerShell query failed:\n{result.stderr}")

    raw = result.stdout.strip()
    if not raw:
        raise SystemExit("No output from Get-NetFirewallProfile.")

    data = json.loads(raw)
    if isinstance(data, dict):
        data = [data]

    profiles = {}
    for item in data:
        name = item.get("Name") or "unknown"
        # Get-NetFirewallProfile's Enabled comes back as an int (1/0) over
        # ConvertTo-Json, not a JSON bool -- normalize so field_toggled
        # (which requires bool on both sides) fires correctly.
        profiles[name] = {"enabled": bool(item.get("Enabled"))}
    return profiles


if __name__ == "__main__":
    print(json.dumps(collect_firewall_status()))
