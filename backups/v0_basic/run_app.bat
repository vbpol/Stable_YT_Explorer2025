@echo off
setlocal

:: Get the directory where the batch file is located
set "APP_ROOT=%~dp0"
set "VENV_DIR=%APP_ROOT%venv"

:: Activate virtual environment and run the app
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment
    exit /b 1
)

:: Run the application as a module
python -m src.main
if errorlevel 1 (
    echo Application exited with error
    exit /b 1
)

:: Deactivate virtual environment
call "%VENV_DIR%\Scripts\deactivate.bat"

endlocal
