@echo off
echo ========================================================
echo  Syncing Updates to Streamlit Cloud (GitHub)
echo ========================================================

:: Check if git is initialized
if not exist .git (
    echo Error: This folder is not a git repository yet.
    echo Please follow the README instructions to 'git init' and connect to GitHub first.
    pause
    exit /b
)

echo Adding all changes...
git add .

echo Committing changes...
set /p commit_msg="Enter update message (e.g., 'Update logic'): "
if "%commit_msg%"=="" set commit_msg="Update by Antigravity"
git commit -m "%commit_msg%"

echo Pushing to GitHub...
git push -f -u origin main

echo ========================================================
echo  Done! Streamlit Cloud will auto-update in ~1-2 mins.
echo ========================================================
pause
