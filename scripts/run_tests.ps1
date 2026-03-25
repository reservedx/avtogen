$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$python = Join-Path $repoRoot "tools\python312\python.exe"
$testsPath = Join-Path $repoRoot "tests"
$backendPath = Join-Path $repoRoot "backend"

Set-Location $repoRoot

@"
import sys
import pytest

sys.path.insert(0, r"$backendPath")
raise SystemExit(pytest.main([r"$testsPath"]))
"@ | & $python -
