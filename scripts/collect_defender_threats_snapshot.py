"""Real Defender Threats Snapshot Collector (Malware Detected trigger).

Queries Windows Defender via the same Get-MpThreatDetection /
Get-MpThreat join create_defender_incident.py already uses (ThreatID ->
ThreatName), but over *all* current detections instead of just the
latest one, and returns them as an entity map keyed by DetectionID --
ready for baseline_store.save_snapshot("defender_threats", ...). A new
detection appearing is a new_entity Change Detector event: "Malware
Detected".
"""
import json
import subprocess

# Same join create_defender_incident.py's PS_SCRIPT performs, applied to
# every current detection rather than just the most recent.
PS_SCRIPT = r"""
$dets = Get-MpThreatDetection -ErrorAction SilentlyContinue
$threats = Get-MpThreat -ErrorAction SilentlyContinue
$joined = foreach ($d in $dets) {
    $t = $threats | Where-Object { $_.ThreatID -eq $d.ThreatID } | Select-Object -First 1
    [PSCustomObject]@{
        DetectionID   = $d.DetectionID
        ThreatID      = $d.ThreatID
        ThreatName    = $t.ThreatName
        ProcessName   = $d.ProcessName
        Resources     = ($d.Resources -join '; ')
        DetectionTime = if ($d.InitialDetectionTime) { $d.InitialDetectionTime.ToString('o') } else { $null }
        ActionSuccess = $d.ActionSuccess
    }
}
if ($joined) { $joined | ConvertTo-Json -Depth 5 -Compress } else { '[]' }
"""


def collect_defender_threats() -> dict:
    """Return an entity map {detection_id: {...}} for the
    defender_threats baseline source."""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", PS_SCRIPT],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"PowerShell query failed:\n{result.stderr}")

    raw = result.stdout.strip()
    if not raw:
        return {}

    data = json.loads(raw)
    if isinstance(data, dict):
        data = [data]  # PowerShell collapses a single-item array to an object

    threats = {}
    for i, item in enumerate(data):
        key = item.get("DetectionID") or f"unknown-detection-{i}"
        threats[key] = {
            "threat_id": item.get("ThreatID"),
            "threat_name": item.get("ThreatName") or "unknown_threat",
            "process_name": item.get("ProcessName"),
            "resources": item.get("Resources"),
            "detection_time": item.get("DetectionTime"),
            "action_success": item.get("ActionSuccess"),
        }
    return threats


if __name__ == "__main__":
    print(json.dumps(collect_defender_threats()))
