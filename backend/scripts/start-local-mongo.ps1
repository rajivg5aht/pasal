# Run from any directory. Uses the installed MongoDB binary and existing replica data.
$ErrorActionPreference = 'Stop'
$workspacePath = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$databasePath = Join-Path $workspacePath 'data/local-mongo'
if (-not (Test-Path -LiteralPath (Join-Path $databasePath 'WiredTiger'))) {
  throw 'Approved replica-set data directory missing. Do not initialize a different database silently.'
}
if (Get-NetTCPConnection -State Listen -LocalPort 27018 -ErrorAction SilentlyContinue) {
  Write-Output 'Port 27018 is already listening. Verify replica-set health before starting Pasal.'
  exit 0
}
$mongoExecutable = Get-ChildItem 'C:/Program Files/MongoDB/Server' -Filter mongod.exe -Recurse | Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $mongoExecutable) { throw 'Install MongoDB Server or specify its executable path.' }
$mongoArguments = '--dbpath "{0}" --port 27018 --bind_ip 127.0.0.1 --replSet pasalLocal --logpath "{1}" --logappend' -f $databasePath, (Join-Path $databasePath 'server.log')
Start-Process -FilePath $mongoExecutable -ArgumentList $mongoArguments -WindowStyle Hidden
Write-Output 'Started local MongoDB. Wait for primary readiness before starting the backend.'
