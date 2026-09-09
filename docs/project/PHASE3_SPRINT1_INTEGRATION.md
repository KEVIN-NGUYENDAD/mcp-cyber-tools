# PHASE 3 SPRINT 1: TELEGRAM WIRING & ALERT ENGINE
## Integration Guide

**Date**: 2026-09-09  
**Sprint**: Phase 3 - Sprint 1  
**Status**: IMPLEMENTATION IN PROGRESS  
**Branch**: feature/phase3-sprint1-telegram-wiring

---

## OVERVIEW

Sprint 1 implements the complete alert pipeline: event detection → alert creation → routing → delivery.

**Architecture**:
```
change_detector.py (events)
         ↓
  EventWiring.wire_change_detector_to_telegram()
         ↓
  AlertEngine.create_alert() + route_alert()
         ↓
  ┌──────────┬──────────┬──────────────┬─────────┐
  ↓          ↓          ↓              ↓         ↓
telegram_  github_    daily_brief/   alert_    [event_
queue.json queue.json [date].json    archive.  routing_
                                     json      log.json]
  ↓
process_alerts.py (5-min runner)
  ↓
Telegram Bot API → Alerts to SOC
```

---

## MODULES CREATED

### 1. utils/storage.py (328 lines)
Atomic JSON read/write with file locking and transactions.

**Key Classes**:
- `AtomicStorage`: Main class with methods:
  - `read_json(filename, default)` - Safe read with default fallback
  - `write_json(filename, data, create_backup)` - Atomic write with backup
  - `append_to_list(filename, item)` - Append to JSON array
  - `update_field(filename, field_path, value)` - Update nested field (dot notation)
  - `read_and_modify(filename, modifier_func)` - Atomic read-modify-write
  - `get_field(filename, field_path, default)` - Get nested field

**Features**:
- File locking (Unix fcntl + Windows fallback)
- Lock timeout: 30 seconds (configurable)
- Atomic writes via temp file → rename
- Backup creation before overwrite
- Concurrent access safe
- Cross-platform (Windows + Linux)

**Usage**:
```python
from utils import get_storage

storage = get_storage()

# Read
data = storage.read_json('alerts.json', default=[])

# Write atomically
success, error = storage.write_json('config.json', {'key': 'value'})

# Append to list
success, error = storage.append_to_list('alerts.json', {'id': 1})

# Update nested field
success, error = storage.update_field('config.json', 'telegram.enabled', True)

# Atomic increment counter
def increment(data):
    data['count'] = data.get('count', 0) + 1
    return data

success, result, error = storage.read_and_modify('counter.json', increment)
```

---

### 2. utils/alerts.py (344 lines)
Alert engine that routes change_detector events to appropriate channels.

**Key Classes**:
- `Severity` (Enum): CRITICAL (4), HIGH (3), MEDIUM (2), LOW (1)
- `AlertChannel` (Enum): TELEGRAM, GITHUB, DAILY_BRIEF, ARCHIVE
- `AlertEngine`: Route events to channels based on severity

**Alert Flow**:
```
event (from change_detector)
  ↓
determine_severity(source, change_type)
  ↓
create_alert(event) → alert object
  ↓
route_alert(alert) → channels
  ↓
_route_telegram(alert) → queue for async send
_route_github(alert) → github_queue
_route_daily_brief(alert) → daily_brief/[date].json
_route_archive(alert) → alert_archive.json
```

**Severity Routing**:
```python
CRITICAL → [TELEGRAM, GITHUB, DAILY_BRIEF, ARCHIVE]
HIGH     → [GITHUB, DAILY_BRIEF, ARCHIVE]
MEDIUM   → [DAILY_BRIEF, ARCHIVE]
LOW      → [DAILY_BRIEF, ARCHIVE]
```

**Severity Overrides** (source-based):
```python
('defender_threats', 'new_entity')     → CRITICAL  # Malware
('defender_status', 'field_toggled')   → CRITICAL  # Defender off
('device_inventory', 'new_entity')     → HIGH      # Unknown device
('firewall_status', 'field_toggled')   → HIGH      # Firewall change
```

