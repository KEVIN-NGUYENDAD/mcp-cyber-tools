<#
.SYNOPSIS
    Mo log Security cho pipeline doc duoc MA KHONG can nang quyen moi lan chay.

.DESCRIPTION
    Sprint 8 ket luan: 8 tool mu vi log Security doi quyen Administrator.
    Sprint 9 do ky hon va tim ra dieu quan trong hon:

        tai khoan NAY CO trong nhom Administrators.
        Tien trinh chi chua nang quyen (UAC loc token thanh "deny only").

    Nghia la khong can xin ai cap quyen gi. Chi can chay script nay MOT LAN.

    Vi sao them vao nhom "Event Log Readers" chu khong phai "cu chay pipeline
    bang quyen admin":

        Nang quyen sua duoc DUNG MOT LAN CHAY. Pipeline chay theo lich thi
        khong co ai o do de bam UAC. Thanh vien nhom sua VINH VIEN, cho moi
        lan chay binh thuong ve sau.

    Script nay KHONG lam gi ngoai pham vi tren tru khi duoc yeu cau ro rang
    bang -EnableProcessAuditing.

.PARAMETER UserName
    Tai khoan can cap quyen doc. Mac dinh: nguoi dang chay script.

.PARAMETER EnableProcessAuditing
    Bat them audit "Process Creation" (sinh Event ID 4688).
    KHONG bat mac dinh: day la thay doi chinh sach bao mat cua may, va no lam
    log Security day nhanh hon. Chi bat khi ban that su muon giam sat 4688.

.PARAMETER EnableScriptBlockLogging
    Bat chinh sach Script Block Logging (sinh Event ID 4104 cho MOI khoi lenh
    PowerShell).

    Vi sao dieu nay dang mot cong tac rieng: khi chinh sach TAT, PowerShell VAN
    tu ghi 4104 cho nhung khoi lenh NO cho la dang ngo. Nen log co ban ghi, va
    moi bang tong hop deu hien mau xanh — trong khi thuc te chi mot phan duoc
    ghi. Do la ly do sensor_probe.py xep nang luc nay la PARTIAL chu khong phai
    COVERED khi chua bat.

    KHONG bat mac dinh: noi dung moi lenh PowerShell se duoc ghi lai, ke ca lenh
    co chua chuoi nhay cam nguoi dung go tay.

.PARAMETER Undo
    Go tai khoan khoi nhom "Event Log Readers", tra may ve trang thai cu.
    KHONG dong thoi tat lai audit hay Script Block Logging: go mot quyen doc thi
    an toan, con tat mot nguon ghi lai la lam may mu di, nen viec do phai duoc
    go rieng va co chu y.

.EXAMPLE
    # Chay trong mot cua so PowerShell DA NANG QUYEN (Run as Administrator):
    .\scripts\enable_security_log_access.ps1

.EXAMPLE
    .\scripts\enable_security_log_access.ps1 -EnableProcessAuditing

.EXAMPLE
    .\scripts\enable_security_log_access.ps1 -Undo

.NOTES
    Kiem chung sau khi chay:
        1. Dang xuat va dang nhap lai  (token chi nhan nhom moi khi tao lai)
        2. python scripts/sensor_probe.py
        3. Cho ky vong: security_log readable = true
#>

[CmdletBinding()]
param(
    [string]$UserName,
    [switch]$EnableProcessAuditing,
    [switch]$EnableScriptBlockLogging,
    [switch]$Undo
)

$ErrorActionPreference = 'Stop'

function Write-Step($text)  { Write-Host "  $text" }
function Write-Good($text)  { Write-Host "  [OK]   $text"   -ForegroundColor Green }
function Write-Warn2($text) { Write-Host "  [WARN] $text"   -ForegroundColor Yellow }
function Write-Bad($text)   { Write-Host "  [FAIL] $text"   -ForegroundColor Red }

