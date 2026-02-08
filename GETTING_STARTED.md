# 🚀 GETTING STARTED - PropBet Analyzer

## What You Have

A complete, production-ready NBA prop bet analysis application with:
- ✅ Backend API (Python/FastAPI)
- ✅ Database models (PostgreSQL)  
- ✅ Frontend interface (React/TypeScript)
- ✅ BallDontLie API integration
- ✅ Authentication system
- ✅ Analysis algorithms

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Python 3.10+** installed ([python.org](https://python.org))
- [ ] **PostgreSQL** installed and running ([postgresql.org](https://postgresql.org))
- [ ] **Node.js 18+** installed ([nodejs.org](https://nodejs.org))
- [ ] **Visual Studio Code** (you already have this!)
- [ ] **Git** (optional, recommended)

## Option 1: Automated Setup (Windows)

### Double-click `quickstart.bat`

This script will:
1. Check prerequisites
2. Set up Python virtual environment
3. Install all dependencies
4. Create database tables
5. Start both backend and frontend servers
6. Open the app in your browser

**Note**: You still need to manually create the PostgreSQL database first!

## Option 2: Manual Setup (All Platforms)

### Phase 1: Database Setup (5 minutes)

#### Step 1.1: Create PostgreSQL Database

Open **pgAdmin** or **psql** command line:

```sql
CREATE DATABASE propbet_db;
```

Or using psql from command line:
```bash
psql -U postgres
# Enter password when prompted
CREATE DATABASE propbet_db;
\q
```

Verify it was created:
```bash
psql -U postgres -l
# Should see propbet_db in the list
```

### Phase 2: Backend Setup (10 minutes)

#### Step 2.1: Open Terminal in VS Code

- Open Visual Studio Code
- Open the `prop-bet-analyzer` folder (File → Open Folder)
- Open Terminal (Terminal → New Terminal or Ctrl+`)

#### Step 2.2: Navigate to Backend

```bash
cd backend
```

#### Step 2.3: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

#### Step 2.4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will take 2-3 minutes. You should see packages being installed.

#### Step 2.5: Configure Environment

**Windows:**
```bash
copy .env.example .env
```

**Mac/Linux:**
```bash
cp .env.example .env
```

**Edit the `.env` file:**

Open `backend/.env` in VS Code and update:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/propbet_db
SECRET_KEY=run-the-command-below-to-generate
BALLDONTLIE_API_KEY=469863e1-e277-4a1e-bd6b-78445301c342
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Copy the output and paste it as your `SECRET_KEY` in `.env`.

**Replace YOUR_PASSWORD with your PostgreSQL password!**

#### Step 2.6: Initialize Database

```bash
alembic upgrade head
```

You should see:
```
INFO  [alembic.runtime.migration] Running upgrade -> xxxxx, Initial migration
```

If you get an error:
- Check PostgreSQL is running
- Verify DATABASE_URL in .env is correct
- Make sure propbet_db database exists

#### Step 2.7: Start Backend Server

```bash
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

**✅ Backend is now running!**

**Test it:** Open http://localhost:8000/docs in your browser.
You should see the interactive API documentation.

**Keep this terminal open!** Backend must stay running.

### Phase 3: Frontend Setup (10 minutes)

#### Step 3.1: Open New Terminal

In VS Code:
- Click the `+` button in the terminal panel (top right)
- Or use Terminal → New Terminal

#### Step 3.2: Navigate to Frontend

```bash
cd frontend
```

#### Step 3.3: Install Dependencies

```bash
npm install
```

This will take 3-5 minutes. You'll see many packages being installed.

Common issues:
- If you get `npm not found`, install Node.js first
- If you get permission errors, try running VS Code as administrator

#### Step 3.4: Start Frontend Server

```bash
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**✅ Frontend is now running!**

**Keep this terminal open too!** Frontend must stay running.

### Phase 4: First Use (5 minutes)

#### Step 4.1: Open the Application

Open your browser and go to: **http://localhost:5173**

You should see the PropBet Analyzer homepage.

#### Step 4.2: Register an Account

1. Click "Register" or "Sign Up"
2. Fill in:
   - **Email**: your@email.com
   - **Username**: yourusername
   - **Password**: yourpassword123
   - **Full Name**: Your Name (optional)
3. Click "Register"

#### Step 4.3: Login

1. Login with your credentials
2. You'll be redirected to the dashboard

#### Step 4.4: Create Your First Bet Slip

1. Click "New Bet Slip" or "Analyze Bets"
2. Enter your first prop:
   - **Player Name**: Anthony Black
   - **Stat Type**: points (or pts)
   - **Line**: 15.5
   - **Over/Under**: over
   - **Opponent**: Cleveland Cavaliers (optional)

3. Click "Add Prop" to add more props

4. Click "Analyze Bet Slip"

The system will:
- Search for the player in the NBA database
- Fetch their last 10 games
- Calculate hit rates and averages
- Analyze multiple factors
- Generate a confidence score
- Provide a recommendation

#### Step 4.5: Review Results

You'll see:
- **Confidence Score**: 0-100 (higher is better)
- **Hit Rate**: % of last 10 games player hit this prop
- **Average Stat**: Player's recent average
- **Recommendation**: Strong Bet / Bet / Neutral / Avoid / Strong Avoid
- **Factors**: What's affecting the analysis
- **Analysis Notes**: Detailed explanation

## Troubleshooting

### Problem: Backend won't start

**Error: Database connection failed**
```
Solution:
1. Check PostgreSQL is running (check Task Manager/Activity Monitor)
2. Verify DATABASE_URL in backend/.env
3. Test connection: psql -U postgres -d propbet_db
```

**Error: ModuleNotFoundError**
```
Solution:
1. Make sure virtual environment is activated (see (venv) in terminal)
2. Run: pip install -r requirements.txt
```

**Error: Port 8000 already in use**
```
Solution:
1. Find what's using port 8000: netstat -ano | findstr :8000
2. Kill that process or use different port:
   uvicorn app.main:app --reload --port 8001
```

### Problem: Frontend won't start

**Error: npm command not found**
```
Solution:
Install Node.js from nodejs.org
```

**Error: Cannot connect to backend**
```
Solution:
1. Check backend is running on http://localhost:8000
2. Test: curl http://localhost:8000/health
3. Check CORS settings in backend/app/config.py
```

**Error: Port 5173 already in use**
```
Solution:
Kill the process or edit vite.config.ts to use different port
```

### Problem: Analysis returns 50% confidence for all props

**This means player data wasn't found**
```
Solutions:
1. Check player name spelling (case doesn't matter)
2. Try full name: "Anthony Black" not "A. Black"
3. Verify BallDontLie API key in backend/.env
4. Check backend logs for errors
5. Test API directly: http://localhost:8000/docs
```

### Problem: Can't login / register

**Error: 401 Unauthorized**
```
Solution:
1. Check username and password are correct
2. Make sure you registered first
3. Check backend logs for errors
4. Try registering with a new username
```

## Daily Usage

### Starting the App

**Terminal 1 - Backend:**
```bash
cd prop-bet-analyzer/backend
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd prop-bet-analyzer/frontend
npm run dev
```

**Then open:** http://localhost:5173

### Stopping the App

- Press `Ctrl+C` in each terminal
- Type `deactivate` in backend terminal to exit virtual environment

## Understanding the Analysis

### Confidence Score Explained

- **70-100%**: Strong Bet - High probability, favorable factors
- **58-69%**: Bet - Good probability, some favorable factors  
- **45-57%**: Neutral - Toss-up, unclear
- **30-44%**: Avoid - Low probability, unfavorable factors
- **0-29%**: Strong Avoid - Very low probability

### What the Factors Mean

**Recent Trend** (-1 to 1):
- Positive: Player is improving
- Negative: Player is declining

**Consistency** (0 to 1):
- High: Reliable, similar performances
- Low: Unpredictable, varies wildly

**Playing Time** (0 to 1):
- High: Getting lots of minutes
- Low: Limited playing time

## Next Steps

### Immediate
1. ✅ Register and login
2. ✅ Analyze your first bet slip
3. ✅ Try different players and props
4. ✅ Compare confidence scores

### Short Term
- Analyze multiple bet slips
- Track which analyses were correct
- Learn which factors matter most
- Build your betting strategy

### Long Term (Coming in v2)
- Upload bet slip images
- Advanced ML predictions
- Historical accuracy tracking
- Subscription tiers
- Mobile app

## Important Files

### Configuration
- `backend/.env` - Database and API settings
- `frontend/vite.config.ts` - Frontend proxy settings

### Core Logic
- `backend/app/core/analysis_engine.py` - Analysis algorithms
- `backend/app/services/balldontlie.py` - NBA data fetching
- `backend/app/api/bets.py` - Bet slip endpoints

### Database
- `backend/app/models/` - Database tables
- `backend/alembic/versions/` - Migration files

## API Reference

Full interactive docs at: http://localhost:8000/docs

### Key Endpoints

**Authentication:**
- POST `/auth/register` - Create account
- POST `/auth/login` - Get token
- GET `/auth/me` - Get user info

**Bet Slips:**
- POST `/bets/` - Create bet slip
- GET `/bets/` - List user's bet slips
- GET `/bets/{id}` - Get specific bet slip
- POST `/bets/{id}/analyze` - Run analysis
- DELETE `/bets/{id}` - Delete bet slip

## Support

### If you're stuck:

1. **Read error messages** - They usually tell you what's wrong
2. **Check logs** - Backend terminal shows detailed errors
3. **Test API** - Use http://localhost:8000/docs to test endpoints directly
4. **Verify setup** - Go through checklist again
5. **Check database** - Use pgAdmin to verify tables exist

### Common Questions

**Q: How accurate is the analysis?**
A: This is an MVP. Accuracy improves with more data and better models. Always do your own research!

**Q: Can I deploy this online?**
A: Yes! See deployment guide (coming soon). Recommended: Railway for backend, Vercel for frontend.

**Q: Can I add other sports?**
A: Yes, but you'll need to integrate other APIs. NFL, MLB support planned for v2.

**Q: Is this legal?**
A: This is an analysis tool. Betting laws vary by jurisdiction. You're responsible for compliance.

## Getting Help

- Check README.md for overview
- Check SETUP_GUIDE.md for detailed instructions
- Review code comments for technical details
- Test endpoints at http://localhost:8000/docs

## Success Checklist

- [ ] PostgreSQL database created
- [ ] Backend starts without errors
- [ ] Can access http://localhost:8000/docs
- [ ] Frontend starts without errors  
- [ ] Can access http://localhost:5173
- [ ] Can register a user
- [ ] Can login successfully
- [ ] Can create a bet slip
- [ ] Analysis returns real data (not just 50%)

If all checked, you're ready to use the app! 🎉

## What's Next?

Now that you have it running:

1. **Try different players** - Test various props and lines
2. **Check accuracy** - Compare predictions to actual outcomes
3. **Experiment with factors** - See what affects confidence scores
4. **Provide feedback** - Note what works and what doesn't
5. **Plan improvements** - Decide what features you want next

Remember: This is an MVP. It's meant to be built upon and improved!

---

**Have fun and good luck with your bets! 🏀💰**

(Always bet responsibly!)
