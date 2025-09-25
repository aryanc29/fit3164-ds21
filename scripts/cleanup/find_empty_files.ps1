<#
Find and optionally delete empty files under the repository root.
Usage:
  .\find_empty_files.ps1            # list empty files
  .\find_empty_files.ps1 -Delete   # delete empty files (prompts for confirmation)
#>

# CODE REVIEW: PowerShell script for finding and optionally deleting empty files
# GOOD PRACTICES:
# - Uses proper PowerShell parameter handling with [switch]$Delete
# - Includes comprehensive help documentation
# - Uses Write-Host with color coding for better UX
# - Includes confirmation prompt before deletion
# - Handles relative path resolution correctly
# - Uses -Force flag for hidden files
# - Provides clear feedback on operations
# IMPROVEMENTS:
# - Could add logging to file option
# - Could add file size threshold parameter
# - Could add file type filtering
# - Could add dry-run mode

param(
    [switch]$Delete
)

$root = Resolve-Path "..\.." -Relative | Split-Path -Parent
Write-Host "Searching for empty files under: $root"

$emptyFiles = Get-ChildItem -Path $root -Recurse -File -Force | Where-Object { $_.Length -eq 0 }

if ($emptyFiles.Count -eq 0) {
    Write-Host "No empty files found." -ForegroundColor Green
    exit 0
}

Write-Host "Empty files found:" -ForegroundColor Yellow
$emptyFiles | ForEach-Object { Write-Host " - $($_.FullName)" }

if ($Delete) {
    $confirm = Read-Host "Delete these $($emptyFiles.Count) files? Type 'yes' to confirm"
    if ($confirm -eq 'yes') {
        $emptyFiles | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force; Write-Host "Deleted: $($_.FullName)" }
        Write-Host "Deletion complete." -ForegroundColor Green
    } else {
        Write-Host "Aborted deletion." -ForegroundColor Cyan
    }
}
