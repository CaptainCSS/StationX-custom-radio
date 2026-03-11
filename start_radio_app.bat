@echo off

:: 1. Open 'playit' in a new window
start "Playit" cmd /k "playit"

:: Define the project path to keep things clean
set PROJECT_DIR="C:\Users\colin\.gemini\antigravity\scratch\radio_app\broadcaster"

:: 2. Open Node server in the project folder
start "Node Server" cmd /k "cd /d %PROJECT_DIR% && npm start"

:: 3. Open Python app in the same project folder
start "Python App" cmd /k "cd /d %PROJECT_DIR% && python app.py"

exit