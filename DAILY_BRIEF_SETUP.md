# SentinelOps Daily Brief - Automated Delivery Setup

**Status**: Ready for deployment ✅

Automated Daily Brief generation and delivery via Telegram and Email at **3:00 PM every day**.

---

## 📋 Files

| File | Purpose |
|------|---------|
| `scripts/run_daily_brief.py` | Main orchestrator - generates brief and calls delivery methods |
| `scripts/send_daily_brief_telegram.py` | Sends brief via Telegram Bot API |
| `scripts/send_daily_brief_email.py` | Sends brief via SMTP (localhost or configured server) |
| `scripts/schedule-daily-brief.ps1` | PowerShell script to create Windows Task Scheduler task |
| `scripts/setup-daily-brief-task.bat` | Batch wrapper for PowerShell script (run as Administrator) |
| `daily_brief/YYYY-MM-DD.json` | Daily brief output (auto-generated) |

---

## 🚀 Setup Instructions

### Option 1: Batch File (Recommended - Easiest)

1. Open Command Prompt **as Administrator**
2. Run:
```cmd
cd C:\GitHub\mcp-cyber-tools\scripts
setup-daily-brief-task.bat
```

3. Verify:
```cmd
schtasks /query /tn SentinelOps-DailyBrief /v
```

### Option 2: PowerShell Script

1. Open PowerShell **as Administrator**
2. Run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
C:\GitHub\mcp-cyber-tools\scripts\schedule-daily-brief.ps1
```

3. Verify:
```powershell
Get-ScheduledTask -TaskName "SentinelOps-DailyBrief" | Select *
```

### Option 3: Manual schtasks Command

1. Open Command Prompt **as Administrator**
2. Run:
```cmd
schtasks /create /tn "SentinelOps-DailyBrief" /tr "python C:\GitHub\mcp-cyber-tools\scripts\run_daily_brief.py" /sc daily /st 15:00 /f
```

3. Verify:
```cmd
schtasks /query /tn SentinelOps-DailyBrief
```

---

## 📊 Daily Brief Workflow

```
3:00 PM (Daily)
    ↓
run_daily_brief.py
    ↓
    ├─ generate_daily_brief()
    │  └─ Build JSON from Daily Brief Store
    ├─ Save to daily_brief/2026-09-DD.json
    ├─ Send via Telegram ✅ (Primary - always works)
    ├─ Send via Email (Requires SMTP server)
    └─ Log all events
```

---

## ✅ Delivery Methods

### Telegram (VERIFIED WORKING ✅)

- **Credentials**: TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID from `.env`
- **Status**: ✅ Operational and tested
- **Message Format**: HTML-formatted, emoji indicators for risk levels
- **Logging**: Message ID captured and logged

Example output:
```
📊 SENTINELOPS DAILY BRIEF
2026-09-12

Security Score:
  N/A

Today's Changes:
  No changes detected today.

Current Risk:
  🟢 LOW

Recommended Actions:
  No recommendations at this time.
