<#
.SYNOPSIS
    Bat hai kenh log dang TAT: TaskScheduler/Operational va
    DriverFrameworks-UserMode/Operational.

.DESCRIPTION
    Sprint 16, Priority 1 + 2.

    Hai kenh nay khong bi tu choi quyen - chung dang TAT. Khac biet do quan
    trong hon no trong:

        bi tu choi quyen -> co ban ghi, minh khong doc duoc
        dang tat        -> KHONG co ban ghi nao het, chua ai tung ghi

    `Get-WinEvent -LogName X` tra ve dung mot cau "No events were found" cho ca
    hai. Doc cau do roi ket luan "may sach" la cach mot he thong giam sat tu
    trao cho minh mot tam chung chi chua dat.

    Script nay doi Administrator. Mot script sua cau hinh may thi phai do nguoi
    quyet dinh chay, khong phai pipeline tu chay.

.PARAMETER Size
    Kich thuoc toi da moi kenh, don vi byte. Mac dinh 32MB. Mac dinh cua Windows
    la 10MB (TaskScheduler) va 1MB (DriverFrameworks) - 1MB cuon vong trong
    vai gio tren mot may co cam USB thuong xuyen, tuc la bang chung bien mat
    truoc khi co ai kip hoi den no.

.PARAMETER Revert
    Tat lai hai kenh, tra ve dung trang thai truoc khi chay script nay.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\enable_forensic_logs.ps1
#>

[CmdletBinding()]
param(
    [int]$Size = 33554432,
    [switch]$Revert
)

$ErrorActionPreference = 'Stop'

$Channels = @(
    @{ Name = 'Microsoft-Windows-TaskScheduler/Operational'
       Why  = 'Task Scheduler ghi lai tac vu nao duoc TAO, SUA, va CHAY thuc su. Khong co no, huntSuspiciousTasks chi thay tac vu dang ton tai - khong thay tac vu da chay roi bi xoa.' },
    @{ Name = 'Microsoft-Windows-DriverFrameworks-UserMode/Operational'
       Why  = 'Kenh nay ghi thiet bi USB nao duoc cam vao va luc nao. usbLogs khong co nguon nao khac cho cau hoi do.' }
)

function Get-ChannelState {
    param([string]$Name)
    try {
        $log = Get-WinEvent -ListLog $Name -ErrorAction Stop
        return [pscustomobject]@{
            Name    = $Name
            Found   = $true
            Enabled = [bool]$log.IsEnabled
            Records = [int64]$log.RecordCount
            MaxSize = [int64]$log.MaximumSizeInBytes
        }
    } catch {
        return [pscustomobject]@{
            Name = $Name; Found = $false; Enabled = $false
            Records = 0; MaxSize = 0
        }
    }
}

$identity  = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
$isAdmin   = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

Write-Host ''
Write-Host '=== ENABLE FORENSIC LOGS (Sprint 16) ===' -ForegroundColor Cyan
Write-Host ("Tai khoan : {0}" -f $identity.Name)
Write-Host ("Quyen     : {0}" -f $(if ($isAdmin) { 'Administrator' } else { 'KHONG nang quyen' }))
Write-Host ''

