Param()
Set-StrictMode -Version Latest
$base = $PSScriptRoot
$a = Get-Content -Path (Join-Path $base 'checksums.sha256') -Encoding Unicode
$b = Get-Content -Path (Join-Path $base 'file_hashes.txt') -Encoding UTF8
$exclude = '_compute|file_hashes.txt|_compare|file_hashes'
$a_filtered = $a | Where-Object { $_ -notmatch $exclude }
$b_filtered = $b | Where-Object { $_ -notmatch $exclude }
$d = Compare-Object -ReferenceObject $a_filtered -DifferenceObject $b_filtered
if ($d) { $d | Format-Table -AutoSize } else { Write-Host 'No differences after filtering.' }
Write-Host 'Filtered comparison complete.'