**Usage**:
```python
from utils import get_alert_engine

engine = get_alert_engine()

# Determine severity
severity = engine.determine_severity('defender_threats', 'new_entity')
# → Severity.CRITICAL

# Create alert from event
event = {
    'source': 'defender_threats',
    'change_type': 'new_entity',
    'entity_id': 'trojan.exe',
    'description': 'Malware detected',
}
alert = engine.create_alert(event)

# Route to channels
success, routing_result = engine.route_alert(alert)
# routing_result['channels_routed'] = ['telegram', 'github', ...]
```

---

### 3. utils/telegram_sender.py (340 lines)
Queue-based Telegram message delivery with retry and deduplication.

**Key Classes**:
- `TelegramSender`: Send alerts to Telegram with reliability features

**Features**:
- Queue-based delivery: telegram_queue.json
- Deduplication: ignore duplicate messages within 5min window
- Retry logic: exponential backoff (1min, 5min, 15min)
- Max retries: 3 attempts per message
- Message tracking: telegram_sent.json with hashes
- HTML formatting support
- Loads credentials from .env file

**State Files**:
- `telegram_queue.json`: Pending messages
- `telegram_sent.json`: Sent messages with hashes (for dedup)

**Usage**:
```python
from utils import get_telegram_sender

sender = get_telegram_sender()

# Send single alert (queues for async delivery)
alert = {
    'id': 'alert_001',
    'title': 'Malware detected',
    'description': 'Trojan.exe on Desktop',
    'severity': 'CRITICAL',
    'source': 'defender_threats',
    'entity_id': 'trojan.exe',
}
success, error = sender.send_alert(alert)

# Process queue (called by process_alerts.py)
result = sender.process_queue(batch_size=10)
# result = {
#   'sent': 3,
#   'failed': 1,
#   'deduped': 2,
#   'timestamp': '2026-09-09T10:30:00',
#   'errors': [...]
# }

# Get queue status
status = sender.get_queue_status()
# status['queued_count'] = 5
# status['sent_count'] = 42
```

---

### 4. utils/event_wiring.py (250 lines)
Bridge between change_detector and alert engine.

**Key Classes**:
- `EventWiring`: Process events through alert engine and route

**Features**:
- Process single events or batches
- Routing statistics by severity/source/change_type
- Event routing log for auditing
- Integration point for change_detector.py

**Event Routing Flow**:
```
change_detector event
    ↓
wire_change_detector_to_telegram(event)
    ↓
EventWiring.process_event(event)
    ↓
AlertEngine.create_alert() + route_alert()
    ↓
Routing result + logging
```

**Usage**:
```python
from utils import wire_change_detector_to_telegram, get_event_wiring

# From change_detector.py context:
event = {
    'source': 'device_inventory',
    'change_type': 'new_entity',
    'entity_id': '192.168.1.100',
    'description': 'Unknown device detected',
}

result = wire_change_detector_to_telegram(event)
# result['success'] = True
# result['routing']['channels_routed'] = ['github', 'daily_brief', 'archive']

# Get statistics
wiring = get_event_wiring()
stats = wiring.get_routing_stats()
# stats['by_severity'] = {'CRITICAL': 5, 'HIGH': 12, ...}
# stats['channel_usage'] = {'telegram': 5, 'github': 17, ...}
```

---

### 5. scripts/process_alerts.py (223 lines)
Main entry point for alert queue processing (runs every 5 minutes).

**Usage**:
```bash
# Process all queues (Telegram + GitHub)
python scripts/process_alerts.py

# Process only Telegram queue
python scripts/process_alerts.py --telegram

# Process only GitHub queue
python scripts/process_alerts.py --github

# Show statistics
python scripts/process_alerts.py --stats

# Clean up old data
python scripts/process_alerts.py --cleanup
```

**Logging**:
- `logs/alert_processor.log` - Timestamped log of all processing
- Console output with Unicode → ASCII fallback for Windows

---

## INTEGRATION STEPS

### Step 1: Verify Imports
```bash
python -c "from utils import *; print('[OK] All modules ready')"
```

### Step 2: Wire change_detector.py (NEXT SPRINT)
Currently, change_detector emits events but doesn't route to Telegram.

**Future Integration** (after Phase 3 Sprint 1 merge):
```python
# At end of change_detector.py, after emitting event:

from utils import wire_change_detector_to_telegram

# Convert event to routing
routing_result = wire_change_detector_to_telegram(event)
if routing_result['success']:
    print(f"Event routed to: {routing_result['routing']['channels_routed']}")
```

