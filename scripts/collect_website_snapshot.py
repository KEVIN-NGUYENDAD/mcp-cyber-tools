"""Real Website Snapshot Collector (Website Sensor).

Checks a website's HTTP status, HTTPS status, SSL certificate validity
and expiry, and response time -- stdlib only (urllib, ssl, socket) --
and returns them as the flat state dict
baseline_store.save_snapshot("website_status", ...) expects. No new
dependencies, no new infrastructure.
"""
import json
import socket
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

DEFAULT_TIMEOUT = 10
DEFAULT_HOST = "sentinelops.fyi"
USER_AGENT = "SentinelOps-WebsiteSensor/1.0"


def _http_status(url: str):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, socket.timeout, OSError):
        return None


def _https_status_and_timing(host: str):
    url = f"https://{host}/"
    start = time.monotonic()
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            status = resp.status
    except urllib.error.HTTPError as e:
        status = e.code
    except (urllib.error.URLError, socket.timeout, OSError):
        return None, None
    elapsed_ms = round((time.monotonic() - start) * 1000, 1)
    return status, elapsed_ms


def _ssl_info(host: str, port: int = 443):
    """Return (ssl_valid, ssl_expiry ISO string or None, days_until_expiry or None)."""
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=DEFAULT_TIMEOUT) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
    except (ssl.SSLError, socket.timeout, OSError, ConnectionError):
        return False, None, None

    not_after = cert.get("notAfter") if cert else None
    if not not_after:
        return True, None, None
    expires_at = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    days_until_expiry = (expires_at - datetime.now(timezone.utc)).days
    return True, expires_at.isoformat(), days_until_expiry


def collect_website_status(host: str = DEFAULT_HOST) -> dict:
    """Return a flat state dict for the website_status baseline source."""
    http_status = _http_status(f"http://{host}/")
    https_status, response_time_ms = _https_status_and_timing(host)
    ssl_valid, ssl_expiry, ssl_days_until_expiry = _ssl_info(host)

    return {
        "http_status": http_status,
        "https_status": https_status,
        # Boolean up/down signal, same pattern as defender_status's other
        # booleans -- lets Change Detector fire field_toggled (not just a
        # noisy status-code value_changed) when the site actually goes down.
        "site_up": https_status is not None,
        "ssl_valid": ssl_valid,
        "ssl_expiry": ssl_expiry,
        "ssl_days_until_expiry": ssl_days_until_expiry,
        "response_time_ms": response_time_ms,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Website Snapshot Collector.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    args = parser.parse_args()
    print(json.dumps(collect_website_status(args.host)))
