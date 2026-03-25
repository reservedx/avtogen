$env:PYTHONPATH = Join-Path $PSScriptRoot "..\backend"
$python = Join-Path $PSScriptRoot "..\tools\python312\python.exe"
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload