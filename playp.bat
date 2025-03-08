@echo off
setlocal enabledelayedexpansion

REM Usage: play_video_segment.bat input_file start_time end_time
REM Example: play_video_segment.bat video.mp4 00:01:30 00:02:45

REM Check if correct number of arguments provided
if "%~3"=="" (
    echo Usage: %0 input_file start_time end_time
    echo Times should be in format HH:MM:SS or SS
    exit /b 1
)

set "INPUT_FILE=%~1"
set "START_TIME=%~2"
set "END_TIME=%~3"

REM Check if input file exists
if not exist "%INPUT_FILE%" (
    echo Error: Input file '%INPUT_FILE%' does not exist.
    exit /b 1
)

REM Check if ffmpeg is in PATH
where ffmpeg >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: ffmpeg is not found in PATH. Please install it and add to PATH.
    exit /b 1
)

REM Check if ffplay is in PATH
where ffplay >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: ffplay is not found in PATH. Please install it and add to PATH.
    exit /b 1
)

REM Convert start and end times to seconds for duration calculation
for /f "tokens=*" %%a in ('powershell -Command "$start = '%START_TIME%'; if($start -match '^(\d+):(\d+):(\d+)$'){[int]$h=$matches[1]; [int]$m=$matches[2]; [int]$s=$matches[3]; $h*3600+$m*60+$s}elseif($start -match '^(\d+):(\d+)$'){[int]$m=$matches[1]; [int]$s=$matches[2]; $m*60+$s}else{[int]$start}"') do (
    set "start_seconds=%%a"
)

for /f "tokens=*" %%a in ('powershell -Command "$end = '%END_TIME%'; if($end -match '^(\d+):(\d+):(\d+)$'){[int]$h=$matches[1]; [int]$m=$matches[2]; [int]$s=$matches[3]; $h*3600+$m*60+$s}elseif($end -match '^(\d+):(\d+)$'){[int]$m=$matches[1]; [int]$s=$matches[2]; $m*60+$s}else{[int]$end}"') do (
    set "end_seconds=%%a"
)

REM Calculate duration in seconds
set /a duration_seconds=%end_seconds%-%start_seconds%

echo Playing segment from %START_TIME% to %END_TIME% (duration: %duration_seconds% seconds)

REM Play the video segment
ffplay -i "%INPUT_FILE%" -ss "%START_TIME%" -t %duration_seconds% -autoexit

exit /b 0