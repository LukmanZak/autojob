# Register the visible quote agent at 06:00 every day.
$taskName = "QuoteAgentDailyContent"
$projectRoot = Split-Path -Parent $PSScriptRoot
$batPath = Join-Path $projectRoot "scripts\run_quote_agent.bat"
if (-not (Test-Path $batPath)) {
    Write-Error "run_quote_agent.bat tidak ditemukan: $batPath"
    exit 1
}

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batPath`""
$trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType InteractiveToken `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Generate four quote images in Google Flow and send them to the owner's WhatsApp chat" `
    -Force

Write-Host "Task '$taskName' terdaftar setiap hari jam 06:00."
Write-Host "Cek: Get-ScheduledTask -TaskName $taskName"
Write-Host "Catatan: Windows harus sedang login agar browser terlihat."
