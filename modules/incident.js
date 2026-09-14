import { z } from "zod";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { generateJsonReport, generateHtmlReport, generateAuditReport } from "./reportGenerator.js";
import { runPowerShell, formatResponse } from "./shared.js";

const MODULE_DIR = path.dirname(fileURLToPath(import.meta.url));
const STATE_DIR = path.join(MODULE_DIR, "..", "state");

// Mot tool chi tra ve duong dan la mot tool khong tra ve gi. Nguoi goi nhan
// duoc mot chuoi, khong biet no da quan sat thay bao nhieu, khong biet co gi
// dang doc, va khong the phan biet "da thu thap, khong co gi" voi "khong thu
// thap duoc". Trong bang kiem dinh chung deu roi vao o EMPTY vinh vien.
//
// Hop dong moi: bang chung THAT di ra cung luc voi duong dan file.
function evidenceResponse(payload, report) {
  return formatResponse(true, JSON.stringify({
    ...payload,
    reportPath: report ? report.path : null
  }, null, 2));
}

// Doc mot file state do pipeline sinh ra. KHONG tinh lai bat cu thu gi o day:
// repo nay da ba lan tra gia cho viec co hai noi cung tra loi mot cau hoi.
// Khong doc duoc thi noi thang la khong doc duoc, chu khong tra ve mot gia tri
// mac dinh trong nhu binh thuong.
function readStateFile(name) {
  const file = path.join(STATE_DIR, name);
  try {
    return { readable: true, data: JSON.parse(fs.readFileSync(file, "utf8")) };
  } catch (error) {
    return { readable: false, error: `${name}: ${error.message}`, data: null };
  }
}

function hoursSince(isoString) {
  if (!isoString) return null;
  const then = new Date(isoString).getTime();
  if (Number.isNaN(then)) return null;
  return (Date.now() - then) / 3600000;
}

