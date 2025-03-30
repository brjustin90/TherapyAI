@echo off
REM Script to run Mental Health AI Therapy Web Application on Windows

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else if exist "..\.venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ..\.venv\Scripts\activate.bat
)

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python could not be found. Please install Python and try again.
    exit /b 1
)

REM Run the application
echo Starting Mental Health AI Therapy Web Application...
python run.py %* 