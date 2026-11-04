$ErrorActionPreference = 'Stop'
Write-Host 'Clarity Lint — Imperial Jade setup' -ForegroundColor Green
if (-not (Test-Path '.venv')) { py -3.11 -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
Write-Host 'Launching Streamlit...' -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m streamlit run app/app.py