Write-Host ''
Write-Host '=============================================================='
Write-Host ' SECURITY LOG ACCESS' -ForegroundColor Cyan
Write-Host '=============================================================='
Write-Host ''

# --------------------------------------------------------------------------
# 1. Phai nang quyen. Kiem tra truoc khi lam bat cu thay doi nao.
# --------------------------------------------------------------------------
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]$identity
$isElevated = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isElevated) {
    Write-Bad 'Cua so nay CHUA nang quyen.'
    Write-Host ''
    Write-Host '  Script nay thay doi thanh vien nhom cuc bo, nen bat buoc phai'
    Write-Host '  chay duoi quyen Administrator. Cach lam:'
    Write-Host ''
    Write-Host '    1. Bam phim Windows, go "PowerShell"'
    Write-Host '    2. Chuot phai -> Run as administrator'
    Write-Host '    3. cd "' -NoNewline; Write-Host (Split-Path $PSScriptRoot -Parent) -NoNewline; Write-Host '"'
    Write-Host '    4. .\scripts\enable_security_log_access.ps1'
    Write-Host ''
    exit 1
}
Write-Good ("Da nang quyen (dang chay voi tu cach {0})" -f $identity.Name)

if (-not $UserName) { $UserName = $identity.Name }
Write-Step ("Tai khoan muc tieu: {0}" -f $UserName)
Write-Host ''

# --------------------------------------------------------------------------
# 2. Nhom Event Log Readers
# --------------------------------------------------------------------------
$groupName = 'Event Log Readers'
Write-Host '-- Nhom "Event Log Readers" ---------------------------------'

$existing = @()
try {
    $existing = @(Get-LocalGroupMember -Group $groupName -ErrorAction Stop |
                  ForEach-Object { $_.Name })
} catch {
    Write-Bad ("Khong doc duoc nhom: {0}" -f $_.Exception.Message)
    exit 1
}

$alreadyMember = $existing -contains $UserName

if ($Undo) {
    if (-not $alreadyMember) {
        Write-Warn2 'Tai khoan khong o trong nhom — khong co gi de go.'
    } else {
        Remove-LocalGroupMember -Group $groupName -Member $UserName -ErrorAction Stop
        Write-Good 'Da go khoi nhom. Log Security se dong lai sau khi dang nhap lai.'
    }
    Write-Host ''
    exit 0
}

if ($alreadyMember) {
    Write-Warn2 'Tai khoan DA o trong nhom — khong thay doi gi.'
    Write-Step 'Neu log Security van dong: ban chua dang xuat/dang nhap lai.'
} else {
    Add-LocalGroupMember -Group $groupName -Member $UserName -ErrorAction Stop
    Write-Good 'Da them tai khoan vao nhom.'
}
Write-Host ''

# --------------------------------------------------------------------------
# 3. Audit Process Creation — chi khi duoc yeu cau ro rang
# --------------------------------------------------------------------------
Write-Host '-- Audit "Process Creation" (Event ID 4688) -----------------'

$auditRaw = & "$env:SystemRoot\System32\auditpol.exe" /get /subcategory:"Process Creation"
$auditText = ($auditRaw | Out-String).Trim()
$auditOn = $auditText -match 'Success'

if ($auditOn) {
    Write-Good 'Audit dang BAT — Event 4688 se duoc ghi.'
} elseif (-not $EnableProcessAuditing) {
    Write-Warn2 'Audit dang TAT — se khong co Event 4688 nao du log da mo duoc.'
    Write-Step 'Chay lai kem -EnableProcessAuditing neu ban muon bat.'
    Write-Step 'Luu y: bat len se lam log Security day nhanh hon dang ke.'
} else {
    & "$env:SystemRoot\System32\auditpol.exe" /set /subcategory:"Process Creation" /success:enable | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Good 'Da bat audit Process Creation (success).'
        Write-Step 'Tat lai: auditpol /set /subcategory:"Process Creation" /success:disable'
    } else {
        Write-Bad ("auditpol tra ve ma {0}" -f $LASTEXITCODE)
    }
}
Write-Host ''

