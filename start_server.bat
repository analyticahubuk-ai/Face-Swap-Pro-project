@echo off
echo Starting Face Swap server in virtual environment...
echo Open http://127.0.0.1:8000 in your browser.
.venv\Scripts\uvicorn.exe server:app --host 127.0.0.1 --port 8000
pause
