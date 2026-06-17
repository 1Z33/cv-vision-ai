@echo off
cd /d %~dp0

set ALEMBIC_DATABASE_URL=sqlite:///./cv_vision_ai.db

alembic -c alembic.ini.dev upgrade head

echo.
echo === alembic current (dev) ===
alembic -c alembic.ini.dev current

echo.
echo === SQLite schema interview_sessions ===
sqlite3 cv_vision_ai.db ".schema interview_sessions"

echo.
echo === Migration dev terminee ===
pause

