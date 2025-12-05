Param(
  [string]$PythonExe = "python",
  [string]$AppName = "YouTubePlaylistExplorer",
  [ValidateSet('onefile','onedir')][string]$Mode = 'onefile'
)

Write-Host "[Build] Preparing virtual environment (.venv)" -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
  & $PythonExe -m venv .venv
}

$venvPython = Join-Path ".venv" "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
  $venvPython = Join-Path ".venv" "bin\python"
}

Write-Host "[Build] Upgrading pip and installing PyInstaller" -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install pyinstaller

Write-Host "[Build] Installing application dependencies" -ForegroundColor Cyan
if (Test-Path "requirements.txt") {
  & $venvPython -m pip install -r requirements.txt
} else {
  & $venvPython -m pip install google-api-python-client python-vlc isodate pandas python-dotenv yt-dlp httplib2 google-auth google-auth-oauthlib google-auth-httplib2 uritemplate
}

$tclBase = (& $venvPython -c "import sys, os; print(os.path.join(sys.base_prefix, 'tcl'))")
$tclDir = Join-Path $tclBase "tcl8.6"
$tkDir = Join-Path $tclBase "tk8.6"
$pyLib = (& $venvPython -c "import sys, os; print(os.path.join(sys.base_prefix, 'Lib'))")
$encDir = Join-Path $pyLib "encodings"
$addDataArgs = @()
if (Test-Path $tclDir) { $addDataArgs += @('--add-data', "${tclDir};tcl\\tcl8.6") }
if (Test-Path $tkDir) { $addDataArgs += @('--add-data', "${tkDir};tcl\\tk8.6") }
if (Test-Path $encDir) { $addDataArgs += @('--add-data', "${encDir};encodings") }

Write-Host "[Build] Running PyInstaller" -ForegroundColor Cyan
$entry = Join-Path "src" "main.py"
$distDir = "dist"
$buildDir = "build"
if (-not (Test-Path $distDir)) { New-Item -ItemType Directory -Path $distDir | Out-Null }
if (-not (Test-Path $buildDir)) { New-Item -ItemType Directory -Path $buildDir | Out-Null }

# Use module invocation to be robust across platforms
$rtDir = Join-Path $env:LOCALAPPDATA "$AppName\runtime"
if (-not (Test-Path $rtDir)) { New-Item -ItemType Directory -Path $rtDir -Force | Out-Null }

$args = @('--windowed', '--name', $AppName, '--distpath', $distDir, '--workpath', $buildDir,
  '--hidden-import', 'tkinter', '--collect-all', 'tkinter', '--hidden-import', 'encodings', '--collect-submodules', 'encodings',
  '--hidden-import', 'src', '--hidden-import', 'src.youtube_app', '--hidden-import', 'src.config_manager', '--hidden-import', 'src.playlist',
  '--hidden-import', 'src.pages.setup_page', '--hidden-import', 'src.pages.main.main_page', '--collect-all', 'src', '--collect-submodules', 'src', '--paths', 'src',
  '--hidden-import', 'googleapiclient', '--hidden-import', 'googleapiclient.discovery', '--hidden-import', 'googleapiclient.errors', '--hidden-import', 'googleapiclient.http',
  '--hidden-import', 'google.auth', '--hidden-import', 'google.oauth2', '--hidden-import', 'google.auth.transport.requests', '--hidden-import', 'google_auth_httplib2', '--hidden-import', 'httplib2', '--hidden-import', 'uritemplate',
  '--collect-submodules', 'googleapiclient', '--collect-submodules', 'google', '--collect-submodules', 'google_auth_httplib2')
if ($Mode -eq 'onefile') {
  $args += @('--onefile', '--runtime-tmpdir', $rtDir)
}
$args += $addDataArgs

& $venvPython -m PyInstaller @args $entry

if ($LASTEXITCODE -ne 0) {
  Write-Error "[Build] PyInstaller failed with exit code $LASTEXITCODE"
  exit $LASTEXITCODE
}

if ($Mode -eq 'onefile') {
  $exePath = Join-Path $distDir ("{0}.exe" -f $AppName)
  if (Test-Path $exePath) {
    Write-Host "[Build] Success: $exePath" -ForegroundColor Green
    $runnerCmd = Join-Path $distDir ("Run-{0}.cmd" -f $AppName)
    "@echo off" | Out-File -FilePath $runnerCmd -Encoding ascii -Force
    "setlocal" | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    "set PYTHONHOME=" | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    "set PYTHONPATH=" | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    "set PYTHONUSERBASE=" | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    "set PYTHONUTF8=1" | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    "set SSL_CERT_FILE=" | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    "set REQUESTS_CA_BUNDLE=" | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    "start \"\" \"%~dp0{0}.exe\"" -f $AppName | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    Write-Host "[Build] Runner created: $runnerCmd" -ForegroundColor Cyan
  } else {
    Write-Warning "[Build] Build finished but executable not found in $distDir"
  }
} else {
  $dirPath = Join-Path $distDir $AppName
  if (Test-Path $dirPath) {
    Write-Host "[Build] Success: $dirPath" -ForegroundColor Green
    $runnerCmd = Join-Path $dirPath "Run-App.cmd"
    "@echo off" | Out-File -FilePath $runnerCmd -Encoding ascii -Force
    "setlocal" | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    "set PYTHONHOME=" | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    "set PYTHONPATH=" | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    "set PYTHONUSERBASE=" | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    "set PYTHONUTF8=1" | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    "set SSL_CERT_FILE=" | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    "set REQUESTS_CA_BUNDLE=" | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    "pushd \"%~dp0\"" | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    "start \"\" \"%~dp0{0}.exe\"" -f $AppName | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    "popd" | Out-File -FilePath $runnerCmd -Encoding ascii -Append
    Write-Host "[Build] Runner created: $runnerCmd" -ForegroundColor Cyan
  } else {
    Write-Warning "[Build] Build finished but folder not found in $distDir"
  }
}
