; Inno Setup installer for SentinelOps Agent
; Secure deployment: validates binary, registers service, runs on boot

#define MyAppName "SentinelOps Agent"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "SentinelOps"
#define MyAppURL "https://sentinel.example.com"
#define MyAppExeName "sentinel_agent.exe"
#define SourceExe "dist\sentinel_agent.exe"

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
Source: "{#SourceExe}"; DestDir: "{app}"; Flags: ignoreversion
; Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion (optional - not included)
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion


[CustomMessages]
english.FinishLabel=Installation complete
english.FinishLabelNoIcons=Installation complete (no shortcuts created)

[Run]
Filename: "{sys}\cmd.exe"; Parameters: "/c schtasks /create /tn ""SentinelOpsAgent"" /tr ""{app}\{#MyAppExeName}"" /sc onstart /ru SYSTEM /f /rl HIGHEST"; Flags: runhidden postinstall skipifsilent; Description: "Register startup task"

[UninstallRun]
Filename: "{sys}\cmd.exe"; Parameters: "/c schtasks /delete /tn ""SentinelOpsAgent"" /f"; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
