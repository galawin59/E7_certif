<#
Repo cleanup: remove transient/build artifacts.
Safe defaults: delete zip/archives, python caches, test caches, DS_Store/Thumbs, .coverage artifacts.
#>
param(
  [switch]$WhatIf
)

$ErrorActionPreference = 'SilentlyContinue'

$patterns = @(
  '**/*.zip','**/*.rar','**/*.7z','**/*.tar.gz',
  '**/__pycache__','**/.pytest_cache','**/.mypy_cache','**/.coverage*',
  '**/.ipynb_checkpoints','**/.DS_Store','**/Thumbs.db',
  '**/dist','**/build','**/*.log'
)

function Remove-Glob($glob) {
  $items = Get-ChildItem -Path $glob -Recurse -Force -ErrorAction SilentlyContinue
  foreach ($i in $items) {
    if ($WhatIf) { Write-Host "Would remove: $($i.FullName)" -ForegroundColor Yellow }
    else {
      if ($i.PSIsContainer) { Remove-Item -LiteralPath $i.FullName -Recurse -Force -ErrorAction SilentlyContinue }
      else { Remove-Item -LiteralPath $i.FullName -Force -ErrorAction SilentlyContinue }
    }
  }
}

foreach ($p in $patterns) { Remove-Glob $p }

if ($WhatIf) { Write-Host 'Cleanup (dry-run) complete.' -ForegroundColor Cyan }
else { Write-Host 'Cleanup complete.' -ForegroundColor Green }
