Param(
  [switch]$OpenFirewall,
  [switch]$StartGateway
)

Write-Host "Smart Glasses Distilled machine setup" -ForegroundColor Cyan

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Write-Host "uv not found. Install uv first: https://docs.astral.sh/uv/getting-started/installation/" -ForegroundColor Yellow
  exit 1
}

Write-Host "Syncing Python dependencies with uv..."
uv sync
if ($LASTEXITCODE -ne 0) {
  Write-Host "uv sync failed" -ForegroundColor Red
  exit $LASTEXITCODE
}

if ($OpenFirewall) {
  Write-Host "Opening Windows firewall for TCP 8000..."
  netsh advfirewall firewall add rule name="SmartGlasses Gateway 8000" dir=in action=allow protocol=TCP localport=8000
}

Write-Host "Printing network info..."
uv run python scripts/print_network_info.py

if ($StartGateway) {
  Write-Host "Starting gateway launcher..."
  uv run python start.py --profile production-local --host 0.0.0.0 --port 8000
}
