$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (!(Test-Path ".venv\Scripts\python.exe")) { py -3 -m venv .venv; if ($LASTEXITCODE -ne 0) { throw "Python 3.11+ is required" } }
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
& .\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
