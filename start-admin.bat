@echo off
cd /d "%~dp0admin"
if not exist node_modules (
    echo Installazione dipendenze...
    npm install
)
npm run dev
pause
