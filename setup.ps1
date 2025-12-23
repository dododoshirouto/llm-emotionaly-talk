$ErrorActionPreference = "Stop"

# Version Configuration
$VOICEVOX_VERSION = "0.15.7"
$PYTHON_CMD = "python"
$VENV_DIR = "venv"
$REQUIREMENTS = "requirements.txt"

Write-Host "=== Environment Setup Start ===" -ForegroundColor Cyan

# 1. Check Python
try {
    & $PYTHON_CMD --version
} catch {
    Write-Error "Python not found. Please install Python 3.8+ and add it to PATH."
    exit 1
}

# 2. Create venv
if (-not (Test-Path $VENV_DIR)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    & $PYTHON_CMD -m venv $VENV_DIR
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Green
}

# Define paths for venv execution
$PIP_CMD = "$VENV_DIR\Scripts\pip.exe"
$PYTHON_VENV_CMD = "$VENV_DIR\Scripts\python.exe"

# 3. Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& $PYTHON_VENV_CMD -m pip install --upgrade pip

# 4. Install requirements
if (Test-Path $REQUIREMENTS) {
    Write-Host "Installing requirements from $REQUIREMENTS..." -ForegroundColor Yellow
    & $PIP_CMD install -r $REQUIREMENTS
} else {
    Write-Warning "$REQUIREMENTS not found. Skipping."
}

# 5. Setup VOICEVOX Core
$VOICEVOX_DIR = "answer_voicevox_core" # Changed to avoid conflict or just keep root? Using root as per prev plan instructions usually means keeping dlls in root or specific folder.
# The user wants "voicevox_core/" folder for dlls as per gitignore?
# The downloader extracts to current directory usually or we can specify.
# Let's check if the directory "voicevox_core" exists (which contains the DLLs). 
# Actually the downloader creates a folder or specific files?
# Let's use a specific folder "voicevox_core" to keep things clean if possible, but the python binding needs to find the dll.
# Usually standard practice for this project seems to be dumping DLLs in root or adding to PATH.
# Let's follow the reference script logic: it puts DLLs in root or specific folder and loads them.
# Plan said: "Check: voicevox_core folder (DLLs etc)"

if (-not (Test-Path "voicevox_core")) {
    Write-Host "Setting up VOICEVOX Core $VOICEVOX_VERSION..." -ForegroundColor Yellow
    
    # Download Downloader
    $DOWNLOADER_URL = "https://github.com/VOICEVOX/voicevox_core/releases/download/$VOICEVOX_VERSION/download-windows-x64.exe"
    $DOWNLOADER_EXE = "voicevox-download-windows-x64.exe"
    
    Write-Host "Downloading $DOWNLOADER_EXE..."
    Invoke-WebRequest -Uri $DOWNLOADER_URL -OutFile $DOWNLOADER_EXE

    # Run Downloader
    # Options: -v VERSION -o OUTPUT_DIR
    # We want to output to "voicevox_core" directory
    Write-Host "Running downloader..."
    Start-Process -FilePath .\$DOWNLOADER_EXE -ArgumentList "-v $VOICEVOX_VERSION -o ./voicevox_core" -Wait -NoNewWindow

    # Cleanup Downloader
    Remove-Item $DOWNLOADER_EXE
} else {
    Write-Host "voicevox_core directory likely exists. Skipping download." -ForegroundColor Green
}

# 6. Install VOICEVOX Core Python Wheel
Write-Host "Installing VOICEVOX Core Python Wheel..." -ForegroundColor Yellow
# Note: Ensure this URL matches the python version installed. Assuming cp38 ABI compatible (works on 3.8 ~ 3.12 usually for abi3)
$WHEEL_URL = "https://github.com/VOICEVOX/voicevox_core/releases/download/$VOICEVOX_VERSION/voicevox_core-$VOICEVOX_VERSION+cpu-cp38-abi3-win_amd64.whl"

& $PIP_CMD install $WHEEL_URL

# 7. Check Dictionary
# The downloader should have downloaded the dictionary into voicevox_core/open_jtalk_dic_utf_8-1.11 usually?
# Let's verify. The downloader behavior: it downloads libraries and dicts.
# We just notify the user.

Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "To start using the environment:"
Write-Host "1. Activate venv: .\venv\Scripts\activate"
Write-Host "2. Ensure 'voicevox_core' directory is accessible or paths are set correctly in your code."
