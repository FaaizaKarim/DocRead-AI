@echo off
echo Running ingestion...
call venv\Scripts\activate.bat
python -m app.ingest
pause