```

### Email (SMTP - Ready)

- **Method**: Python `smtplib` module
- **Default SMTP Server**: `localhost:25`
- **Recipient**: `security-team@localhost` (configurable)
- **Format**: HTML email with styled sections
- **Status**: Framework ready (SMTP server configuration needed)

To enable SMTP:
1. Configure local SMTP server or
2. Modify `send_daily_brief_email.py` to use external SMTP:
   ```python
   return send_via_smtp(
       to_email, 
       subject, 
       html_body,
       smtp_server="smtp.gmail.com",  # Change this
       smtp_port=587                   # Change this
   )
   ```

---

## 🔍 Testing

### Manual Run (Test)
```bash
cd C:\GitHub\mcp-cyber-tools\scripts
python run_daily_brief.py
```

Expected output:
```
[BRIEF] Daily Brief run starting at 2026-09-12T23:24:05.368767+00:00
[BRIEF] Generated daily brief
SentinelOps Daily Brief -- 2026-09-12
...
[BRIEF] Saved to C:\GitHub\mcp-cyber-tools\daily_brief\2026-09-12.json
[BRIEF] Sending via Telegram...
[BRIEF] Telegram sent successfully (message_id: 436)
[BRIEF] Telegram delivery successful
[BRIEF] Sending via Email...
[BRIEF] Email delivery successful (or failed if no SMTP)
[BRIEF] Daily Brief run finished at ...
```

### Task Scheduler Run (Manual Trigger)

After creating task:
```cmd
schtasks /run /tn "SentinelOps-DailyBrief"
```

Check results:
```cmd
schtasks /query /tn "SentinelOps-DailyBrief" /v
```

---

## 📝 Logging

All runs log to console with `[BRIEF]` and `[ERROR]` prefixes:

| Tag | Meaning |
|-----|---------|
| `[BRIEF]` | Normal operation step |
| `[ERROR]` | Failure or issue |

Example:
```
[BRIEF] Daily Brief run starting at ...
[BRIEF] Generated daily brief
[BRIEF] Saved to C:\GitHub\mcp-cyber-tools\daily_brief\2026-09-12.json
[BRIEF] Sending via Telegram...
[BRIEF] Telegram sent successfully (message_id: 436)
[BRIEF] Telegram delivery successful
[BRIEF] Daily Brief run finished at ...
```

---

## 🔑 Configuration

### Prerequisites

1. **Python 3.7+** installed and in PATH
2. **Telegram Bot Token** in `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```
3. **SMTP Server** (for email delivery)

### Environment Variables

Read from: `C:\GitHub\mcp-cyber-tools\.env`

```ini
TELEGRAM_BOT_TOKEN=8779048449:AAE1rtDcQZxcH66KlnVsZJk-HfnxtMvB3gs
TELEGRAM_CHAT_ID=8814186709
```

---

## 🚨 Troubleshooting

### Task doesn't run

1. **Check if task exists**:
   ```cmd
   schtasks /query /tn "SentinelOps-DailyBrief"
   ```

2. **Check task history**:
   ```cmd
   wevtutil qe Microsoft-Windows-TaskScheduler/Operational /f:text
   ```

3. **Manual test**:
   ```cmd
   python C:\GitHub\mcp-cyber-tools\scripts\run_daily_brief.py
   ```

### Telegram not sending

1. Verify credentials in `.env`:
   ```bash
   cat C:\GitHub\mcp-cyber-tools\.env | findstr TELEGRAM
   ```

2. Test Telegram connectivity:
   ```bash
   python -c "from send_daily_brief_telegram import *; print(load_credentials())"
   ```

### Email not sending

1. Verify SMTP server is reachable:
   ```powershell
   Test-NetConnection -ComputerName localhost -Port 25
   ```

2. Configure alternative SMTP in `send_daily_brief_email.py`

---

## 📊 Verification Checklist

- [ ] Python 3.7+ installed
- [ ] `.env` contains TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
- [ ] `python run_daily_brief.py` runs without errors
- [ ] Telegram message received successfully
- [ ] Task created in Windows Task Scheduler
- [ ] Task scheduled for 3:00 PM daily
- [ ] Email delivery tested (if SMTP configured)

---

## 🔄 Daily Workflow

After setup is complete:

1. **3:00 PM every day** - Task Scheduler runs `run_daily_brief.py`
2. **Script execution**:
   - Generates brief from Daily Brief Store
   - Saves JSON to `daily_brief/YYYY-MM-DD.json`
   - Sends Telegram message
   - Sends Email (if SMTP available)
   - Logs all steps
3. **User receives** - Daily Brief appears in Telegram (and email if configured)
4. **Next day** - Process repeats

---

**Status**: ✅ PRODUCTION READY  
**Last Updated**: 2026-09-12  
**Version**: 1.0.0
