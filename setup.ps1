$ErrorActionPreference = "Stop"

# Version Configuration
$VOICEVOX_VERSION = "0.15.7"
$PYTHON_CMD = "python"
$VENV_DIR = "venv"
$REQUIREMENTS = "requirements.txt"
$CORE_DIR = "voicevox_core"

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

$PIP_CMD = "$VENV_DIR\Scripts\pip.exe"
$PYTHON_VENV_CMD = "$VENV_DIR\Scripts\python.exe"

# 3. Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& $PYTHON_VENV_CMD -m pip install --upgrade pip

# 4. Install requirements
if (Test-Path $REQUIREMENTS) {
    Write-Host "Installing requirements from $REQUIREMENTS..." -ForegroundColor Yellow
    & $PIP_CMD install -r $REQUIREMENTS
}

# 5. Setup VOICEVOX Core (Manual Download)
if (-not (Test-Path $CORE_DIR)) {
    Write-Host "Setting up VOICEVOX Core $VOICEVOX_VERSION (Manual Download)..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $CORE_DIR | Out-Null

    # 5a. Download Core Libraries (Zip)
    $CORE_ZIP = "voicevox_core-windows-x64-cpu-$VOICEVOX_VERSION.zip"
    $CORE_URL = "https://github.com/VOICEVOX/voicevox_core/releases/download/$VOICEVOX_VERSION/$CORE_ZIP"
    
    if (-not (Test-Path $CORE_ZIP)) {
        Write-Host "Downloading Core Libraries from $CORE_URL..."
        Invoke-WebRequest -Uri $CORE_URL -OutFile $CORE_ZIP
    }
    
    Write-Host "Extracting Core Libraries..."
    Expand-Archive -Path $CORE_ZIP -DestinationPath "temp_core" -Force
    
    # Move contents to VOICEVOX_DIR
    # The zip usually contains a folder named like "voicevox_core-windows-x64-cpu-0.15.7"
    # We want the contents of that folder to be in $CORE_DIR
    $EXTRACTED_ROOT = Get-ChildItem -Path "temp_core" -Directory | Select-Object -First 1
    Copy-Item -Path "$($EXTRACTED_ROOT.FullName)\*" -Destination $CORE_DIR -Recurse -Force
    
    # Cleanup
    Remove-Item "temp_core" -Recurse -Force
    Remove-Item $CORE_ZIP
} else {
    Write-Host "voicevox_core directory exists. Skipping download." -ForegroundColor Green
}

# 6. Setup Dictionary (OpenJTalk)
$DICT_DIR = "$CORE_DIR\open_jtalk_dic_utf_8-1.11"
if (-not (Test-Path $DICT_DIR)) {
    Write-Host "Setting up OpenJTalk Dictionary..." -ForegroundColor Yellow
    
    # Using a stable mirror or direct link. 
    # Official Sourceforge is annoying for scripts (redirects). Github mirror from r9y9 is better.
    $DICT_TAR = "open_jtalk_dic_utf_8-1.11.tar.gz"
    $DICT_URL = "https://github.com/r9y9/open_jtalk/releases/download/v1.11.1/$DICT_TAR"
    
    if (-not (Test-Path $DICT_TAR)) {
        Write-Host "Downloading Dictionary from $DICT_URL..."
        Invoke-WebRequest -Uri $DICT_URL -OutFile $DICT_TAR
    }

    Write-Host "Extracting Dictionary..."
    # Windows native tar (if available) or rely on others. Windows 10+ has tar.
    # Note: PowerShell 5.1 might verify tar availability.
    tar -xf $DICT_TAR -C $CORE_DIR
    
    # Cleanup
    Remove-Item $DICT_TAR
} else {
    Write-Host "Dictionary directory exists." -ForegroundColor Green
}

# 7. Install VOICEVOX Core Python Wheel
Write-Host "Installing VOICEVOX Core Python Wheel..." -ForegroundColor Yellow
$WHEEL_URL = "https://github.com/VOICEVOX/voicevox_core/releases/download/$VOICEVOX_VERSION/voicevox_core-$VOICEVOX_VERSION+cpu-cp38-abi3-win_amd64.whl"

# Force reinstall to ensure deps are correct (sometimes conflicts leave mess)
& $PIP_CMD install --force-reinstall --no-deps $WHEEL_URL
# Re-install requirements to ensure they are satisfied
& $PIP_CMD install -r $REQUIREMENTS

Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "To start using the environment:"
Write-Host "1. Activate venv: .\venv\Scripts\activate"
Write-Host "2. voicevox_core libraries are in: $CORE_DIR"
