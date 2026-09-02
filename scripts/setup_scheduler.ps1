# Setup Windows Task Scheduler - daily 07:00
$taskName = "AutoJobDailyScrape"
$projectRoot = Split-Path -Parent $PSScriptRoot
$batPath = Join-Path $projectRoot "scripts\run_daily.bat"
if (-not (Test-Path $batPath)) { Write-Error "run_daily.bat tidak ditemukan: $batPath"; exit 1 }
$action = New-ScheduledTaskAction -Execute $batPath
$trigger = New-ScheduledTaskTrigger -Daily -At 7:00AM
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Daily scrape MLE/AI jobs" -Force
Write-Host "Task '$taskName' terdaftar jam 07:00 daily -> $batPath"
Write-Host "Cek: Get-ScheduledTask -TaskName $taskName"
