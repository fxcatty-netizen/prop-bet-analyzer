@echo off
echo ================================
echo PropBet Analyzer - Quick Start
echo ================================
echo.

echo Step 1: Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.10 or higher.
    pause
    exit /b 1
)

echo.
echo Step 2: Checking PostgreSQL...
psql --version
if errorlevel 1 (
    echo WARNING: PostgreSQL command line tools not found.
    echo Make sure PostgreSQL is installed and running.
    echo.
)

echo.
echo Step 3: Setting up Backend...
cd backend

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Step 4: Creating .env file...
if not exist .env (
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit backend\.env file and set your DATABASE_URL!
    echo Example: DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/propbet_db
    echo.
    pause
)

echo.
echo Step 5: Setting up database...
echo Make sure you've created the propbet_db database in PostgreSQL!
echo Run this in psql: CREATE DATABASE propbet_db;
echo.
pause

echo Running database migrations...
alembic upgrade head

if errorlevel 1 (
    echo.
    echo ERROR: Database migration failed!
    echo Please check:
    echo  1. PostgreSQL is running
    echo  2. Database propbet_db exists  
    echo  3. DATABASE_URL in .env is correct
    echo.
    pause
    exit /b 1
)

echo.
echo Step 6: Starting backend server...
echo Backend will start at http://localhost:8000
echo API Docs at http://localhost:8000/docs
echo.
echo Keep this window open!
echo.

start cmd /k "cd /d %cd% && venv\Scripts\activate && uvicorn app.main:app --reload"

echo.
echo Step 7: Setting up Frontend...
cd ..\frontend

echo Installing Node dependencies...
call npm install

if errorlevel 1 (
    echo.
    echo ERROR: npm install failed!
    echo Please make sure Node.js is installed.
    pause
    exit /b 1
)

echo.
echo Step 8: Starting frontend...
echo Frontend will start at http://localhost:5173
echo.
echo A new window will open for the frontend.
echo.

start cmd /k "cd /d %cd% && npm run dev"

echo.
echo ================================
echo   Setup Complete!
echo ================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Next steps:
echo 1. Open http://localhost:5173 in your browser
echo 2. Register a new account
echo 3. Start analyzing bet slips!
echo.
echo Press any key to open the app in your browser...
pause > nul

start http://localhost:5173

pause
