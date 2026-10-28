param([int]$Port = 8765)
$ErrorActionPreference = 'Stop'
$localPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$workspacePython = Join-Path $PSScriptRoot '..\..\work\.venv\Scripts\python.exe'
$runtimePython = if (Test-Path -LiteralPath $localPython) { $localPython } elseif (Test-Path -LiteralPath $workspacePython) { $workspacePython } else { throw 'Run setup.ps1 -PythonPath <Python 3.12 executable> first.' }
Push-Location $PSScriptRoot
try { & $runtimePython -m uvicorn motorlab.api:app --host 127.0.0.1 --port $Port } finally { Pop-Location }
