$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$manifest = Get-Content (Join-Path $root "workspace.json") -Raw | ConvertFrom-Json
foreach ($repo in $manifest.repositories) {
$dest = Join-Path $root $repo.folder
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
if (Test-Path (Join-Path $dest ".git")) { Write-Host "Already cloned: $($repo.name) - preserving local repo" } else { git clone $repo.url $dest }
}
$dirs = @("database/source_records","database/exports/en","database/exports/ta","database/exports/si","database/esp32","web-tests","local-sync")
foreach ($d in $dirs) { New-Item -ItemType Directory -Force -Path (Join-Path $root $d) | Out-Null }
Write-Host "Clones complete. Configure local Dropbox and Drive synced folder paths."