### Step 3: Schedule process_alerts.py
**Windows Task Scheduler**:
```
Trigger: Every 5 minutes
Action: python C:\Users\tamng\Projects\mcp-cyber-tools\scripts\process_alerts.py
```

**Linux/macOS cron**:
```
*/5 * * * * python /path/to/mcp-cyber-tools/scripts/process_alerts.py
```

### Step 4: Monitor Queues
```bash
# Check pending Telegram messages
python scripts/process_alerts.py --stats

# Check logs
tail -f logs/alert_processor.log
```

---

## STATE FILES CREATED

| File | Format | Purpose | Size |
|------|--------|---------|------|
| `telegram_queue.json` | Array | Pending Telegram messages | Dynamic |
| `telegram_sent.json` | Array | Sent messages (1000 recent) | ~50KB |
| `github_queue.json` | Array | Pending GitHub issues | Dynamic |
| `alert_archive.json` | Array | All alerts (10000 recent) | ~500KB |
| `event_routing_log.json` | Array | Audit trail (1000 recent) | ~100KB |
| `daily_brief/[YYYY-MM-DD].json` | Object | Daily changes | ~50KB |

---

## WORKFLOW EXAMPLE

### Scenario: Malware Detected
```
1. Windows Defender detects malware (trojan.exe)

2. change_detector.py runs (every 15 min via Task Scheduler)
   - Compares current vs previous Defender threats
   - Detects new_entity: "trojan.exe"
   - Emits event:
     {
       "source": "defender_threats",
       "change_type": "new_entity",
       "entity_id": "trojan.exe",
       "description": "Malware detected by Windows Defender",
       ...
     }

3. EventWiring.process_event(event)
   - Determines severity: CRITICAL (override for defender_threats+new_entity)

4. AlertEngine.create_alert(event)
   - Creates alert object:
     {
       "id": "alert_20260909_103042_001",
       "severity": "CRITICAL",
       "title": "[NEW] defender_threats: trojan.exe",
       "channels": ["telegram", "github", "daily_brief", "archive"],
       ...
     }

5. AlertEngine.route_alert(alert)
   - Routes CRITICAL to all 4 channels:
     ✓ TELEGRAM: queues in telegram_queue.json
     ✓ GITHUB: queues in github_queue.json
     ✓ DAILY_BRIEF: added to daily_brief/2026-09-09.json
     ✓ ARCHIVE: added to alert_archive.json

6. process_alerts.py runs (every 5 min via Task Scheduler)
   - Reads telegram_queue.json
   - Checks for duplicates (hashing)
   - Sends via Telegram API:
     🚨 SentinelOps Alert [CRITICAL]
     Title: [NEW] defender_threats: trojan.exe
     Description: Malware detected by Windows Defender
     ...

7. Message sent successfully
   - Tracked in telegram_sent.json
   - Removed from telegram_queue.json
   - Logged to alert_processor.log
```

---

## TESTING CHECKLIST

- [x] Atomic storage module imports
- [x] Alert engine imports
- [x] Telegram sender imports
- [x] Event wiring imports
- [x] Process alerts script runs
- [ ] Alert processor sends test message to Telegram (requires .env setup)
- [ ] Deduplication prevents duplicates
- [ ] Retry logic retries failed messages
- [ ] Stats command shows accurate counts
- [ ] Daily brief receives alerts

---

## PHASE 3 SPRINT 2 (NEXT)

After merging Sprint 1:

1. **Wire change_detector.py**: Integrate EventWiring into change_detector
2. **GitHub issue creation**: Implement full create_issue() for GitHub queue
3. **Daily brief scheduler**: Wire daily brief generation to 8 PM automation
4. **Monitoring API**: Expose queue status via REST endpoints
5. **Performance testing**: Stress test with 1000+ alerts/hour

---

## ROLLBACK PLAN

If issues arise, revert to develop branch:
```bash
git checkout develop
git pull origin develop
```

All new code is in `utils/` and `scripts/process_alerts.py`.
Existing code (change_detector.py, etc.) unchanged until Sprint 2.

---

**Sprint 1 Status**: ✅ INFRASTRUCTURE COMPLETE  
**Ready for**: change_detector integration (Sprint 2)  
**Deployment**: After PR review and merge to develop

