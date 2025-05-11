# --- Configuration ---
$PythonExe = "python"
$VenvDirName = ".venv" # Relative to script location
$RequirementsFileName = "requirements.txt" # Relative to script location

# --- Resolve Absolute Paths ---
# $PSScriptRoot is an automatic variable holding the directory of the script
$ScriptDir = $PSScriptRoot
$VenvDir = Join-Path $ScriptDir $VenvDirName
$RequirementsFile = Join-Path $ScriptDir $RequirementsFileName
$VenvActivateBat = Join-Path $VenvDir "Scripts" "activate.bat"
$VenvActivatePs1 = Join-Path $VenvDir "Scripts" "Activate.ps1" # For PowerShell-internal activation

# --- Helper Functions ---
function Check-Python {
    Write-Host "Checking for Python..."
    & $PythonExe --version *>&1 | Out-Null # Suppress stdout and stderr
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Python is not installed or not found in PATH."
        Write-Warning "Please install Python 3.7+ and ensure it's added to your PATH."
        Write-Warning "https://www.python.org/downloads/"
        return $false
    }
    Write-Host "Python found."
    return $true
}

function Create-Venv {
    Write-Host "Creating virtual environment in $VenvDir..."
    & $PythonExe -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment."
        return $false
    }
    Write-Host "Virtual environment created."
    return $true
}

function Install-Requirements {
    Write-Host "Activating virtual environment and installing requirements..."

    if (-not (Test-Path $VenvActivatePs1)) {
        Write-Error "PowerShell activation script not found: $VenvActivatePs1"
        Write-Error "The virtual environment might be incomplete or not created correctly for PowerShell."
        # The batch script relies on activate.bat. If Activate.ps1 is missing, it's a problem for this PS function.
        return $false
    }

    # Try to activate using PowerShell's own activation script
    try {
        . $VenvActivatePs1 # Dot-source to run in current scope
    }
    catch {
        Write-Error "Failed to activate virtual environment $VenvDir using $VenvActivatePs1."
        # Deactivation is not applicable/safe if activation itself failed.
        return $false
    }
    
    # Now pip should be in path (or an alias/function)
    pip install -r $RequirementsFile
    $pipInstallErrorLevel = $LASTEXITCODE

    # Always attempt to deactivate
    Write-Host "Deactivating virtual environment (it will be activated by individual script runners)."
    try {
        deactivate # This function is defined by Activate.ps1
    }
    catch {
        Write-Warning "Warning: Failed to deactivate virtual environment. The 'deactivate' command might not be available or failed."
    }

    if ($pipInstallErrorLevel -ne 0) {
        Write-Error "Failed to install requirements from $RequirementsFile. (Errorlevel: $pipInstallErrorLevel)"
        return $false
    }

    Write-Host "Requirements installed successfully."
    return $true
}

# --- Main Script ---
Write-Host "Starting LCMimicry Suite Setup..."

if (-not (Check-Python)) {
    exit 1
}

# Check for existence of activate.bat as the original script does for its primary check
if (-not (Test-Path $VenvActivateBat)) {
    Write-Host "Virtual environment activation script ($VenvActivateBat) not found."
    if (-not (Create-Venv)) {
        exit 1
    }
    if (-not (Install-Requirements)) {
        exit 1
    }
} else {
    Write-Host "Virtual environment $VenvDirName already exists."
    Write-Host "Ensuring requirements are up-to-date..."
    if (-not (Install-Requirements)) {
        exit 1
    }
}

Write-Host ""
Write-Host "Setup complete."
Write-Host ""
Write-Host "Launching Python scripts in new windows..."
Write-Host "Please ensure your .env file is configured in the main package directory (this directory: $ScriptDir)."
Write-Host "You can close this window once the new script windows have appeared."
Write-Host ""

# Launch voice_model2.py in a new window
$script1Path = Join-Path $ScriptDir "voice_model2.py"
$script1Title = "Voice Model Processor"
$command1 = "call `"$VenvActivateBat`" && echo Activating venv for $script1Title... && $PythonExe `"$script1Path`" && echo $script1Title finished. && pause"
Start-Process cmd -ArgumentList "/k title `"$script1Title`" && $command1"

# Launch ingame_llm_tts.py in a new window
$script2Path = Join-Path $ScriptDir "ingame_llm_tts.py"
$script2Title = "In-Game LLM TTS"
$command2 = "call `"$VenvActivateBat`" && echo Activating venv for $script2Title... && $PythonExe `"$script2Path`" && echo $script2Title finished. && pause"
Start-Process cmd -ArgumentList "/k title `"$script2Title`" && $command2"

Write-Host ""
Write-Host "Scripts launched. Check the new command prompt windows for output."

# No endlocal equivalent needed as PowerShell handles scope differently.
# Script will exit with 0 by default if no 'exit X' with X > 0 was called.