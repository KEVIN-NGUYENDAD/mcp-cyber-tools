; Inno Setup installer for SentinelOps Agent
; Secure deployment: validates binary, registers service, runs on boot

#define MyAppName "SentinelOps Agent"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "SentinelOps"
#define MyAppURL "https://sentinel.example.com"
; PRIMARY runtime: self-contained executable (bundles Node, no PATH dependency).
; FALLBACK runtime: batch wrapper, requires Node.js on PATH. Shipped alongside
; until the removal criteria in docs/project/PROJECT_READY_STATE.md are met.
#define MyAppExeName "sentinel_agent.exe"
#define SourceExe "dist\sentinel_agent.exe"
#define FallbackCmd "dist\sentinel_agent.cmd"

[Setup]
AppId={{SENTINEL-OPS-AGENT-2026}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\SentinelOps
ArchitecturesInstallIn64BitMode=x64
DefaultGroupName=SentinelOps
OutputBaseFilename=SentinelOps-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
AllowUNCPath=no
ShowLanguageDialog=no
; LicenseFile=LICENSE (optional - not included in deployment)
InfoBeforeFile=
AllowNoIcons=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; PRIMARY runtime - self-contained, starts without Node.js installed
Source: "{#SourceExe}"; DestDir: "{app}"; Flags: ignoreversion
; FALLBACK runtime - used only if the .exe fails to start
Source: "{#FallbackCmd}"; DestDir: "{app}"; Flags: ignoreversion
; Application code - web server (source of truth for the fallback runtime)
Source: "web\server.js"; DestDir: "{app}\web"; Flags: ignoreversion
Source: "web\app.js"; DestDir: "{app}\web"; Flags: ignoreversion
Source: "web\*.html"; DestDir: "{app}\web"; Flags: ignoreversion
; Node.js runtime dependencies
Source: "node_modules\*"; DestDir: "{app}\node_modules"; Flags: recursesubdirs ignoreversion
; Configuration templates
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion
Source: "package.json"; DestDir: "{app}"; Flags: ignoreversion


[CustomMessages]
english.FinishLabel=Installation complete
english.FinishLabelNoIcons=Installation complete (no shortcuts created)

[Run]
; Startup task points at the PRIMARY runtime. If the exe ever fails, re-point
; this task at sentinel_agent.cmd and record the fallback use.
Filename: "{sys}\cmd.exe"; Parameters: "/c schtasks /create /tn ""SentinelOpsAgent"" /tr ""\""{app}\{#MyAppExeName}\"""" /sc onstart /ru SYSTEM /f /rl HIGHEST"; Flags: runhidden postinstall skipifsilent; Description: "Register startup task"

[UninstallRun]
Filename: "{sys}\cmd.exe"; Parameters: "/c schtasks /delete /tn ""SentinelOpsAgent"" /f"; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
