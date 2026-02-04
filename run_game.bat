@echo off

setlocal enabledelayedexpansion

echo Starting the Flappy Bird Game...............

echo Activating the virtual environment...
call venv\Scripts\activate

echo Launching control.py in a new minimized window...
start "Control Script" /min cmd /k python "Source Code\control.py" 2>&1