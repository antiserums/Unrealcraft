# Starts the Unrealcraft stack on the Windows server: API (port 8000), website (port 3000) and the Quartermaster bot.
# Usage: .\run.ps1            start all three in separate windows
#        .\run.ps1 api|web|bot start one of them in this window
param([ValidateSet("all", "api", "web", "bot")] [string] $What = "all")

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

$cmds = @{
  api = "Set-Location '$root\api'; `$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
  web = "Set-Location '$root\web'; npm run dev"
  bot = "Set-Location '$root\bot'; `$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m registrar"
}

if ($What -eq "all") {
  foreach ($k in "api", "web", "bot") {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmds[$k] -WindowStyle Normal
  }
  Write-Host "Started api (http://localhost:8000), web (http://localhost:3000) and bot in separate windows."
} else {
  Invoke-Expression $cmds[$What]
}