# --------------------------------------------------------------------------
# 3b. Script Block Logging — chi khi duoc yeu cau ro rang
#
# Day la o PARTIAL duy nhat trong bang nang luc, va no PARTIAL vi mot ly do de
# bi bo qua: 4104 VAN duoc ghi khi chinh sach tat, chi la ghi co chon loc. Mot
# he thong chi dem "co ban ghi khong" se cham diem chinh no cao hon su that.
# --------------------------------------------------------------------------
Write-Host '-- Script Block Logging (Event ID 4104) ---------------------'

$sblPath = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging'
$sblValue = $null
try {
    $sblValue = (Get-ItemProperty -Path $sblPath -Name EnableScriptBlockLogging -ErrorAction Stop).EnableScriptBlockLogging
} catch {
    $sblValue = $null
}

if ($sblValue -eq 1) {
    Write-Good 'Chinh sach dang BAT — moi khoi lenh PowerShell deu duoc ghi.'
} elseif (-not $EnableScriptBlockLogging) {
    Write-Warn2 'Chinh sach dang TAT — chi nhung khoi lenh PowerShell tu cho la dang ngo moi duoc ghi.'
    Write-Step 'Log van co su kien 4104, nen no TRONG NHU da phu song. Thuc te la mot phan.'
    Write-Step 'Chay lai kem -EnableScriptBlockLogging neu ban muon ghi day du.'
} else {
    if (-not (Test-Path $sblPath)) { New-Item -Path $sblPath -Force | Out-Null }
    New-ItemProperty -Path $sblPath -Name EnableScriptBlockLogging `
        -Value 1 -PropertyType DWord -Force | Out-Null
    Write-Good 'Da bat Script Block Logging.'
    Write-Step 'Tat lai: Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" -Name EnableScriptBlockLogging -Value 0'
    Write-Step 'Luu y: noi dung moi lenh PowerShell se nam trong log ke tu bay gio.'
}
Write-Host ''

# --------------------------------------------------------------------------
# 4. Kiem chung ngay tai day
# --------------------------------------------------------------------------
Write-Host '-- Kiem chung -----------------------------------------------'
try {
    $ev = Get-WinEvent -LogName 'Security' -MaxEvents 1 -ErrorAction Stop
    Write-Good ("Doc duoc log Security tu cua so NAY (su kien gan nhat: ID {0})" -f $ev.Id)
} catch {
    Write-Warn2 ("Cua so nay chua doc duoc: {0}" -f $_.Exception.Message)
}
Write-Host ''

Write-Host '=============================================================='
Write-Host ' BUOC TIEP THEO' -ForegroundColor Cyan
Write-Host '=============================================================='
Write-Host ''
Write-Host '  1. DANG XUAT va DANG NHAP LAI.'
Write-Host '     Windows chi gan nhom moi vao token luc tao token. Khong dang'
Write-Host '     nhap lai thi tien trinh khong nang quyen van thay log dong.'
Write-Host ''
Write-Host '  2. Kiem lai bang tien trinh BINH THUONG (khong nang quyen):'
Write-Host '       python scripts/sensor_probe.py'
Write-Host '       python scripts/tool_validator.py'
Write-Host ''
Write-Host '  3. Ky vong: security_log readable = true, va 5 tool BLIND'
Write-Host '     chuyen sang PASS hoac EMPTY.'
Write-Host ''
Write-Host '     Trong bang "Nang luc phat hien":'
Write-Host '       Security Log          BLIND   -> COVERED'
Write-Host '       Process Creation      BLIND   -> COVERED neu audit 4688 dang bat'
Write-Host '                                        (ProcessCreationIncludeCmdLine da = 1)'
Write-Host '       Script Block Logging  PARTIAL -> COVERED chi khi chay kem'
Write-Host '                                        -EnableScriptBlockLogging'
Write-Host ''
