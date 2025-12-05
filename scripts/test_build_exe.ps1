Param(
  [string]$ExePath = "dist\YouTubePlaylistExplorer.exe",
  [int]$WaitSeconds = 7,
  [switch]$Kill
)

Write-Host "[Test] Executable path: $ExePath" -ForegroundColor Cyan
if (-not (Test-Path $ExePath)) {
  Write-Error "[Test] Executable not found: $ExePath"
  exit 1
}

Write-Host "[Test] Launching EXE" -ForegroundColor Cyan
$proc = Start-Process -FilePath $ExePath -PassThru -WindowStyle Normal
Write-Host "[Test] PID: $($proc.Id)" -ForegroundColor Cyan

$exited = $proc.WaitForExit($WaitSeconds * 1000)
if ($exited) {
  $code = $proc.ExitCode
  if ($code -eq 0) {
    Write-Host "[Test] EXE exited successfully with code 0" -ForegroundColor Green
    exit 0
  } else {
    Write-Error "[Test] EXE exited with non-zero code: $code"
    exit 3
  }
}

try {
  $p = Get-Process -Id $proc.Id -ErrorAction Stop
  $title = $p.MainWindowTitle
  if ([string]::IsNullOrWhiteSpace($title)) {
    Write-Host "[Test] Process running; window title not reported" -ForegroundColor Yellow
  } else {
    Write-Host "[Test] Window title: $title" -ForegroundColor Green
  }
  Write-Host "[Test] EXE launch verification: OK" -ForegroundColor Green
  if ($Kill.IsPresent) {
    Write-Host "[Test] Stopping process PID $($proc.Id)" -ForegroundColor Cyan
    try { Stop-Process -Id $proc.Id -Force } catch {}
  }
  Write-Host "[Test] Done" -ForegroundColor Green
  exit 0
} catch {
  Write-Error "[Test] Process not running and did not exit cleanly"
  exit 2
}
