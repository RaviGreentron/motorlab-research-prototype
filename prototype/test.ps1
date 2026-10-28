$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try { & .\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider } finally { Pop-Location }
