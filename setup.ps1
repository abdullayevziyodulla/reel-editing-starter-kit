param([switch]$SkipBrowser, [switch]$SkipModel)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONUTF8 = '1'
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue) -or -not (Get-Command ffprobe -ErrorAction SilentlyContinue)) {
    throw 'Install FFmpeg and add ffmpeg/ffprobe to PATH, then reopen PowerShell. See README.'
}
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    if (Get-Command py -ErrorAction SilentlyContinue) { & py -3.12 -m venv .venv }
    else { & python -m venv .venv }
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 is required.' }
}
& .venv/Scripts/python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
if (-not $SkipBrowser) {
    & .venv/Scripts/python.exe -m playwright install chromium
    if ($LASTEXITCODE -ne 0) { throw 'Chromium installation failed.' }
}
if (-not $SkipModel) {
    & .venv/Scripts/python.exe -X utf8 scripts/bootstrap.py --model
    if ($LASTEXITCODE -ne 0) { throw 'Model download failed.' }
}
if ($SkipBrowser) { & .venv/Scripts/python.exe -X utf8 scripts/bootstrap.py --doctor --skip-browser }
else { & .venv/Scripts/python.exe -X utf8 scripts/bootstrap.py --doctor }
if ($LASTEXITCODE -ne 0) { throw 'Setup check failed. See the errors above.' }
Write-Host 'Ready. Start with README.md or START_HERE_UZ.md.'
