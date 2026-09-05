"""Real Device Inventory Snapshot Collector (Phase F).

Parses `arp -a` -- the same network-discovery capability
modules/network.js's `arp` tool already exposes (as raw, unparsed
text) -- into an entity map keyed by IP address, ready for
baseline_store.save_snapshot("device_inventory", ...). No new data
source: this only adds the structured parsing that tool never had.
"""
import json
import re
import subprocess

# Multicast/broadcast entries aren't real devices on the network.
_IGNORE_MAC = {"ff-ff-ff-ff-ff-ff", "00-00-00-00-00-00"}

_ENTRY_RE = re.compile(
    r"^\s*(\d{1,3}(?:\.\d{1,3}){3})\s+([0-9a-fA-F]{2}(?:-[0-9a-fA-F]{2}){5})\s+(\w+)\s*$"
)


def collect_device_inventory() -> dict:
    """Return an entity map {ip: {mac, type}} for the device_inventory
    baseline source, parsed from `arp -a`."""
    result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"arp -a failed:\n{result.stderr}")

    devices = {}
    for line in result.stdout.splitlines():
        match = _ENTRY_RE.match(line)
        if not match:
            continue
        ip, mac, entry_type = match.groups()
        mac = mac.lower()
        if ip.startswith("224.") or ip.startswith("239.") or ip == "255.255.255.255" or mac in _IGNORE_MAC:
            continue
        devices[ip] = {"mac": mac, "type": entry_type.lower()}
    return devices


if __name__ == "__main__":
    print(json.dumps(collect_device_inventory()))
