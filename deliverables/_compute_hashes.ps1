Param()
Set-StrictMode -Version Latest
$out = Join-Path $PSScriptRoot 'file_hashes.txt'
if (Test-Path $out) { Remove-Item $out -Force }
Get-ChildItem -Path $PSScriptRoot -File | ForEach-Object {
  $h = Get-FileHash -Algorithm SHA256 $_.FullName
  "$($h.Hash)  $($_.Name)" | Out-File -FilePath $out -Append -Encoding UTF8
}
Write-Host "Wrote hashes to $out"
