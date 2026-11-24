# SwasthAI local setup for Windows.
# Run from the repository root:
#   powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "Python:"
py -3.14 --version
Write-Host "GPU:"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv

if (-not (Test-Path ".\.venv")) {
    py -3.14 -m venv .venv
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m pip install -r requirements-ml.txt

Write-Host ""
Write-Host "ICBHI 2017 is not downloaded by this script."
Write-Host "Place registered files in data\external\icbhi\  (see docs\ICBHI_SETUP.md)."
Write-Host ""
Write-Host "Frontend:  .\.venv\Scripts\python.exe -m streamlit run frontend\app.py"
Write-Host "API:       .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"
Write-Host "Tests:     .\.venv\Scripts\python.exe -m pytest tests -q"
Write-Host "Smoke train (not ICBHI): .\.venv\Scripts\python.exe -c \"from ml.respiratory.training.train import train_respiratory_model; train_respiratory_model(epochs=3, smoke_test=True)\""
