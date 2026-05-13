$ErrorActionPreference = "Continue"
$PackageRoot = Split-Path -Parent $PSScriptRoot
$RepoRoot = (Resolve-Path (Join-Path $PackageRoot "..\..")).Path

$mdFiles = Get-ChildItem -Path $PackageRoot -Recurse -Filter "*.md" |
    Where-Object { $_.FullName -notmatch "\\dist\\" }

# Backtick-enclosed paths: app/..., clients/..., tests/..., firmware/..., or exactly start.py
$pattern = [regex]'`((?:app|clients|tests|firmware)/[^`]+|start\.py)`'

$issues = 0
foreach ($f in $mdFiles) {
    $content = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction SilentlyContinue
    if (-not $content) { continue }
    foreach ($m in $pattern.Matches($content)) {
        $rel = $m.Groups[1].Value.Trim()
        if (-not $rel) { continue }
        $rel = $rel -replace '/', [IO.Path]::DirectorySeparatorChar
        $candidate = Join-Path $RepoRoot $rel
        if (-not (Test-Path -LiteralPath $candidate)) {
            Write-Warning "Missing path (in $($f.Name)): ``$rel`` -> $candidate"
            $issues++
        }
    }
}

if ($issues -gt 0) {
    Write-Host "verify-paths: $issues warning(s)."
    exit 1
}

Write-Host "verify-paths: OK"
exit 0
