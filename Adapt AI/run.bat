@echo off
title AdaptAI - Personalised AI Tutor
echo ===================================================
echo Starting AdaptAI Server...
echo ===================================================

where py >nul 2>nul
if %errorlevel% equ 0 (
    py app.py
    goto end
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python app.py
    goto end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" app.py
    goto end
)

echo [ERROR] Python not found on your system!
pause

:end
