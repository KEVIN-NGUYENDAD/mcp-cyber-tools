# MCP Connection Verification Checklist

**Date**: 2026-09-06  
**Purpose**: Verify AppData copy retirement is safe

## ✅ Pre-Retirement Status

| Item | Status | Path |
|------|--------|------|
| MCP Config | ✅ Verified | `%APPDATA%\Claude\claude_desktop_config.json` |
| Config Target | ✅ PRIMARY | `C:\Users\tamng\Projects\mcp-cyber-tools` |
| Primary Server | ✅ Starts | Successfully loaded 90+ tools |
| AppData Copy | ✅ Marked | `DEPRECATED.txt` created |

## 🔄 Restart Process

### Step 1: Close Claude Desktop
```
File → Exit (complete shutdown, not minimize)
Wait 5 seconds
```

### Step 2: Start Claude Desktop
```
Launch Claude Desktop
Wait 10 seconds for full startup
```

### Step 3: Verify MCP Connection
**In Claude Desktop:**
```
1. Open Settings → Developer
2. Find "cyber-tools" server
3. Should show: ✅ CONNECTED (green indicator)
4. If yellow/red: restart Claude or check logs
```

**In Claude Code Terminal:**
```bash
claude mcp list
# Should show: cyber-tools ✅ Connected
```

**Test MCP Tools:**
```bash
# Any cyber-tools function should work:
# mcp__cyber-tools__get_asset_status
# mcp__cyber-tools__get_security_score
```

## 📋 24-Hour Observation Period

### Day 1 (2026-09-06): Active Monitoring
- [ ] MCP shows CONNECTED
- [ ] No error messages in Claude logs
- [ ] Tools execute without errors
- [ ] Telegram bot still uses correct state files

### Day 2 (2026-09-07): Archive Phase
```powershell
# Rename to backup
Rename-Item `
  "C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools" `
  "C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools-backup"
```

### Day 3 (2026-09-08): Final Deletion
```powershell
# Only if still connected and no errors:
Remove-Item `
  "C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools-backup" `
  -Recurse -Force
```

## 🚨 Rollback Procedure

**If anything breaks:**
```powershell
# Restore from backup
Rename-Item `
  "C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools-backup" `
  "C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools"

# Update config if needed
# See: C:\Users\tamng\Projects\mcp-cyber-tools\MCP_CONFIG_FIX.md
```

## ✅ Success Criteria

All of these must remain true:
- [ ] MCP shows CONNECTED in Claude Desktop
- [ ] No "Server disconnected" errors
- [ ] Telegram bot shows 7 CRITICAL, 11 HIGH (correct data)
- [ ] All cyber-tools commands work
- [ ] No performance degradation

## 📝 Notes

- Primary project: `C:\Users\tamng\Projects\mcp-cyber-tools`
- Config file: `%APPDATA%\Claude\claude_desktop_config.json`
- Deprecation marker: `DEPRECATED.txt`
- MCP fix docs: `MCP_CONFIG_FIX.md`

---

**Status**: Ready for restart  
**Next Action**: Restart Claude Desktop and verify connection
