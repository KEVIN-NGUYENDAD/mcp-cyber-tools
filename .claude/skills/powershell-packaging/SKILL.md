# PowerShell Packaging & Windows Service Deployment

Automates secure PowerShell scripting patterns, standalone binary packaging, and Windows Service registration using industry-standard tools.

## Safe PowerShell Patterns

- **Environment Variable Parameter Isolation** (`MCP_ARG_*` prefix): Parameters never interpolated into script source before encoding
- **Avoid Template Literals**: Never use `${variable}` inside PowerShell script bodies
- **Pattern**: `runPowerShell(\`cmd -Param $param\`, { param: String(value) })`

## Packaging Workflow

1. **PyInstaller / pkg**: Convert Node.js agent to standalone executable (`< 35MB`)
2. **Inno Setup**: Create installer with registry entries, file placement, NSSM service registration
3. **NSSM Integration**: Auto-register service to run on boot with restart capability

## Key Security Points

- All parameters pass via environment variables, not command-line strings
- Service runs with minimal required privileges (LOCAL SERVICE by default)
- Installer validates signatures before execution
- Logs all deployment actions to Windows Event Log

## Deployment Verification

```powershell
Get-Service SentinelOpsAgent -ErrorAction SilentlyContinue
```

Should return: Status = Running, StartType = Automatic
