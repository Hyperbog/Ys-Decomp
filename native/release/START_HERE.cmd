@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Ys SMS Native - Development Diagnostics (Not Gameplay)
if not exist "bin\ys-native-window.exe" (
    echo ERROR: Windows diagnostic executable not found.
    echo Extract the FULL ZIP before opening START_HERE.cmd.
    echo Do not run this file from inside a ZIP archive.
    echo Expected: bin\ys-native-window.exe next to this launcher.
    pause
    exit /b 1
)
:menu
cls
echo ================================================
echo   Ys SMS Native - Development Build
echo   HARDWARE TEST TOOLS, NOT A PLAYABLE PC GAME
echo ================================================
echo.
echo  1  OPEN VISUAL TEST WINDOW  [no game ROM required]
echo  2  Check native CPU/VBlank timing [no ROM]
echo  3  Trace your Ys SMS ROM and VIEW its VDP checkpoint
echo  4  Export a synthetic video image
echo  5  Show build information
echo  6  Exit
echo.
choice /C 123456 /N /M "Choose 1-6: "
if errorlevel 6 goto done
if errorlevel 5 goto info
if errorlevel 4 goto picture
if errorlevel 3 goto rom
if errorlevel 2 goto timing
if errorlevel 1 goto window
goto menu
:window
echo Starting the Windows graphics test ...
start "" "bin\ys-native-window.exe"
if errorlevel 1 echo Failed to launch window. Check Windows security and OS support.
echo Window shows synthetic SMS tile graphics, not Ys gameplay.
pause
goto menu
:timing
echo.
"bin\ys-native-timing.exe" --check > "last-diagnostic.txt" 2>&1
set "RESULT=%errorlevel%"
type "last-diagnostic.txt"
echo.
echo Exit code: %RESULT%   Log: last-diagnostic.txt
pause
goto menu
:rom
echo.
echo Enter the full path to your legally obtained Ys Master System ROM.
echo You can drag the file into this console window, then press Enter.
echo This expects a 256 KiB SMS ROM, NOT an NES ROM.
set "ROM="
set /p "ROM=ROM file: "
if not defined ROM goto menu
set "ROM=%ROM:"=%"
if not exist "%ROM%" (
    echo ERROR: File not found: "%ROM%"
    pause
    goto menu
)
if exist "checkpoint.ppm" del /q "checkpoint.ppm"
"bin\ys-native-timed-rom.exe" "%ROM%" --frame "checkpoint.ppm" > "last-diagnostic.txt" 2>&1
set "RESULT=%errorlevel%"
type "last-diagnostic.txt"
echo.
echo Exit code: %RESULT%   Log: last-diagnostic.txt
echo This is a verified tile-upload snapshot, NOT live Ys gameplay.
if "%RESULT%"=="0" if exist "checkpoint.ppm" (
    echo Opening the real cartridge VDP checkpoint in the Windows viewer.
    echo Its screen may be blank because game graphics are not yet initialized.
    start "" "bin\ys-native-window.exe" --ppm "checkpoint.ppm"
)
pause
goto menu
:picture
"bin\ys-native-preview.exe" "synthetic.ppm" > "last-diagnostic.txt" 2>&1
set "RESULT=%errorlevel%"
type "last-diagnostic.txt"
echo.
echo Exit code: %RESULT%   File: synthetic.ppm
pause
goto menu
:info
"bin\ys-native-info.exe" --help > "last-diagnostic.txt" 2>&1
set "RESULT=%errorlevel%"
type "last-diagnostic.txt"
echo.
echo Exit code: %RESULT%
pause
goto menu
:done
exit /b 0
