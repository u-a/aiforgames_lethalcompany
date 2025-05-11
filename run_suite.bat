
@echo off
setlocal

REM --- Configuration ---
set PYTHON_EXE=python
set VENV_DIR=.venv
set REQUIREMENTS_FILE=requirements.txt

REM --- Helper Functions ---
:check_python
echo Checking for Python...
%PYTHON_EXE% --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not found in PATH.
    echo Please install Python 3.7+ and ensure it's added to your PATH.
    echo https://www.python.org/downloads/
    exit /b 1
)
echo Python found.
exit /b 0

:create_venv
echo Creating virtual environment in %VENV_DIR%...
%PYTHON_EXE% -m venv %VENV_DIR%
if errorlevel 1 (
    echo Failed to create virtual environment.
    exit /b 1
)
echo Virtual environment created.
exit /b 0

:install_requirements
echo Activating virtual environment and installing requirements...
call .\%VENV_DIR%\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment .\%VENV_DIR%.
    REM Deactivation is not applicable/safe if activation itself failed.
    exit /b 1
)

pip install -r %REQUIREMENTS_FILE%
set "PIP_INSTALL_ERRORLEVEL=%errorlevel%"

REM Always attempt to deactivate, but the primary error status comes from pip.
echo Deactivating virtual environment (it will be activated by individual script runners).
call .\%VENV_DIR%\Scripts\deactivate.bat
if errorlevel 1 (
    echo Warning: Failed to deactivate .\%VENV_DIR%\Scripts\activate.bat.
)

if %PIP_INSTALL_ERRORLEVEL% neq 0 (
    echo Failed to install requirements from %REQUIREMENTS_FILE%. (Errorlevel: %PIP_INSTALL_ERRORLEVEL%)
    exit /b 1
)

echo Requirements installed successfully.
exit /b 0

REM --- Main Script ---
echo Starting LCMimicry Suite Setup...

call :check_python
if errorlevel 1 goto :eof

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    call :create_venv
    if errorlevel 1 goto :eof
    call :install_requirements
    if errorlevel 1 goto :eof
) else (
    echo Virtual environment %VENV_DIR% already exists.
    echo Ensuring requirements are up-to-date...
    call :install_requirements
    if errorlevel 1 goto :eof
)

echo.
echo Setup complete.
echo.
echo Launching Python scripts in new windows...
echo Please ensure your .env file is configured in the main package directory (this directory).
echo You can close this window once the new script windows have appeared.
echo.

REM Launch voice_model2.py in a new window
start "Voice Model Processor" cmd /k "call .\%VENV_DIR%\Scripts\activate.bat && echo Activating venv for Voice Model Processor... && %PYTHON_EXE% voice_model2.py && echo Voice Model Processor finished. && pause"

REM Launch ingame_llm_tts.py in a new window
start "In-Game LLM TTS" cmd /k "call .\%VENV_DIR%\Scripts\activate.bat && echo Activating venv for In-Game LLM TTS... && %PYTHON_EXE% ingame_llm_tts.py && echo In-Game LLM TTS finished. && pause"

echo.
echo Scripts launched. Check the new command prompt windows for output.

endlocal
