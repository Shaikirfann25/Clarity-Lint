$ErrorActionPreference = "Stop"
$Web = Split-Path -Parent $PSScriptRoot
$Project = Split-Path -Parent $Web
Write-Host "CLARITY LINT — IMPERIAL JADE WEB" -ForegroundColor Yellow
$Health = $false
try {
    Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 3 | Out-Null
    $Health = $true
    Write-Host "Backend already running on port 8000." -ForegroundColor Green
} catch {
    $Python = Join-Path $Project ".venv\Scripts\python.exe"
    if (!(Test-Path $Python)) { throw "Backend venv not found at $Python. Start the existing API separately." }
    Start-Process powershell.exe -ArgumentList @("-NoExit","-Command","Set-Location '$Project'; .\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000")
    Start-Sleep -Seconds 4
}
Set-Location $Web
if (!(Test-Path ".\node_modules")) { npm install; if ($LASTEXITCODE -ne 0) { throw "npm install failed." } }
if (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue) {
    Write-Host "Frontend port 3000 is already listening." -ForegroundColor Green
} else {
    Start-Process powershell.exe -ArgumentList @("-NoExit","-Command","Set-Location '$Web'; `$env:NEXT_PUBLIC_CLARITY_API_URL='http://127.0.0.1:8000'; npm run dev")
    Start-Sleep -Seconds 5
}
Start-Process "http://localhost:3000"
Write-Host "Dashboard: http://localhost:3000" -ForegroundColor Green
