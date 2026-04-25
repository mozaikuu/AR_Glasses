# Delete this temporary test folder after use.
$folder = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $folder)
Remove-Item -LiteralPath $folder -Recurse -Force
Write-Output "Deleted $folder"
