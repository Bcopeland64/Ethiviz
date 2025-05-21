@echo off
REM EthiViz - Setup Script for Windows
REM Creates a virtual environment and installs all dependencies

echo.
echo  -------------------------------------------------------------------------------
echo  ███████╗████████╗██╗  ██╗██╗██╗   ██╗██╗███████╗
echo  ██╔════╝╚══██╔══╝██║  ██║██║██║   ██║██║╚══███╔╝
echo  █████╗     ██║   ███████║██║██║   ██║██║  ███╔╝ 
echo  ██╔══╝     ██║   ██╔══██║██║╚██╗ ██╔╝██║ ███╔╝  
echo  ███████╗   ██║   ██║  ██║██║ ╚████╔╝ ██║███████╗
echo  ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═╝╚══════╝
echo.                                                
echo  Cultural Bias Analysis Platform - Setup Script
echo  -------------------------------------------------------------------------------
echo.

echo This script will set up a virtual environment for EthiViz.
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.8+ and try again.
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYTHON_VERSION=%%I
echo Detected Python version: %PYTHON_VERSION%

REM Parse version
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

REM Ensure Python 3.8+
if %PYTHON_MAJOR% LSS 3 (
    echo Error: Python 3.8+ is required.
    echo Current version: %PYTHON_VERSION%
    exit /b 1
)
if %PYTHON_MAJOR% EQU 3 (
    if %PYTHON_MINOR% LSS 8 (
        echo Error: Python 3.8+ is required.
        echo Current version: %PYTHON_VERSION%
        exit /b 1
    )
)

REM Check if virtual environment exists
if exist venv (
    echo Virtual environment directory 'venv' already exists.
    set /p RECREATE="Do you want to remove it and create a new one? (y/n): "
    if /i "%RECREATE%"=="y" (
        echo Removing existing virtual environment...
        rmdir /s /q venv
        echo Existing environment removed.
    ) else (
        echo Using existing virtual environment.
    )
)

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment.
        exit /b 1
    )
    echo Virtual environment created successfully.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment.
    exit /b 1
)

REM Install requirements
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies.
    echo Please check the error messages above.
    exit /b 1
)

REM Install SpaCy model
echo Installing SpaCy language model...
python -m spacy download en_core_web_md
if errorlevel 1 (
    echo Warning: Failed to install SpaCy language model.
    echo You can try installing it manually with 'python -m spacy download en_core_web_md'
)

REM Optional dependencies
echo Checking for optional dependencies...

REM Check if TensorFlow is installed
python -c "import tensorflow" >nul 2>&1
if errorlevel 1 (
    echo TensorFlow not found. Advanced image analysis features will be limited.
    set /p INSTALL_TF="Do you want to install TensorFlow? (y/n): "
    if /i "%INSTALL_TF%"=="y" (
        echo Installing TensorFlow...
        pip install tensorflow
    ) else (
        echo Skipping TensorFlow installation.
    )
) else (
    echo TensorFlow is installed.
)

REM Check if OpenCV is installed
python -c "import cv2" >nul 2>&1
if errorlevel 1 (
    echo OpenCV not found. Medium-level image analysis features will be limited.
    set /p INSTALL_CV="Do you want to install OpenCV? (y/n): "
    if /i "%INSTALL_CV%"=="y" (
        echo Installing OpenCV...
        pip install opencv-python
    ) else (
        echo Skipping OpenCV installation.
    )
) else (
    echo OpenCV is installed.
)

REM Create activation script
echo Creating convenience activation script...
echo @echo off > activate-ethiviz.bat
echo call venv\Scripts\activate.bat >> activate-ethiviz.bat
echo echo EthiViz virtual environment activated! >> activate-ethiviz.bat
echo echo Run 'streamlit run app.py' to start the EthiViz application >> activate-ethiviz.bat

REM Success message
echo.
echo EthiViz setup completed successfully!
echo.
echo To activate the virtual environment in the future, run:
echo   activate-ethiviz.bat
echo.
echo To start the EthiViz application, run:
echo   streamlit run app.py
echo.
echo Happy analyzing!
echo.

REM Keep the window open
pause