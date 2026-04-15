@echo off
echo Starting Face Swap server...
echo Open http://127.0.0.1:8000 in your browser.
uvicorn server:app --reload --port 8000
pause
