$env:PYTHONPATH = Join-Path $PSScriptRoot "..\backend"
$python = Join-Path $PSScriptRoot "..\tools\python312\python.exe"
& $python -m pytest (Join-Path $PSScriptRoot "..\tests")