export function registerIncidentTools(server) {
  // 1. COLLECTEVIDENCE
  server.tool(
    "collectEvidence",
    "Collect forensic evidence for incident (returns summary, record count and report path)",
    {
      incidentId: z.string()
    },
    async ({ incidentId }) => {
      const result = runPowerShell(`
        $ErrorActionPreference = 'SilentlyContinue'
        $os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
        $procs = @(Get-Process -ErrorAction SilentlyContinue)
        $conns = @(Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue)
        $svcs  = @(Get-Service -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Running' })
        $admins = @(Get-LocalGroupMember -Group 'Administrators' -ErrorAction SilentlyContinue)
        [PSCustomObject]@{
          Hostname      = [string]$env:COMPUTERNAME
          User          = [string]$env:USERNAME
          OS            = [string]$os.Caption
          BootTime      = [string]$os.LastBootUpTime
          CollectedAt   = (Get-Date).ToString('o')
          ProcessCount  = $procs.Count
          ConnectionCount = $conns.Count
          RunningServiceCount = $svcs.Count
          LocalAdminCount = $admins.Count
          TopProcesses  = @($procs | Sort-Object WorkingSet -Descending | Select-Object -First 10 |
                             ForEach-Object { [PSCustomObject]@{ Name = $_.Name; Id = $_.Id; WorkingSetMB = [math]::Round($_.WorkingSet / 1MB, 1) } })
          RemoteEndpoints = @($conns | Where-Object { $_.RemoteAddress -notin @('127.0.0.1','::1','0.0.0.0') } |
                              Select-Object -First 20 |
                              ForEach-Object { [PSCustomObject]@{ Remote = "$($_.RemoteAddress):$($_.RemotePort)"; Pid = $_.OwningProcess } })
        } | ConvertTo-Json -Depth 5 -Compress
        exit 0
      `);

      if (!result.success) return formatResponse(false, "", result.error);

      let evidence = null;
      try {
        evidence = JSON.parse(result.data);
      } catch (error) {
        return formatResponse(false, "", `Khong phan tich duoc ket qua thu thap: ${error.message}`);
      }

      const report = generateJsonReport(`Incident ${incidentId} Evidence`, evidence, "incident");

      // recordCount dem so QUAN SAT, khong dem so truong. Mot bo bang chung co
      // 0 quan sat va mot bo khong thu thap duoc phai doc khac nhau.
      const recordCount = (evidence.TopProcesses || []).length
        + (evidence.RemoteEndpoints || []).length;

      return evidenceResponse({
        incidentId,
        summary: `${evidence.Hostname}: ${evidence.ProcessCount} tien trinh, `
          + `${evidence.ConnectionCount} ket noi, ${evidence.RunningServiceCount} dich vu dang chay, `
          + `${evidence.LocalAdminCount} quan tri vien cuc bo`,
        recordCount,
        collectedAt: evidence.CollectedAt,
        host: {
          hostname: evidence.Hostname,
          user: evidence.User,
          os: evidence.OS,
          bootTime: evidence.BootTime
        },
        counts: {
          processes: evidence.ProcessCount,
          connections: evidence.ConnectionCount,
          runningServices: evidence.RunningServiceCount,
          localAdmins: evidence.LocalAdminCount
        },
        topProcesses: evidence.TopProcesses || [],
        remoteEndpoints: evidence.RemoteEndpoints || []
      }, report);
    }
  );

  // 2. COLLECTPROCESSES
  server.tool(
    "collectProcesses",
    "Collect all running processes snapshot",
    {},
    async () => {
      const result = runPowerShell(`Get-Process | Select-Object Name, Id, Path, StartTime, WorkingSet, CPU | ConvertTo-Json -Depth 5`);
      if (result.success) {
        const report = generateJsonReport("Process Collection", result.data, "incident");
        return formatResponse(true, `Processes collected and saved to: ${report.path}`);
      }
      return formatResponse(false, "", result.error);
    }
  );

  // 3. COLLECTSERVICES
  server.tool(
    "collectServices",
    "Collect all services snapshot",
    {},
    async () => {
      const result = runPowerShell(`Get-Service | Select-Object Name, DisplayName, Status, StartType | ConvertTo-Json -Depth 5`);
      if (result.success) {
        const report = generateJsonReport("Services Collection", result.data, "incident");
        return formatResponse(true, `Services collected and saved to: ${report.path}`);
      }
      return formatResponse(false, "", result.error);
    }
  );

  // 4. COLLECTNETWORKSTATE
  server.tool(
    "collectNetworkState",
    "Collect network connections snapshot",
    {},
    async () => {
      const result = runPowerShell(`Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess | ConvertTo-Json -Depth 5`);
      if (result.success) {
        const report = generateJsonReport("Network State Collection", result.data, "incident");
        return formatResponse(true, `Network state collected and saved to: ${report.path}`);
      }
      return formatResponse(false, "", result.error);
    }
  );

  // 5. COLLECTSTARTUPITEMS
  server.tool(
    "collectStartupItems",
    "Collect startup items and persistence mechanisms",
    {},
    async () => {
      const result = runPowerShell(`@{ StartupPrograms = (Get-CimInstance Win32_StartupCommand).Count; ScheduledTasks = (Get-ScheduledTask | Where-Object { $_.State -ne 'Disabled' }).Count; RunKeys = (Get-ItemProperty 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -ErrorAction SilentlyContinue).PSObject.Properties.Count; } | ConvertTo-Json -Depth 5`);
      if (result.success) {
        const report = generateJsonReport("Startup Items Collection", result.data, "incident");
        return formatResponse(true, `Startup items collected and saved to: ${report.path}`);
      }
      return formatResponse(false, "", result.error);
    }
  );

  // 6. COLLECTFIREWALL
  server.tool(
    "collectFirewall",
    "Collect firewall configuration",
    {},
    async () => {
      const result = runPowerShell(`Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction | ConvertTo-Json -Depth 5`);
      if (result.success) {
        const report = generateJsonReport("Firewall Collection", result.data, "incident");
        return formatResponse(true, `Firewall config collected and saved to: ${report.path}`);
      }
      return formatResponse(false, "", result.error);
    }
  );

  // 7. COLLECTDEFENDER
  server.tool(
    "collectDefender",
    "Collect Windows Defender status and threats",
    {},
    async () => {
      const result = runPowerShell(`@{ DefenderStatus = (Get-MpComputerStatus).AntivirusEnabled; LastScanTime = (Get-MpComputerStatus).LastFullScanTime; Threats = (Get-MpThreat).Count; } | ConvertTo-Json -Depth 5`);
      if (result.success) {
        const report = generateJsonReport("Defender Collection", result.data, "incident");
        return formatResponse(true, `Defender info collected and saved to: ${report.path}`);
      }
      return formatResponse(false, "", result.error);
    }
  );

  // 8. COLLECTLOGS
  server.tool(
    "collectLogs",
    "Collect relevant event logs (returns log count, source count and file path)",
    {
      logName: z.enum(["Security", "System", "Application"]).optional(),
      count: z.coerce.number().optional()
    },
    async ({ logName = "Security", count = 1000 }) => {
      const result = runPowerShell(`
        $ErrorActionPreference = 'SilentlyContinue'
        $rows = @(Get-WinEvent -LogName '${logName}' -MaxEvents ${count} -ErrorAction SilentlyContinue |
          ForEach-Object {
            # Thong diep su kien thi thoang chua ky tu dieu khien tho (0x00-0x1F
            # ngoai tab/CR/LF). ConvertTo-Json nha chung ra nguyen ven, va
            # JSON.parse ben Node chet voi "Bad control character in string
            # literal" — mot tool dang chay tot bong bao FAIL, tuy vao viec trong
            # 1000 su kien vua lay co dinh mot cai hay khong.
            $msg = [string]$_.Message
            if ($msg) { $msg = [regex]::Replace($msg, '[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F]', ' ') }
            [PSCustomObject]@{
              TimeCreated = $_.TimeCreated
              Id          = $_.Id
              Level       = [string]$_.LevelDisplayName
              Provider    = [string]$_.ProviderName
              Message     = $msg
            }
          })
        # Trang thai cau hinh cua log di kem bang chung. Thieu no thi "0 ban ghi"
        # cua mot log DANG TAT doc y het "0 ban ghi" cua mot log rong that.
        $info = Get-WinEvent -ListLog '${logName}' -ErrorAction SilentlyContinue
        [PSCustomObject]@{
          LogEnabled  = [bool]$info.IsEnabled
          LogRecords  = [string]$info.RecordCount
          Collected   = $rows.Count
          Events      = $rows
        } | ConvertTo-Json -Depth 5 -Compress
        exit 0
      `);

      if (!result.success) return formatResponse(false, "", result.error);

      let payload = null;
      try {
        payload = JSON.parse(result.data);
      } catch (error) {
        return formatResponse(false, "", `Khong phan tich duoc log: ${error.message}`);
      }

      const events = payload.Events || [];
      const byProvider = {};
      const byLevel = {};
      for (const event of events) {
        const provider = event.Provider || "(khong ro)";
        const level = event.Level || "(khong ro)";
        byProvider[provider] = (byProvider[provider] || 0) + 1;
        byLevel[level] = (byLevel[level] || 0) + 1;
      }

      const report = generateJsonReport(`${logName} Logs Collection`, payload, "incident");

      const oldest = events.length ? events[events.length - 1].TimeCreated : null;
      const newest = events.length ? events[0].TimeCreated : null;

      return evidenceResponse({
        logName,
        logCount: events.length,
        sourceCount: Object.keys(byProvider).length,
        logEnabled: payload.LogEnabled,
        totalRecordsInLog: payload.LogRecords,
        // Rong voi mot log DANG TAT khong phai bang chung vang mat: chua tung
        // co ai ghi vao day. Noi ro ngay trong cau tom tat.
        summary: events.length
          ? `${events.length} su kien tu ${Object.keys(byProvider).length} nguon trong log ${logName}`
          : (payload.LogEnabled
            ? `Log ${logName} doc duoc va khong co su kien nao khop`
            : `Log ${logName} DANG TAT — khong co ban ghi vi chua ai ghi vao, khong phai vi khong co gi xay ra`),
        timeRange: { oldest, newest },
        byProvider,
        byLevel
      }, report);
    }
  );

  // 9. TIMELINE
  server.tool(
    "timeline",
    "Generate incident timeline (returns the actual ordered events, not just counts)",
    {
      days: z.coerce.number().optional(),
      limit: z.coerce.number().optional()
    },
    async ({ days = 7, limit = 300 }) => {
      // Ba con so dem khong phai mot timeline. Mot timeline la cac su kien da
      // xay ra, xep theo thoi gian, du chi tiet de doc duoc chuyen gi. "12 su
      // kien dang nhap" khong tra loi duoc cau hoi duy nhat ma timeline ton tai
      // de tra loi: dieu gi da xay ra, luc may gio, va truoc/sau cai gi.
      //
      // Duyet thu muc gioi han o Desktop/Downloads/Documents voi -Depth 2:
      // ban cu de quy toan bo profile, va cai do khong the ve dich trong 30s.
      const result = runPowerShell(`
        $ErrorActionPreference = 'SilentlyContinue'
        $start = (Get-Date).AddDays(-${days})
        $events = New-Object System.Collections.ArrayList

        function Add-Row($time, $source, $type, $detail) {
          if ($null -eq $time) { return }
          # Cung ly do nhu collectLogs: ky tu dieu khien tho trong noi dung su
          # kien lam hong JSON o phia Node.
          $clean = [string]$detail
          if ($clean) { $clean = [regex]::Replace($clean, '[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F]', ' ') }
          [void]$events.Add([PSCustomObject]@{
            Time = (Get-Date $time).ToString('o')
            Source = $source
            Type = $type
            Detail = $clean
          })
        }

        Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624,4625,4634,4720,4722,4732; StartTime=$start} -MaxEvents 200 -ErrorAction SilentlyContinue |
          ForEach-Object {
            $label = switch ($_.Id) {
              4624 { 'Dang nhap thanh cong' }
              4625 { 'Dang nhap that bai' }
              4634 { 'Dang xuat' }
              4720 { 'Tao tai khoan' }
              4722 { 'Kich hoat tai khoan' }
              4732 { 'Them vao nhom dac quyen' }
              default { "Su kien $($_.Id)" }
            }
            Add-Row $_.TimeCreated 'Security' $label (([string]$_.Message) -split "\`n")[0]
          }

        Get-WinEvent -FilterHashtable @{LogName='System'; Id=7045,7040; StartTime=$start} -MaxEvents 100 -ErrorAction SilentlyContinue |
          ForEach-Object {
            $label = if ($_.Id -eq 7045) { 'Cai dat dich vu moi' } else { 'Doi kieu khoi dong dich vu' }
            Add-Row $_.TimeCreated 'System' $label (([string]$_.Message) -split "\`n")[0]
          }

        Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-PowerShell/Operational'; Id=4104; StartTime=$start} -MaxEvents 100 -ErrorAction SilentlyContinue |
          ForEach-Object {
            Add-Row $_.TimeCreated 'PowerShell' 'Script block' (([string]$_.Message) -split "\`n")[0]
          }

        foreach ($folder in @('Desktop','Downloads','Documents')) {
          $full = Join-Path $env:USERPROFILE $folder
          if (Test-Path $full) {
            Get-ChildItem -Path $full -File -Recurse -Depth 2 -Force -ErrorAction SilentlyContinue |
              Where-Object { $_.LastWriteTime -gt $start } |
              Sort-Object LastWriteTime -Descending | Select-Object -First 60 |
              ForEach-Object { Add-Row $_.LastWriteTime 'Filesystem' 'File thay doi' $_.FullName }
          }
        }

        Get-ScheduledTask -ErrorAction SilentlyContinue | ForEach-Object {
          $info = $_ | Get-ScheduledTaskInfo -ErrorAction SilentlyContinue
          if ($info -and $info.LastRunTime -and $info.LastRunTime -gt $start) {
            Add-Row $info.LastRunTime 'ScheduledTask' 'Tac vu da chay' ($_.TaskPath + $_.TaskName)
          }
        }

        $sorted = @($events | Sort-Object Time -Descending | Select-Object -First ${limit})
        [PSCustomObject]@{ WindowStart = $start.ToString('o'); Total = $events.Count; Events = $sorted } |
          ConvertTo-Json -Depth 5 -Compress
        exit 0
      `);

      if (!result.success) return formatResponse(false, "", result.error);

      let payload = null;
      try {
        payload = JSON.parse(result.data);
      } catch (error) {
        return formatResponse(false, "", `Khong phan tich duoc timeline: ${error.message}`);
      }

      const events = payload.Events || [];
      const bySource = {};
      for (const event of events) {
        bySource[event.Source] = (bySource[event.Source] || 0) + 1;
      }

      const report = generateJsonReport(`Incident Timeline - Last ${days} days`, payload, "incident");

      return evidenceResponse({
        days,
        windowStart: payload.WindowStart,
        eventCount: events.length,
        totalObserved: payload.Total,
        truncated: payload.Total > events.length,
        summary: events.length
          ? `${events.length} su kien tu ${Object.keys(bySource).length} nguon trong ${days} ngay qua`
          : `Khong co su kien nao trong ${days} ngay qua tren cac nguon da doc duoc`,
        bySource,
        firstEvent: events.length ? events[events.length - 1].Time : null,
        lastEvent: events.length ? events[0].Time : null,
        events
      }, report);
    }
  );

  // 10. SECURITYAUDIT
  server.tool(
    "securityAudit",
    "Run a security audit against live Defender, Firewall, Event Log, Risk Score and Incident data",
    {
      auditType: z.enum(["quick", "full"]).optional()
    },
    async ({ auditType = "full" }) => {
      // Ban cu tra ve mot checklist viet cung trong ma: tam muc, moi muc mot chu
      // "Review" hoac "Check Enabled", khong doc bat cu thu gi tren may. No chay
      // duoc tren mot may da bi chiem hoan toan va van in ra dung tam dong do.
      //
      // Mot tool ten la "audit" khong quan sat gi la thu nguy hiem nhat trong ca
      // kho: no khong im lang, no tra loi — va cau tra loi luon giong nhau.
      //
      // Hai nguyen tac cho ban moi:
      //   1. Moi ket luan phai co gia tri QUAN SAT DUOC di kem.
      //   2. Nguon khong doc duoc -> UNKNOWN, khong bao gio la OK. Mot muc chua
      //      nhin thay ma to xanh chinh la cach mot bang audit noi doi.
      const full = auditType !== "quick";
      const result = runPowerShell(`
        $ErrorActionPreference = 'SilentlyContinue'
        $out = [ordered]@{}

        try {
          $mp = Get-MpComputerStatus -ErrorAction Stop
          $threats = if ($${full}) { @(Get-MpThreat -ErrorAction SilentlyContinue) } else { @() }
          $out.Defender = [PSCustomObject]@{
            Readable = $true
            AntivirusEnabled = [bool]$mp.AntivirusEnabled
            RealTimeProtectionEnabled = [bool]$mp.RealTimeProtectionEnabled
            SignatureAgeDays = [int]$mp.AntivirusSignatureAge
            LastFullScan = [string]$mp.LastFullScanTime
            ThreatCount = $threats.Count
          }
        } catch {
          $out.Defender = [PSCustomObject]@{ Readable = $false; Error = [string]$_.Exception.Message }
        }

        try {
          $profiles = @(Get-NetFirewallProfile -ErrorAction Stop |
            ForEach-Object { [PSCustomObject]@{ Name = [string]$_.Name; Enabled = [bool]$_.Enabled; DefaultInbound = [string]$_.DefaultInboundAction } })
          $out.Firewall = [PSCustomObject]@{
            Readable = $true
            Profiles = $profiles
            EnabledCount = @($profiles | Where-Object { $_.Enabled }).Count
            TotalCount = $profiles.Count
          }
        } catch {
          $out.Firewall = [PSCustomObject]@{ Readable = $false; Error = [string]$_.Exception.Message }
        }

        $logs = @()
        foreach ($name in @('Security','System','Application')) {
          try {
            $info = Get-WinEvent -ListLog $name -ErrorAction Stop
            $readable = $false
            try { [void](Get-WinEvent -LogName $name -MaxEvents 1 -ErrorAction Stop); $readable = $true } catch { $readable = $false }
            $logs += [PSCustomObject]@{
              Name = $name; Exists = $true; Enabled = [bool]$info.IsEnabled
              Records = [string]$info.RecordCount; Readable = $readable
            }
          } catch {
            $logs += [PSCustomObject]@{ Name = $name; Exists = $false; Error = [string]$_.Exception.Message }
          }
        }
        $out.EventLogs = $logs

        $out | ConvertTo-Json -Depth 6 -Compress
        exit 0
      `);

      if (!result.success) return formatResponse(false, "", result.error);

      let live = null;
      try {
        live = JSON.parse(result.data);
      } catch (error) {
        return formatResponse(false, "", `Khong phan tich duoc ket qua audit: ${error.message}`);
      }

      const findings = [];
      const add = (name, status, observed, detail) =>
        findings.push({ category: name, status, observed, detail });

      // --- Defender -------------------------------------------------------
      const defender = live.Defender || {};
      if (!defender.Readable) {
        add("Defender", "UNKNOWN", null,
          `Khong doc duoc trang thai Defender: ${defender.Error || "khong ro"}`);
      } else {
        const on = defender.AntivirusEnabled && defender.RealTimeProtectionEnabled;
        const stale = defender.SignatureAgeDays > 7;
        add("Defender", defender.ThreatCount > 0 ? "ATTENTION" : (on && !stale ? "OK" : "ATTENTION"), {
          antivirusEnabled: defender.AntivirusEnabled,
          realTimeProtection: defender.RealTimeProtectionEnabled,
          signatureAgeDays: defender.SignatureAgeDays,
          lastFullScan: defender.LastFullScan,
          threatCount: defender.ThreatCount
        }, on
          ? (stale ? `Dang bat nhung chu ky da cu ${defender.SignatureAgeDays} ngay`
            : `Dang bat, chu ky moi ${defender.SignatureAgeDays} ngay, ${defender.ThreatCount} moi de doa trong lich su`)
          : "Antivirus hoac bao ve thoi gian thuc dang TAT");
      }

      // --- Firewall -------------------------------------------------------
      const firewall = live.Firewall || {};
      if (!firewall.Readable) {
        add("Firewall", "UNKNOWN", null,
          `Khong doc duoc cau hinh tuong lua: ${firewall.Error || "khong ro"}`);
      } else {
        const { EnabledCount: enabled, TotalCount: total } = firewall;
        add("Firewall",
          enabled === total ? "OK" : (enabled === 0 ? "CRITICAL" : "ATTENTION"),
          { enabledProfiles: enabled, totalProfiles: total, profiles: firewall.Profiles },
          `${enabled}/${total} profile dang bat`);
      }

      // --- Event Logs -----------------------------------------------------
      const logs = live.EventLogs || [];
      const unreadable = logs.filter(l => l.Exists && !l.Readable).map(l => l.Name);
      const disabled = logs.filter(l => l.Exists && !l.Enabled).map(l => l.Name);
      const missing = logs.filter(l => !l.Exists).map(l => l.Name);
      let logStatus = "OK";
      if (missing.length || unreadable.length) logStatus = "UNKNOWN";
      else if (disabled.length) logStatus = "ATTENTION";
      add("Event Logs", logStatus,
        logs.map(l => ({ name: l.Name, enabled: l.Enabled, readable: l.Readable, records: l.Records })),
        logStatus === "OK"
          ? `${logs.length}/${logs.length} log doc duoc va dang ghi`
          : [
            missing.length ? `khong ton tai: ${missing.join(", ")}` : null,
            unreadable.length ? `KHONG DOC DUOC: ${unreadable.join(", ")}` : null,
            disabled.length ? `dang TAT: ${disabled.join(", ")}` : null
          ].filter(Boolean).join("; "));

      // --- Risk Score (doc file canonical, khong tu tinh lai) --------------
      const risk = readStateFile("risk_score.json");
      if (!risk.readable) {
        add("Risk Score", "UNKNOWN", null,
          `Khong doc duoc state/risk_score.json: ${risk.error}`);
      } else {
        const age = hoursSince(risk.data.generated_at);
        const level = String(risk.data.risk_level || "").toUpperCase();
        const stale = age !== null && age > 24;
        add("Risk Score",
          stale ? "UNKNOWN" : (level === "CRITICAL" ? "CRITICAL" : (level === "LOW" ? "OK" : "ATTENTION")),
          {
            overallScore: risk.data.overall_score,
            riskLevel: risk.data.risk_level,
            criticalCount: risk.data.critical_count,
            highCount: risk.data.high_count,
            scale: risk.data.scale,
            generatedAt: risk.data.generated_at,
            ageHours: age === null ? null : Math.round(age * 10) / 10
          },
          // Diem cu doc y het diem moi neu khong ai noi no bao nhieu tuoi. Mot
          // diem rui ro 3 ngay tuoi khong phai la trang thai hom nay.
          stale
            ? `Diem da cu ${Math.floor(age)} gio — khong con mo ta trang thai hien tai, chay lai pipeline`
            : `${risk.data.overall_score}/100 (${risk.data.risk_level}), thang ${risk.data.scale}`);
      }

      // --- Incidents ------------------------------------------------------
      const incidents = readStateFile("incidents.json");
      if (!incidents.readable) {
        add("Incidents", "UNKNOWN", null,
          `Khong doc duoc state/incidents.json: ${incidents.error}`);
      } else {
        const total = incidents.data.total_incidents || 0;
        const bySeverity = incidents.data.by_severity || {};
        const open = (incidents.data.by_status || {}).OPEN || 0;
        const severe = (bySeverity.CRITICAL || 0) + (bySeverity.HIGH || 0);
        add("Incidents",
          bySeverity.CRITICAL ? "CRITICAL" : (severe || open ? "ATTENTION" : "OK"),
          {
            total,
            open,
            bySeverity,
            byStatus: incidents.data.by_status || {},
            recent: (incidents.data.incidents || []).slice(0, 5)
          },
          total ? `${total} su co, ${open} dang mo, ${severe} o muc HIGH tro len`
            : "Khong co su co nao duoc ghi nhan");
      }

      const tally = findings.reduce((acc, f) => {
        acc[f.status] = (acc[f.status] || 0) + 1;
        return acc;
      }, {});

      // Bang HTML van duoc ghi ra nhu cu, nhung gio no cho gia tri quan sat
      // duoc chu khong phai chu "Review".
      const categories = {};
      for (const finding of findings) {
        categories[finding.category] = { status: finding.status, details: finding.detail };
      }
      const report = generateAuditReport(
        `Security Audit Report (${auditType})`, categories, "audit");

      // UNKNOWN khong duoc gop vao "dat". Mot muc chua nhin thay khong phai mot
      // muc da qua — va cung khong phai mot muc da truot.
      const verdict = tally.CRITICAL ? "CRITICAL"
        : (tally.UNKNOWN ? "INCOMPLETE" : (tally.ATTENTION ? "ATTENTION" : "OK"));

      return evidenceResponse({
        auditType,
        verdict,
        summary: `${findings.length} hang muc: ${tally.OK || 0} OK, `
          + `${tally.ATTENTION || 0} can chu y, ${tally.CRITICAL || 0} nghiem trong, `
          + `${tally.UNKNOWN || 0} khong quan sat duoc`,
        recordCount: findings.length,
        tally,
        findings
      }, report);
    }
  );
}

