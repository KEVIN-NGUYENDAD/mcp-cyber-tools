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

.PARAMETER Undo
    Go tai khoan khoi nhom "Event Log Readers", tra may ve trang thai cu.

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
Write-Host '  3. Ky vong: security_log readable = true, va 8 tool BLIND'
Write-Host '     chuyen sang PASS hoac EMPTY.'
Write-Host ''
