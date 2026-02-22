# Writing Studio Analytics - USB Copy Script
# Run this PowerShell script to copy everything to your USB drive
#
# Usage:
#   1. Plug in USB drive
#   2. Update $USB_DRIVE_LETTER below if needed
#   3. Right-click this file -> "Run with PowerShell"
#   Or run: powershell -ExecutionPolicy Bypass -File COPY_TO_USB.ps1

param(
    [string]$USB_DRIVE_LETTER = ""
)

# If no drive letter provided, prompt user
if ($USB_DRIVE_LETTER -eq "") {
    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host "  Writing Studio Analytics - USB Copy Tool" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Available drives:" -ForegroundColor Yellow
    Get-PSDrive -PSProvider FileSystem | Where-Object { $_.DriveType -eq "Removable" } | ForEach-Object {
        Write-Host "  $($_.Name): - $([math]::Round($_.Used/1GB, 2))GB used, $([math]::Round($_.Free/1GB, 2))GB free" -ForegroundColor White
    }
    Write-Host ""
    $USB_DRIVE_LETTER = Read-Host "Enter USB drive letter (e.g., E)"
}

# Clean up drive letter
$USB_DRIVE_LETTER = $USB_DRIVE_LETTER.TrimEnd(":", "\").ToUpper()

# Validate drive exists
if (-not (Test-Path "${USB_DRIVE_LETTER}:")) {
    Write-Host "[ERROR] Drive ${USB_DRIVE_LETTER}: not found!" -ForegroundColor Red
    Write-Host "Please check the drive letter and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check free space (need at least 5GB)
$drive = Get-PSDrive -Name $USB_DRIVE_LETTER
$freeGB = [math]::Round($drive.Free / 1GB, 2)
if ($drive.Free -lt 5GB) {
    Write-Host "[WARNING] Only $freeGB GB free on ${USB_DRIVE_LETTER}:" -ForegroundColor Yellow
    Write-Host "Recommended: 8GB+ for full package" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") { exit 0 }
}

# Set paths
$SOURCE_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($SOURCE_DIR -eq "") { $SOURCE_DIR = "." }
$DEST_DIR = "${USB_DRIVE_LETTER}:\WritingStudioAnalytics"

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  USB Copy Configuration" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Source: $SOURCE_DIR" -ForegroundColor White
Write-Host "  Destination: $DEST_DIR" -ForegroundColor White
Write-Host "  Free space: $freeGB GB" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$confirm = Read-Host "Proceed with copy? (y/n)"
if ($confirm -ne "y") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}

# Create destination directory
Write-Host ""
Write-Host "[1/8] Creating destination directory..." -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $DEST_DIR | Out-Null

# Copy root batch files and readme
Write-Host "[2/8] Copying launcher files..." -ForegroundColor Green
Copy-Item -Force "$SOURCE_DIR\START_PROGRAM.bat" $DEST_DIR
Copy-Item -Force "$SOURCE_DIR\README_FIRST.txt" $DEST_DIR
Copy-Item -Force "$SOURCE_DIR\setup_portable_python.bat" $DEST_DIR
Copy-Item -Force "$SOURCE_DIR\INSTALL_DEPENDENCIES.bat" $DEST_DIR
Copy-Item -Force "$SOURCE_DIR\RUN_WITH_PYTHON.bat" $DEST_DIR
Copy-Item -Force "$SOURCE_DIR\requirements-release.txt" $DEST_DIR

# Copy courses.csv if exists
if (Test-Path "$SOURCE_DIR\courses.csv") {
    Copy-Item -Force "$SOURCE_DIR\courses.csv" $DEST_DIR
}

# Copy executable (large file - takes longest)
Write-Host "[3/8] Copying executable (~3.5GB - this takes several minutes)..." -ForegroundColor Green
$exeSrc = "$SOURCE_DIR\dist\WritingStudioAnalytics.exe"
$exeDst = "$DEST_DIR\WritingStudioAnalytics.exe"

if (Test-Path $exeSrc) {
    # Use robocopy for large file with progress
    $exeSize = (Get-Item $exeSrc).Length / 1GB
    Write-Host "       File size: $([math]::Round($exeSize, 2)) GB" -ForegroundColor Gray
    Copy-Item -Force $exeSrc $exeDst
} else {
    Write-Host "[ERROR] Executable not found: $exeSrc" -ForegroundColor Red
    Write-Host "Please build the executable first: python build_executable.py" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Copy models folder
Write-Host "[4/8] Copying AI models..." -ForegroundColor Green
$modelsDest = "$DEST_DIR\models"
New-Item -ItemType Directory -Force -Path $modelsDest | Out-Null
Get-ChildItem -Path "$SOURCE_DIR\models" -File | ForEach-Object {
    if ($_.Extension -in @(".gguf", ".txt", ".md")) {
        Write-Host "       Copying $($_.Name)..." -ForegroundColor Gray
        Copy-Item -Force $_.FullName $modelsDest
    }
}

# Copy source code
Write-Host "[5/8] Copying source code..." -ForegroundColor Green
$srcDest = "$DEST_DIR\SOURCE_CODE"
New-Item -ItemType Directory -Force -Path $srcDest | Out-Null

# Copy src folder
Copy-Item -Recurse -Force "$SOURCE_DIR\src" $srcDest

# Copy tests folder
Copy-Item -Recurse -Force "$SOURCE_DIR\tests" $srcDest

# Copy docs folder
Copy-Item -Recurse -Force "$SOURCE_DIR\docs" $srcDest

# Copy requirements
Copy-Item -Force "$SOURCE_DIR\requirements-release.txt" $srcDest
Copy-Item -Force "$SOURCE_DIR\pytest.ini" $srcDest

# Copy additional docs to root
Write-Host "[6/8] Copying documentation..." -ForegroundColor Green
Copy-Item -Recurse -Force "$SOURCE_DIR\docs" $DEST_DIR

# Verify critical files
Write-Host "[7/8] Verifying copied files..." -ForegroundColor Green
$errors = @()

if (-not (Test-Path "$DEST_DIR\START_PROGRAM.bat")) { $errors += "START_PROGRAM.bat missing" }
if (-not (Test-Path "$DEST_DIR\WritingStudioAnalytics.exe")) { $errors += "WritingStudioAnalytics.exe missing" }
if (-not (Test-Path "$DEST_DIR\README_FIRST.txt")) { $errors += "README_FIRST.txt missing" }
if (-not (Test-Path "$DEST_DIR\models\gemma-3-4b-it-q4_0.gguf")) { $errors += "AI model file missing" }
if (-not (Test-Path "$DEST_DIR\SOURCE_CODE\src\dashboard\main.py")) { $errors += "Source code entry point missing" }

if ($errors.Count -gt 0) {
    Write-Host ""
    Write-Host "[WARNING] Some files may not have copied correctly:" -ForegroundColor Yellow
    $errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
} else {
    Write-Host "       All critical files verified!" -ForegroundColor Gray
}

# Calculate total size
Write-Host "[8/8] Calculating total size..." -ForegroundColor Green
$totalSize = (Get-ChildItem -Path $DEST_DIR -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1GB
Write-Host "       Total package size: $([math]::Round($totalSize, 2)) GB" -ForegroundColor Gray

# Summary
Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  COPY COMPLETE!" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Package location: $DEST_DIR" -ForegroundColor White
Write-Host "Total size: $([math]::Round($totalSize, 2)) GB" -ForegroundColor White
Write-Host ""
Write-Host "Next steps for supervisor:" -ForegroundColor Cyan
Write-Host "  1. Open the WritingStudioAnalytics folder" -ForegroundColor White
Write-Host "  2. Read README_FIRST.txt" -ForegroundColor White
Write-Host "  3. Double-click START_PROGRAM.bat" -ForegroundColor White
Write-Host ""
Write-Host "========================================================" -ForegroundColor Green

Read-Host "Press Enter to exit"