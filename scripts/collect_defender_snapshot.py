"""Real Defender Status Snapshot Collector (Phase F).

Queries Windows Defender via the same Get-MpComputerStatus cmdlet and
field selection modules/defender.js's `defenderStatus` MCP tool already
exposes, and returns them as the flat state dict
baseline_store.save_snapshot("defender_status", ...) expects. No new
data source: this reuses the exact query already proven live in this
repo, just from Python instead of the MCP server's JS side (the same
"shell out via subprocess" pattern create_defender_incident.py already
uses for its own Get-MpThreatDetection query).
"""
import json
import subprocess

# Identical cmdlet + fields to modules/defender.js's defenderStatus tool.
PS_SCRIPT = r"""
Get-MpComputerStatus -ErrorAction SilentlyContinue |
Select-Object AntivirusEnabled, RealTimeProtectionEnabled, BehaviorMonitoringEnabled, IOAVProtectionEnabled, NISEnabled, TamperProtected, InitializationProgress, RebootRequired |
ConvertTo-Json -Depth 5 -Compress
"""


def collect_defender_status() -> dict:
    """Return a flat state dict for the defender_status baseline source."""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", PS_SCRIPT],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"PowerShell query failed:\n{result.stderr}")

    raw = result.stdout.strip()
    if not raw:
        raise SystemExit("No output from Get-MpComputerStatus.")

    return json.loads(raw)


if __name__ == "__main__":
    print(json.dumps(collect_defender_status()))
