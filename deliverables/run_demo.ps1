Param()
$base = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $base

if (Test-Path .\docker_image.tar) {
    Write-Host "Loading Docker image..."
    docker load -i .\docker_image.tar
    Write-Host "Running container on port 8000..."
    docker run --rm -p 8000:8000 --name smartglasses_demo smartglasses:deliverable
} elseif (Test-Path .\bin\app_demo.exe) {
    Write-Host "Running binary fallback..."
    .\bin\app_demo.exe --demo-mode
} else {
    Write-Host "No runnable artifact found. See README.md"
    exit 2
}
