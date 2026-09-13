import { z } from "zod";
import { runPowerShell, formatResponse } from "./shared.js";

/**
 * Mọi truy vấn hunting đều phải phân biệt được hai trạng thái khác hẳn nhau:
 *
 *   "đã săn, không thấy gì"  -> máy sạch, kết quả hợp lệ  -> []
 *   "không săn được"         -> lỗi, kết quả vô nghĩa     -> isError
 *
 * Trước bản sửa này cả hai đều ra cùng một chỗ. `Get-WinEvent` ném lỗi khi
 * không có sự kiện nào khớp ("No events were found..."), PowerShell thoát với
 * mã khác 0, và tool báo hỏng - dù câu trả lời đúng là "máy này sạch".
 *
 * jsonOrEmpty() ép mọi truy vấn về một hợp đồng duy nhất: luôn là JSON hợp lệ,
 * `[]` khi không có gì, và exit 0 khi cuộc săn thực sự đã chạy.
 */
function jsonOrEmpty(body, depth = 4) {
  return `
$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference = 'SilentlyContinue'
$result = @(${body})
if ($result.Count -eq 0) { Write-Output '[]' }
else { Write-Output ($result | ConvertTo-Json -Depth ${depth} -Compress) }
exit 0
`;
}

export function registerHuntingTools(server) {
  // 1. HUNTENCODEDPOWERSHELL
  server.tool(
    "huntEncodedPowerShell",
    "Hunt for encoded PowerShell commands",
    {},
    async () => {
      const result = runPowerShell(jsonOrEmpty(`
        Get-WinEvent -FilterHashtable @{LogName='Windows PowerShell'; Id=400,600,800} -MaxEvents 100 -ErrorAction SilentlyContinue |
        Where-Object { $_.Message -match 'EncodedCommand|FromBase64|DownloadString' } |
        Select-Object TimeCreated, Id, Message
      `));
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 2. HUNTPERSISTENCE
  server.tool(
    "huntPersistence",
    "Hunt for persistence mechanisms",
    {},
    async () => {
      const result = runPowerShell(jsonOrEmpty(`
        Get-ScheduledTask |
        Where-Object { $_.TaskPath -notlike '*\\Microsoft\\*' -and $_.State -ne 'Disabled' } |
        ForEach-Object {
          [PSCustomObject]@{
            Kind     = 'ScheduledTask'
            Name     = $_.TaskName
            Location = $_.TaskPath
            State    = [string]$_.State
            Author   = $_.Author
          }
        }
        Foreach ($hive in @('HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                            'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run')) {
          $key = Get-ItemProperty -Path $hive -ErrorAction SilentlyContinue
          if ($key) {
            $key.PSObject.Properties |
            Where-Object { $_.Name -notlike 'PS*' } |
            ForEach-Object {
              [PSCustomObject]@{
                Kind     = 'RunKey'
                Name     = $_.Name
                Location = $hive
                State    = 'Enabled'
                Command  = [string]$_.Value
              }
            }
          }
        }
      `));
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 3. HUNTSUSPICIOUSSERVICES
  server.tool(
    "huntSuspiciousServices",
    "Hunt for suspicious services",
    {},
    async () => {
      const result = runPowerShell(jsonOrEmpty(`
        Get-CimInstance Win32_Service -ErrorAction SilentlyContinue |
        Where-Object {
          $_.PathName -and
          $_.PathName -notmatch 'system32|SysWOW64' -and
          $_.State -eq 'Running'
        } |
        Select-Object Name, DisplayName, State, StartMode, PathName
      `));
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 4. HUNTSUSPICIOUSTASKS
  server.tool(
    "huntSuspiciousTasks",
    "Hunt for suspicious scheduled tasks",
    {},
    async () => {
      const result = runPowerShell(jsonOrEmpty(`
        Get-ScheduledTask |
        Where-Object { $_.TaskPath -notlike '*\\Microsoft\\*' -and $_.State -ne 'Disabled' } |
        Select-Object TaskName, TaskPath, @{N='State';E={[string]$_.State}}, Author
      `));
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 5. HUNTCREDENTIALDUMPING
  //    Phụ thuộc Security log Id 4688 (process creation). Trên Windows Home,
  //    audit chính sách này TẮT mặc định, nên [] ở đây nghĩa là "không quan sát
  //    được", không phải "chắc chắn sạch". Người tiêu thụ phải biết phân biệt.
  server.tool(
    "huntCredentialDumping",
    "Hunt for credential dumping attempts",
    {},
    async () => {
      const result = runPowerShell(jsonOrEmpty(`
        Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4688} -MaxEvents 1000 -ErrorAction SilentlyContinue |
        Where-Object { $_.Message -match 'lsass|mimikatz|ntdsutil|procdump|comsvcs' } |
        Select-Object TimeCreated, Id, Message
      `));
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 6. HUNTLATERALMOVEMENT
  server.tool(
    "huntLateralMovement",
    "Hunt for lateral movement indicators",
    {},
    async () => {
      const result = runPowerShell(jsonOrEmpty(`
        Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624,4769,4768} -MaxEvents 500 -ErrorAction SilentlyContinue |
        Where-Object { $_.Message -match 'Network|3389|445' } |
        Select-Object TimeCreated, Id, Message
      `));
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 7. HUNTREMOTEDESKTOP
  server.tool(
    "huntRemoteDesktop",
    "Hunt for RDP activity and anomalies",
    {},
    async () => {
      const result = runPowerShell(jsonOrEmpty(`
        Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624,4625,4648,4778,4779} -MaxEvents 100 -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, Message
      `));
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 8. HUNTNETWORKBEACONS
  server.tool(
    "huntNetworkBeacons",
    "Hunt for network beacon indicators",
    {},
    async () => {
      const result = runPowerShell(jsonOrEmpty(`
        Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
        Where-Object { $_.RemotePort -in @(443,80,8080,53) } |
        ForEach-Object {
          $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
          [PSCustomObject]@{
            Process       = $proc.Name
            ProcessId     = $_.OwningProcess
            RemoteAddress = $_.RemoteAddress
            RemotePort    = $_.RemotePort
            LocalPort     = $_.LocalPort
            Path          = $proc.Path
          }
        }
      `));
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 9. HUNTLIVINGOFFTHELAND
  server.tool(
    "huntLivingOffTheLand",
    "Hunt for Living off the Land Binaries (LOLBins)",
    {},
    async () => {
      const result = runPowerShell(jsonOrEmpty(`
        $lolbins = @('powershell','pwsh','cmd','wscript','cscript','regsvcs','regasm','msiexec','rundll32','schtasks','certutil','bitsadmin','mshta','installutil','msbuild')
        Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $lolbins -contains $_.Name } |
        Select-Object Name, Id, Path, @{N='StartTime';E={ if ($_.StartTime) { $_.StartTime.ToString('o') } else { $null } }}
      `));
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 10. HUNTINDICATORS
  server.tool(
    "huntIndicators",
    "Hunt for various IOCs (Indicators of Compromise)",
    {
      indicatorType: z.enum(["suspicious_ports", "unusual_binaries", "network_anomalies"]).optional()
    },
    async ({ indicatorType = "suspicious_ports" }) => {
      let body;
      if (indicatorType === "suspicious_ports") {
        body = `
          Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
          Where-Object { $_.RemotePort -in @(4444,5555,6666,7777,8888,9999) } |
          Select-Object LocalAddress, RemoteAddress, RemotePort, OwningProcess
        `;
      } else if (indicatorType === "unusual_binaries") {
        // Không quét cả \AppData\: phần mềm hiện đại cài theo từng người dùng vào
        // %LOCALAPPDATA%\Programs là chuyện bình thường (Zalo, Canva, Webex,
        // Claude Code...). Gắn cờ cả nhánh đó chỉ đổi cảnh báo giả lấy cảnh báo
        // sai - vẫn là thứ người trực ca phải bỏ đi.
        body = `
          Get-Process -ErrorAction SilentlyContinue |
          Where-Object {
            $_.Path -like '*\\Temp\\*' -or
            $_.Path -like '*\\Downloads\\*' -or
            $_.Path -like '*\\Users\\Public\\*'
          } |
          Select-Object Name, Path, Id
        `;
      } else {
        body = `
          Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
          Select-Object RemoteAddress, RemotePort, OwningProcess |
          Sort-Object RemotePort -Unique
        `;
      }
      const result = runPowerShell(jsonOrEmpty(body));
      return formatResponse(result.success, result.data, result.error);
    }
  );
}
