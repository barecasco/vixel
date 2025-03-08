@echo off
setlocal

REM Check if an argument was provided
if "%~1"=="" (
    echo Error: Please provide a Python script name as an argument
    echo Usage: %0 script_name
    echo Example: %0 hello
    exit /b 1
)

REM Check if the Python script exists
if not exist "script/%~1.py" (
    echo Error: Python script '%~1.py' not found
    exit /b 1
)

REM Execute the Python script
python "script/%~1.py"

REM Check if Python execution was successful
if errorlevel 1 (
    echo Error: Python script execution failed
    exit /b 1
)

exit /b 0