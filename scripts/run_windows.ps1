$ErrorActionPreference = 'Stop'
Write-Host 'Clarity Lint — Environment & Application Launcher' -ForegroundColor Green

# Create virtual environment if not already present
if (-not (Test-Path '.venv')) {
    Write-Host 'Creating .venv virtual environment...' -ForegroundColor Cyan
    $pyCreated = $false
    if (Get-Command 'py' -ErrorAction SilentlyContinue) {
        $pyList = (& py --list 2>&1 | Out-String)
        if ($pyList -match '3\.11') {
            Write-Host 'Using Python 3.11 via py launcher...' -ForegroundColor Gray
            py -3.11 -m venv .venv
            $pyCreated = $true
        } elseif ($pyList -match '3\.12') {
            Write-Host 'Using Python 3.12 via py launcher...' -ForegroundColor Gray
            py -3.12 -m venv .venv
            $pyCreated = $true
        }
    }
    if (-not $pyCreated) {
        Write-Host 'Using default system python...' -ForegroundColor Gray
        python -m venv .venv
    }
}

$venvPython = ".\.venv\Scripts\python.exe"

# Upgrade pip and install pinned requirements
Write-Host 'Checking dependencies in .venv...' -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install -r requirements.txt

# Launch the Streamlit application
Write-Host 'Launching Clarity Lint Streamlit application...' -ForegroundColor Yellow
& $venvPython -m streamlit run app/app.py