Write-Host 'TRUOC:' -ForegroundColor Yellow
$before = @{}
foreach ($channel in $Channels) {
    $state = Get-ChannelState -Name $channel.Name
    $before[$channel.Name] = $state
    if (-not $state.Found) {
        Write-Host ("  [?] {0} - KHONG TIM THAY tren may nay" -f $state.Name) -ForegroundColor Red
    } else {
        $mark = if ($state.Enabled) { '[v]' } else { '[x]' }
        $color = if ($state.Enabled) { 'Green' } else { 'Red' }
        Write-Host ("  {0} {1}" -f $mark, $state.Name) -ForegroundColor $color
        Write-Host ("      bat={0} ban_ghi={1} kich_thuoc={2}MB" -f `
            $state.Enabled, $state.Records, [math]::Round($state.MaxSize / 1MB, 1))
    }
}
Write-Host ''

if (-not $isAdmin) {
    Write-Host 'DUNG LAI: can Administrator.' -ForegroundColor Red
    Write-Host ''
    Write-Host 'Mo PowerShell bang "Run as Administrator" roi chay lai:' -ForegroundColor Yellow
    Write-Host ('  powershell -ExecutionPolicy Bypass -File "{0}"' -f $PSCommandPath)
    Write-Host ''
    Write-Host 'Khong co gi bi thay doi.' -ForegroundColor DarkGray
    exit 2
}

$target = -not $Revert
$changed = 0
$failed  = 0

foreach ($channel in $Channels) {
    $name  = $channel.Name
    $state = $before[$name]

    if (-not $state.Found) {
        Write-Host ("BO QUA {0}: kenh khong ton tai tren may nay." -f $name) -ForegroundColor DarkYellow
        continue
    }
    if ($state.Enabled -eq $target) {
        Write-Host ("DA DUNG {0}: bat={1}, khong can lam gi." -f $name, $target) -ForegroundColor DarkGray
        continue
    }

    Write-Host ("{0} {1}" -f $(if ($target) { 'BAT' } else { 'TAT' }), $name) -ForegroundColor Cyan
    if ($target) { Write-Host ("     vi sao: {0}" -f $channel.Why) -ForegroundColor DarkGray }

    try {
        if ($target) {
            # Kich thuoc phai dat TRUOC khi bat. Doi voi kenh dang tat, wevtutil
            # tu choi sua thuoc tinh khac trong cung mot lenh voi /e:true tren
            # mot so ban Windows - nen tach lam hai buoc, buoc nao hong thi biet
            # ngay buoc do.
            & wevtutil.exe sl $name "/ms:$Size" 2>&1 | Out-Null
            & wevtutil.exe sl $name '/e:true'   2>&1 | Out-Null
        } else {
            & wevtutil.exe sl $name '/e:false'  2>&1 | Out-Null
        }
    } catch {
        Write-Host ("     LOI: {0}" -f $_.Exception.Message) -ForegroundColor Red
        $failed++
        continue
    }

    # Khong tin lenh da chay xong la da co tac dung. Doc lai.
    $after = Get-ChannelState -Name $name
    if ($after.Enabled -eq $target) {
        Write-Host '     OK' -ForegroundColor Green
        $changed++
    } else {
        Write-Host ("     THAT BAI: van bat={0}" -f $after.Enabled) -ForegroundColor Red
        $failed++
    }
}

Write-Host ''
Write-Host 'SAU:' -ForegroundColor Yellow
$result = @()
foreach ($channel in $Channels) {
    $state = Get-ChannelState -Name $channel.Name
    $result += $state
    $mark  = if ($state.Enabled) { '[v]' } else { '[x]' }
    $color = if ($state.Enabled) { 'Green' } else { 'Red' }
    Write-Host ("  {0} {1}  bat={2} ban_ghi={3} kich_thuoc={4}MB" -f `
        $mark, $state.Name, $state.Enabled, $state.Records,
        [math]::Round($state.MaxSize / 1MB, 1)) -ForegroundColor $color
}

Write-Host ''
Write-Host ("Da doi: {0} | That bai: {1}" -f $changed, $failed)
Write-Host ''
if ($target -and $failed -eq 0) {
    Write-Host 'Luu y ve cai se thay tiep theo:' -ForegroundColor Yellow
    Write-Host '  Kenh vua bat co 0 ban ghi. Do KHONG phai loi - no chua co thoi gian'
    Write-Host '  ghi gi ca. Coverage se bao "vua bat, chua co ban ghi" cho toi khi'
    Write-Host '  ban ghi dau tien xuat hien; goi no la COVERED ngay bay gio se la'
    Write-Host '  noi qua.' -ForegroundColor DarkGray
    Write-Host ''
    Write-Host 'Buoc tiep:' -ForegroundColor Cyan
    Write-Host '  python scripts\refresh_sensor_coverage.py   # doc lai ngay'
    Write-Host ''
}

exit $(if ($failed -gt 0) { 1 } else { 0 })
