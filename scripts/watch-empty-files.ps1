# FileSystem watcher to log new/changed empty files under the backend directory
# Usage: Open PowerShell as administrator (if needed) and run:
#   .\scripts\watch-empty-files.ps1
# Then in another terminal run your `docker-compose up` to reproduce.

$watchPath = Join-Path $PSScriptRoot '..\backend' | Resolve-Path -ErrorAction SilentlyContinue
if (-not $watchPath) {
    Write-Host "Could not find backend directory at expected path. Adjust \$watchPath and rerun." -ForegroundColor Yellow
    exit 1
}
$watchPath = $watchPath.Path

$logFile = Join-Path $PSScriptRoot 'watch-empty-files.log'
if (Test-Path $logFile) { Remove-Item $logFile -Force }

Write-Host "Watching: $watchPath" -ForegroundColor Green
Write-Host "Log: $logFile`n"

$fsw = New-Object System.IO.FileSystemWatcher $watchPath -Property @{ IncludeSubdirectories = $true; NotifyFilter = [System.IO.NotifyFilters]'FileName, LastWrite, Size' }

$action = {
    param($source, $e)
    try {
        Start-Sleep -Milliseconds 50 # small delay to allow file system to settle
        $full = $e.FullPath
        $exists = Test-Path $full
        $size = if ($exists) { (Get-Item $full -ErrorAction SilentlyContinue).Length } else { -1 }
        $entry = [PSCustomObject]@{
            Time = (Get-Date).ToString('o')
            ChangeType = $e.ChangeType
            Path = $full
            Size = $size
            ProcessList = (Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 | ForEach-Object { "{0} (Id:{1})" -f $_.ProcessName,$_.Id }) -join '; '
        }
        $line = $entry | ConvertTo-Json -Depth 3
        Add-Content -Path $using:logFile -Value $line
        Write-Host "[${entry.Time}] ${entry.ChangeType} ${entry.Path} (size=${entry.Size})" -ForegroundColor Cyan
        if ($entry.Size -eq 0) {
            Write-Host " --> Empty file created: ${entry.Path}" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Watcher handler error: $_" -ForegroundColor Red
    }
}

# Register events for Created and Changed
$createdReg = Register-ObjectEvent $fsw Created -Action $action
$changedReg = Register-ObjectEvent $fsw Changed -Action $action

# Start the watcher
$fsw.EnableRaisingEvents = $true
Write-Host "FileSystemWatcher enabled. Press Enter to stop and write summary..."

Read-Host | Out-Null

# Cleanup
$fsw.EnableRaisingEvents = $false
Unregister-Event -SourceIdentifier $createdReg.Name -ErrorAction SilentlyContinue
Unregister-Event -SourceIdentifier $changedReg.Name -ErrorAction SilentlyContinue
$fsw.Dispose()

# Print summary of empty files seen
Write-Host "\nSummary of empty files (from log):" -ForegroundColor Green
if (Test-Path $logFile) {
    Get-Content $logFile | ConvertFrom-Json | Where-Object { $_.Size -eq 0 } | Select-Object Time,Path,Size | Format-Table -AutoSize
} else {
    Write-Host "No log file found." -ForegroundColor Yellow
}

Write-Host "Watcher stopped." -ForegroundColor Green
