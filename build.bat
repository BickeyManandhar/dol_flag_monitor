@echo off
REM Build script for FLAG Monitor Lambda deployment (Windows)

echo ==========================================
echo Building FLAG Monitor Lambda Package
echo ==========================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python 3 is required but not installed.
    exit /b 1
)

echo Step 1: Creating Lambda function zip...

REM Clean up old builds
if exist build rmdir /s /q build
if exist lambda_function.zip del lambda_function.zip
if exist lambda_layer.zip del lambda_layer.zip

REM Create temporary directory for Lambda function
mkdir build\lambda

REM Copy Lambda function code (from same directory)
copy lambda_function.py build\lambda\

REM Create zip file for Lambda function
powershell -command "Compress-Archive -Path build\lambda\lambda_function.py -DestinationPath lambda_function.zip -Force"

echo [OK] Lambda function package created: lambda_function.zip

echo Step 2: Creating Lambda Layer with dependencies...

REM Create directory for layer
mkdir build\layer\python

REM Install dependencies (--no-user fixes the conflict)
pip install requests==2.31.0 beautifulsoup4==4.12.2 --target build\layer\python --no-user --upgrade --quiet

REM Create layer zip
powershell -command "Compress-Archive -Path build\layer\python -DestinationPath lambda_layer.zip -Force"

echo [OK] Lambda layer package created: lambda_layer.zip

REM Cleanup
rmdir /s /q build

echo.
echo ==========================================
echo Build Complete!
echo ==========================================
echo.
echo Created files:
echo   - lambda_function.zip (Lambda function code)
echo   - lambda_layer.zip (Dependencies: requests, beautifulsoup4)
echo.
echo Next steps:
echo   1. Configure terraform.tfvars with your email
echo   2. Run: terraform init
echo   3. Run: terraform plan
echo   4. Run: terraform apply
echo.