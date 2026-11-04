@echo off
setlocal
cd /d "%~dp0"
if not exist .venv (python -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python seed_demo.py
echo.
echo Student: student@demo.edu / StudentDemo123!
echo Admin: admin@demo.edu / AdminDemo123!
echo Open http://127.0.0.1:8000 in your browser.
echo Press CTRL+C to stop the server.
uvicorn app:app --host 127.0.0.1 --port 8000
pause
