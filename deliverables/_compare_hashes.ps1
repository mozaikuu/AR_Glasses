Param()
Set-StrictMode -Version Latest
$base = $PSScriptRoot
$a = Get-Content -Path (Join-Path $base 'checksums.sha256') -Encoding Unicode
$b = Get-Content -Path (Join-Path $base 'file_hashes.txt') -Encoding UTF8
$d = Compare-Object -ReferenceObject $a -DifferenceObject $b
if ($d) {
  $d | Format-Table -AutoSize
} else {
  Write-Host 'No differences; checksums match'
}
Write-Host 'Comparison complete.'
