# PropBet Analyzer - Setup Guide

## Prerequisites

1. **Python 3.10+** installed
2. **PostgreSQL** installed and running
3. **Visual Studio Code** (already have)
4. **Git** (optional but recommended)

## Part 1: Database Setup

### Step 1: Create PostgreSQL Database

Open **pgAdmin** or **psql** command line and run:

```sql
CREATE DATABASE propbet_db;
CREATE USER propbet_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE propbet_db TO propbet_user;
```

Or using psql command line:
```bash
psql -U postgres
CREATE DATABASE propbet_db;
\q
```

## Part 2: Backend Setup

### Step 2: Navigate to Backend Directory

Open terminal in VS Code (Terminal → New Terminal) and run:

```bash
cd prop-bet-analyzer/backend
```

### Step 3: Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install all required packages (FastAPI, SQLAlchemy, etc.)

### Step 5: Configure Environment Variables

1. Copy `.env.example` to `.env`:
```bash
# On Windows:
copy .env.example .env

# On macOS/Linux:
cp .env.example .env
```

2. Edit `.env` file in VS Code and update:
```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/propbet_db
SECRET_KEY=generate-a-random-secret-key-here
BALLDONTLIE_API_KEY=469863e1-e277-4a1e-bd6b-78445301c342
```

**Important:** To generate a secure SECRET_KEY, run:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Copy the output and paste it as your SECRET_KEY.

### Step 6: Initialize Database with Alembic

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Run migrations to create tables
alembic upgrade head
```

If you encounter any errors, ensure:
- PostgreSQL is running
- Database credentials in `.env` are correct
- You're in the `backend` directory

### Step 7: Start the Backend Server

```bash
# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 8: Test the Backend

Open your browser and go to:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

You should see the interactive API documentation!

## Part 3: Frontend Setup

### Step 9: Open New Terminal

Keep the backend terminal running. Open a new terminal in VS Code:
- Click the `+` button in the terminal panel
- Or use Terminal → New Terminal

### Step 10: Navigate to Frontend Directory

```bash
cd prop-bet-analyzer/frontend
```

### Step 11: Install Node.js Dependencies

```bash
npm install
```

This will install React, Vite, and all frontend dependencies.

### Step 12: Start Frontend Development Server

```bash
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Step 13: Access the Application

Open your browser and go to: **http://localhost:5173**

You should see the PropBet Analyzer interface!

## Part 4: Using the Application

### Step 14: Register a User

1. Go to http://localhost:5173
2. Click "Register" or "Sign Up"
3. Enter your details:
   - Email
   - Username
   - Password
   - Full Name (optional)
4. Click "Register"

### Step 15: Login

1. Login with your credentials
2. You'll be redirected to the dashboard

### Step 16: Create Your First Bet Slip

1. Click "New Bet Slip" or "Analyze Bets"
2. Add prop bets manually:
   - **Player Name**: Anthony Black
   - **Stat Type**: points
   - **Line**: 15
   - **Over/Under**: over
   - **Opponent**: Cleveland Cavaliers
3. Add more props (Coby White, Jaren Jackson Jr., etc.)
4. Click "Analyze"

The app will:
- Fetch player data from BallDontLie API
- Analyze recent performance
- Calculate hit rates
- Provide confidence scores
- Recommend which bets to take

## Troubleshooting

### Backend Issues

**Problem**: Database connection error
```
Solution: Check PostgreSQL is running and credentials in .env are correct
```

**Problem**: Module not found error
```bash
Solution: Make sure virtual environment is activated
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
```

**Problem**: Port 8000 already in use
```bash
Solution: Use a different port
uvicorn app.main:app --reload --port 8001
# Then update frontend API URL
```

### Frontend Issues

**Problem**: Connection refused to backend
```
Solution: Ensure backend is running on http://localhost:8000
Check the API_URL in frontend code matches backend port
```

**Problem**: CORS errors
```
Solution: Backend CORS settings in config.py should include http://localhost:5173
Check CORS_ORIGINS in .env file
```

## Development Workflow

### Daily Startup

1. **Terminal 1** (Backend):
```bash
cd prop-bet-analyzer/backend
venv\Scripts\activate  # or source venv/bin/activate
uvicorn app.main:app --reload
```

2. **Terminal 2** (Frontend):
```bash
cd prop-bet-analyzer/frontend
npm run dev
```

### Stopping the Servers

- Press `CTRL+C` in each terminal
- Deactivate virtual environment: `deactivate`

## Next Steps

### Phase 2 Features (Future)

1. **Image Upload for Bet Slips**
   - OCR integration
   - Automatic prop parsing

2. **Advanced Analytics**
   - Machine learning predictions
   - Historical accuracy tracking

3. **User Features**
   - Subscription tiers
   - Bet slip sharing
   - Performance tracking

4. **Deployment**
   - Deploy backend to Railway/Render
   - Deploy frontend to Vercel
   - Production database setup

## Project Structure

```
prop-bet-analyzer/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Business logic
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # External services
│   │   ├── utils/        # Utilities
│   │   ├── config.py     # Configuration
│   │   ├── database.py   # Database connection
│   │   └── main.py       # FastAPI app
│   ├── alembic/          # Database migrations
│   ├── .env              # Environment variables
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API client
│   │   └── App.tsx       # Main app
│   └── package.json      # Node dependencies
└── README.md
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get token
- `GET /auth/me` - Get current user info

### Bet Slips
- `POST /bets/` - Create new bet slip
- `GET /bets/` - Get user's bet slips
- `GET /bets/{id}` - Get specific bet slip
- `POST /bets/{id}/analyze` - Analyze bet slip
- `DELETE /bets/{id}` - Delete bet slip

## Support

For issues or questions:
1. Check this README
2. Review error logs in terminal
3. Test API endpoints at http://localhost:8000/docs
4. Check database connection
5. Verify all environment variables are set correctly

## License

MIT License - Free to use and modify
