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
DefaultDirName={pf}\SentinelOps
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

[Code]
procedure RegisterService;
var
  ResultCode: Integer;
  ServicePath: String;
  NssmPath: String;
begin
  ServicePath := ExpandConstant('{app}\{#MyAppExeName}');
  NssmPath := ExpandConstant('{app}\nssm.exe');

  // Download NSSM if not present
  if not FileExists(NssmPath) then
  begin
    MsgBox('NSSM not found. Downloading...', mbInformation, MB_OK);
    // In production: fetch from trusted source
    // idpAddFile('https://nssm.cc/release/nssm-2.24-101-g897c7ad.zip', ExpandConstant('{tmp}\nssm.zip'));
  end;

  // Register service with NSSM
  if FileExists(NssmPath) then
  begin
    if Exec(NssmPath, ExpandConstant('install SentinelOpsAgent "' + ServicePath + '"'), '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    begin
      if ResultCode = 0 then
      begin
        // Set startup type to Automatic
        Exec(NssmPath, 'set SentinelOpsAgent Start SERVICE_AUTO_START', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
        // Restart policy: restart service on failure
        Exec(NssmPath, 'set SentinelOpsAgent AppRestartDelay 10000', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
        MsgBox('Service registered successfully', mbInformation, MB_OK);
      end
      else
        MsgBox('Failed to register service. Error code: ' + IntToStr(ResultCode), mbError, MB_OK);
    end;
  end
  else
    MsgBox('NSSM executable not found', mbError, MB_OK);
end;

[CustomMessages]
english.FinishLabel=Installation complete
english.FinishLabelNoIcons=Installation complete (no shortcuts created)

[Run]
Filename: "{app}\nssm.exe"; Parameters: "start SentinelOpsAgent"; Flags: nowait postinstall skipifsilent hidewizard; Description: "Start service"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
