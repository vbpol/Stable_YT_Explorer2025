Param(
  [string]$PythonExe = "python"
)

Write-Host "[Local Deploy] Setting up virtual environment (.venv)" -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
  & $PythonExe -m venv .venv
}

$venvPython = Join-Path ".venv" "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
  $venvPython = Join-Path ".venv" "bin\python"
}

Write-Host "[Local Deploy] Installing dependencies" -ForegroundColor Cyan
if (Test-Path "requirements.txt") {
  & $venvPython -m pip install --upgrade pip
  & $venvPython -m pip install -r requirements.txt
} else {
  & $venvPython -m pip install --upgrade pip
  & $venvPython -m pip install yt-dlp python-dotenv
}

# Check ffmpeg availability
try {
  $ffmpeg = (Get-Command ffmpeg -ErrorAction SilentlyContinue)
  if (-not $ffmpeg) {
    Write-Warning "ffmpeg not found on PATH. HD merges will fall back to single MP4 streams. Install ffmpeg for best results."
  }
} catch {}

Write-Host "[Local Deploy] Launching app" -ForegroundColor Cyan
& $venvPython -m src.main

