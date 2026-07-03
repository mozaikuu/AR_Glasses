Param()
Set-StrictMode -Version Latest
$base = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $base

Write-Host "Building Docker image smartglasses:deliverable (if Dockerfile exists at repo root)"
if (Test-Path "..\Dockerfile") {
  docker build -t smartglasses:deliverable ..
} else {
  Write-Host "No Dockerfile found; skipping docker build"
}

try {
  docker image inspect smartglasses:deliverable | Out-Null
  Write-Host "Saving docker image to docker_image.tar..."
  docker save -o docker_image.tar smartglasses:deliverable
} catch {
  Write-Host "Docker image not found; skipping save"
}

Write-Host "Generating checksums..."
Get-ChildItem -Path * -File | ForEach-Object {
  $h = Get-FileHash -Algorithm SHA256 $_.FullName
  "{0}  {1}" -f $h.Hash, $_.Name | Out-File -Append -FilePath checksums.sha256
}

if (Get-Command gpg -ErrorAction SilentlyContinue) {
  gpg --output checksums.sha256.sig --detach-sign checksums.sha256
} else {
  Write-Host "gpg not found; skipping signature generation"
}

Compress-Archive -Path * -DestinationPath ..\deliverables.zip -Force
Write-Host "deliverables.zip created"
