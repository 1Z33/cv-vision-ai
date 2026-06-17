@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python fix_db.py
pause

