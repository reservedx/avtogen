$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$python = Join-Path $repoRoot "tools\python312\python.exe"

Set-Location $repoRoot

& $python -m uvicorn --app-dir backend app.main:app --host 127.0.0.1 --port 8000 --reload
