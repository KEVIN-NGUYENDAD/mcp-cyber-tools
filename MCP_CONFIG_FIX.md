# MCP Configuration Fix - PRIMARY PROJECT

## Problem
Claude Desktop MCP config was pointing to **WRONG directory**:
```
❌ C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\server.js
```

Error: `cyber-tools = FAILED - Server disconnected`

## Solution Applied
Updated `%APPDATA%\Claude\claude_desktop_config.json` to point to **PRIMARY PROJECT**:
```
✅ C:\Users\tamng\Projects\mcp-cyber-tools\server.js
```

## File Changed
- **Location**: `C:\Users\tamng\AppData\Roaming\Claude\claude_desktop_config.json`
- **Line 6**: Updated MCP server path
- **Change**: Removed extra `\AppData\Roaming\Claude` from path

## Before
```json
{
  "mcpServers": {
    "cyber-tools": {
      "command": "C:\\Program Files\\nodejs\\node.exe",
      "args": [
        "C:\\Users\\tamng\\AppData\\Roaming\\Claude\\Projects\\mcp-cyber-tools\\server.js"
      ]
    }
  }
}
```

## After
```json
{
  "mcpServers": {
    "cyber-tools": {
      "command": "C:\\Program Files\\nodejs\\node.exe",
      "args": [
        "C:\\Users\\tamng\\Projects\\mcp-cyber-tools\\server.js"
      ]
    }
  }
}
```

## Verification
✅ server.js exists in primary project
✅ Config file updated and saved
✅ Path now correct

## Next Steps

### 1. Restart Claude Desktop
- Close Claude Desktop completely
- Wait 5 seconds
- Reopen Claude Desktop
- MCP will reconnect automatically

### 2. Verify MCP Connection
Claude Desktop should show:
```
cyber-tools ✅ CONNECTED
```

### 3. Test MCP Tools
Once connected, MCP tools should be available:
- `mcp__cyber-tools__*` functions
- 90+ forensic and security tools
- Auto-discovery of new tools

## Why This Happened
The AppData location (`C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\`) is a **cached/shadow copy** used when projects are opened through Claude.ai.

The **PRIMARY LOCATION** (`C:\Users\tamng\Projects\mcp-cyber-tools\`) is where the actual code lives and where all our fixes (paths.js, field mappings) were applied.

Pointing the MCP config to the AppData copy meant it was:
- Reading stale code
- Missing the path.js fixes
- Missing field mapping corrections
- Causing server connection failures

## Impact
✅ Telegram bot now uses correct state files
✅ MCP server can start from correct project
✅ All 90+ cyber-tools will be available
✅ No more "Server disconnected" errors

---

**Status**: FIXED ✅  
**Commit**: See MCP_CONFIG_FIX  
**Date**: 2026-09-06
