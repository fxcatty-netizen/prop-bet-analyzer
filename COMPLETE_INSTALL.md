# 🚀 COMPLETE INSTALLATION GUIDE - PropBet Analyzer with Image Upload

## ⚡ Quick Overview

You now have a complete NBA prop bet analyzer with:
- ✅ Image upload for bet slips
- ✅ Claude AI OCR to extract props automatically
- ✅ Manual entry option
- ✅ Advanced analysis engine
- ✅ JWT authentication
- ✅ Modern React frontend

Let's get it running in 30 minutes!

---

## 📋 Prerequisites Check

Before starting, ensure you have:

### Required Software
- [ ] **Python 3.10 or higher** - Check with: `python --version`
- [ ] **PostgreSQL 14+** - Check with: `psql --version`
- [ ] **Node.js 18+** - Check with: `node --version`
- [ ] **Git** (recommended) - Check with: `git --version`

### Required Accounts/Keys
- [ ] **BallDontLie API Key**: `469863e1-e277-4a1e-bd6b-78445301c342` ✅ (Already configured)
- [ ] **Anthropic API Key**: Your Claude API key (for image upload feature)

### Where to get Anthropic API Key:
1. Go to https://console.anthropic.com
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy it (you'll need it in Step 2.5)

---

## 🎯 STEP-BY-STEP INSTALLATION

### PHASE 1: Database Setup (5 minutes)

#### Step 1.1: Start PostgreSQL

**Windows:**
- Open Services (search for "Services" in Start menu)
- Find "postgresql-x64-XX" service
- Right-click → Start

**Mac:**
```bash
brew services start postgresql@14
```

**Linux:**
```bash
sudo systemctl start postgresql
```

#### Step 1.2: Create Database

Open **pgAdmin** or command line:

**Using pgAdmin:**
1. Open pgAdmin
2. Connect to PostgreSQL
3. Right-click "Databases" → Create → Database
4. Name: `propbet_db`
5. Click Save

**Using Command Line (psql):**
```bash
# Windows (Command Prompt as Administrator)
psql -U postgres
# Enter your PostgreSQL password when prompted

# Mac/Linux
psql postgres

# Then run:
CREATE DATABASE propbet_db;
\q
```

#### Step 1.3: Verify Database

```bash
psql -U postgres -l
```

You should see `propbet_db` in the list!

---

### PHASE 2: Backend Setup (10 minutes)

#### Step 2.1: Open Terminal

**Option A: Command Prompt (Windows)**
1. Press `Win + R`
2. Type `cmd`
3. Press Enter

**Option B: VS Code Terminal**
1. Open VS Code
2. File → Open Folder → Select `prop-bet-analyzer`
3. Terminal → New Terminal (or Ctrl + `)

#### Step 2.2: Navigate to Backend

```bash
cd prop-bet-analyzer/backend
```

Confirm you're in the right place:
```bash
dir  # Windows
ls   # Mac/Linux
```

You should see: `app`, `requirements.txt`, `.env.example`, etc.

#### Step 2.3: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
```

**Mac/Linux:**
```bash
python3 -m venv venv
```

This creates a `venv` folder. Wait 30 seconds for it to complete.

#### Step 2.4: Activate Virtual Environment

**Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

You should now see `(venv)` at the start of your command prompt!

#### Step 2.5: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This takes 2-3 minutes. You'll see many packages installing.

**If you get errors:**
- Make sure virtual environment is activated (see `(venv)`)
- Try: `python -m pip install -r requirements.txt`

#### Step 2.6: Configure Environment Variables

**Windows:**
```bash
copy .env.example .env
```

**Mac/Linux:**
```bash
cp .env.example .env
```

Now edit `.env` file in VS Code or any text editor:

```env
# Database - CHANGE THIS!
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/propbet_db

# JWT Secret - GENERATE THIS!
SECRET_KEY=your-secret-key-will-go-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# BallDontLie API - Already set!
BALLDONTLIE_API_KEY=469863e1-e277-4a1e-bd6b-78445301c342

# Anthropic API for Image Upload - ADD YOUR KEY!
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**IMPORTANT - Generate SECRET_KEY:**

Run this command:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and paste it as your `SECRET_KEY` in `.env`.

**IMPORTANT - Set DATABASE_URL:**

Replace `YOUR_PASSWORD` with your PostgreSQL password!

Example:
```
DATABASE_URL=postgresql://postgres:mypassword123@localhost:5432/propbet_db
```

**IMPORTANT - Add ANTHROPIC_API_KEY:**

Paste your Claude API key from console.anthropic.com

#### Step 2.7: Run Database Migrations

```bash
alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> abc123, Initial migration
```

**If you get errors:**

**Error: "Can't connect to database"**
```bash
# Check PostgreSQL is running
# Verify DATABASE_URL in .env is correct
# Test connection: psql -U postgres -d propbet_db
```

**Error: "could not translate host name"**
```bash
# Your DATABASE_URL might be wrong
# Make sure it's: postgresql://postgres:password@localhost:5432/propbet_db
```

#### Step 2.8: Start Backend Server

```bash
uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

✅ **Backend is now running!**

**Test it:**
Open your browser and go to: http://localhost:8000/docs

You should see the interactive API documentation (Swagger UI).

**Keep this terminal window open!** The backend must stay running.

---

### PHASE 3: Frontend Setup (10 minutes)

#### Step 3.1: Open Second Terminal

**VS Code:** Click the `+` button in terminal panel

**Command Prompt:** Open a new command prompt window

#### Step 3.2: Navigate to Frontend

```bash
cd prop-bet-analyzer/frontend
```

Verify you're in the right place:
```bash
dir  # Windows
ls   # Mac/Linux
```

You should see: `src`, `package.json`, etc.

#### Step 3.3: Install Node Dependencies

```bash
npm install
```

This takes 3-5 minutes. You'll see many packages downloading.

**If you get "npm not found":**
1. Install Node.js from nodejs.org
2. Restart your terminal
3. Try again

**If you get permission errors (Windows):**
1. Run Command Prompt as Administrator
2. Navigate to frontend folder
3. Run `npm install` again

#### Step 3.4: Start Frontend Server

```bash
npm run dev
```

**Expected output:**
```
  VITE v5.0.11  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

✅ **Frontend is now running!**

**Keep this terminal open too!** Frontend must stay running.

---

### PHASE 4: First Use (5 minutes)

#### Step 4.1: Open the Application

Open your web browser and go to:

🌐 **http://localhost:5173**

You should see the PropBet Analyzer homepage with login/register options.

#### Step 4.2: Register Your Account

1. Click **"Register"** or **"Create Account"**

2. Fill in the form:
   - **Email**: `your@email.com`
   - **Username**: `yourname` (at least 3 characters)
   - **Password**: `password123` (at least 8 characters)
   - **Full Name**: `Your Name` (optional)

3. Click **"Create Account"**

4. You'll see a success message!

#### Step 4.3: Login

1. Click **"Sign In"** or be redirected to login

2. Enter your credentials:
   - **Username**: The one you just created
   - **Password**: Your password

3. Click **"Sign In"**

4. You'll be redirected to your dashboard!

#### Step 4.4: Create Your First Bet Slip

**Option A: Upload Image (Recommended)**

1. Click **"New Bet Slip"** or **"Create Analysis"**

2. Click **"Upload Image"** tab

3. Upload one of the bet slip images you provided earlier

4. Click **"Analyze Image"**

5. Wait 5-10 seconds while Claude extracts the props

6. Review the extracted props (they should match your image!)

7. Click **"Analyze Bet Slip"**

**Option B: Manual Entry**

1. Click **"New Bet Slip"**

2. Click **"Manual Entry"** tab

3. Fill in the first prop:
   - Player Name: `Anthony Black`
   - Stat Type: `points`
   - Line: `15.5`
   - Over/Under: `over`
   - Opponent: `Cleveland Cavaliers` (optional)

4. Click **"Add Prop"**

5. Add more props (repeat step 3 for each)

6. Click **"Analyze Bet Slip"**

#### Step 4.5: View Analysis Results

After clicking "Analyze," you'll see:

**Overall Analysis:**
- Overall Confidence Score (0-100)
- Risk Assessment (Low/Medium/High)
- Recommended Bets

**For Each Prop:**
- Confidence Score
- Hit Rate (last 10 games)
- Player's Recent Average
- Factors affecting the bet
- Recommendation (Strong Bet / Bet / Neutral / Avoid / Strong Avoid)
- Detailed analysis notes

**Example Result:**
```
Anthony Black - Points Over 15.5
Confidence: 72% (Strong Bet)
Hit Rate: 70% in last 10 games
Average: 17.2 points
Recommendation: Strong Bet

Analysis: Player has hit this prop in 70% of last 10 games. 
Player's average (17.2) is 1.7 above the line. Player is 
trending up recently. Player has been very consistent.
```

---

## 🎉 SUCCESS! You're Ready to Use the App

### Your Running Services

You should now have 3 things running:

1. **Backend**: http://localhost:8000
2. **Frontend**: http://localhost:5173
3. **PostgreSQL**: Running in background

### Quick Feature Tour

**✨ Image Upload with OCR**
- Upload any bet slip image
- Claude AI automatically extracts all props
- Review and edit before analyzing

**📊 Advanced Analysis**
- Hit rate from last 10 games
- Multiple statistical factors
- Confidence scoring
- Smart recommendations

**📚 Bet History**
- View all your past analyses
- Track accuracy over time
- Learn from patterns

**🔐 Secure Authentication**
- JWT token-based auth
- Password hashing with bcrypt
- Session management

---

## 🛑 Stopping the Application

When you're done:

1. **Stop Backend**: Press `Ctrl+C` in backend terminal
2. **Stop Frontend**: Press `Ctrl+C` in frontend terminal
3. **Deactivate venv**: Type `deactivate` in backend terminal

---

## 🔄 Restarting the Application

### Daily Startup Process

**Terminal 1 (Backend):**
```bash
cd prop-bet-analyzer/backend
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
uvicorn app.main:app --reload
```

**Terminal 2 (Frontend):**
```bash
cd prop-bet-analyzer/frontend
npm run dev
```

**Then open:** http://localhost:5173

---

## 🐛 Troubleshooting

### Backend Issues

**Problem: Can't connect to database**
```
✓ Check PostgreSQL is running (Services on Windows)
✓ Verify DATABASE_URL in .env
✓ Test: psql -U postgres -d propbet_db
✓ Check password in DATABASE_URL matches PostgreSQL password
```

**Problem: ModuleNotFoundError**
```bash
✓ Activate virtual environment: venv\Scripts\activate
✓ Reinstall: pip install -r requirements.txt
✓ Check you're in backend directory
```

**Problem: Port 8000 already in use**
```bash
# Find what's using it
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Mac/Linux

# Kill the process or use different port
uvicorn app.main:app --reload --port 8001
```

**Problem: Alembic migration fails**
```bash
# Drop and recreate database
psql -U postgres
DROP DATABASE propbet_db;
CREATE DATABASE propbet_db;
\q

# Run migrations again
alembic upgrade head
```

### Frontend Issues

**Problem: npm not found**
```
✓ Install Node.js from nodejs.org
✓ Restart terminal
✓ Verify: node --version
```

**Problem: Port 5173 already in use**
```bash
# Kill the process or edit vite.config.ts:
# Change port: 5173 to port: 5174
```

**Problem: Can't connect to backend**
```
✓ Verify backend is running: http://localhost:8000/health
✓ Check CORS in backend/app/config.py
✓ Clear browser cache and retry
```

### Image Upload Issues

**Problem: Image upload fails**
```
✓ Check ANTHROPIC_API_KEY in backend/.env
✓ Verify API key is valid at console.anthropic.com
✓ Check image file size (< 10MB)
✓ Check image format (PNG, JPG, GIF)
✓ Look at backend terminal for error messages
```

**Problem: No props extracted from image**
```
✓ Use a clear, well-lit image
✓ Make sure text is readable
✓ Try rotating/cropping the image
✓ Fall back to manual entry
```

### Analysis Issues

**Problem: All props show 50% confidence**
```
✓ Check player names are spelled correctly
✓ Try full names: "Anthony Black" not "A. Black"
✓ Verify BALLDONTLIE_API_KEY in .env
✓ Check backend logs for errors
✓ Test BallDontLie API: http://localhost:8000/docs
```

---

## 📊 Testing the Installation

### Backend Health Check

```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{"status":"healthy","environment":"development"}
```

### API Documentation

Visit: http://localhost:8000/docs

Try these endpoints:
1. POST `/auth/register` - Create test user
2. POST `/auth/login` - Get token
3. GET `/auth/me` - Verify token works

### Frontend Check

1. Can access http://localhost:5173
2. Can register a new user
3. Can login
4. Can create bet slip
5. Can upload image
6. Analysis returns real data (not just 50%)

---

## 📁 Project Structure Reference

```
prop-bet-analyzer/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py       # Login/register endpoints
│   │   │   └── bets.py       # Bet slip & analysis endpoints
│   │   ├── core/
│   │   │   └── analysis_engine.py  # Prop analysis logic
│   │   ├── models/
│   │   │   ├── user.py       # User database model
│   │   │   └── bet.py        # Bet slip models
│   │   ├── services/
│   │   │   ├── balldontlie.py     # NBA stats API
│   │   │   └── claude_ocr.py      # Image OCR service
│   │   ├── config.py         # App configuration
│   │   ├── database.py       # DB connection
│   │   └── main.py           # FastAPI app
│   ├── alembic/              # Database migrations
│   ├── .env                  # Environment variables
│   └── requirements.txt      # Python packages
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── BetSlipUpload.tsx  # Image upload component
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   └── CreateBetSlip.tsx
│   │   ├── services/
│   │   │   └── api.ts        # Backend API client
│   │   └── types/
│   │       └── index.ts      # TypeScript types
│   └── package.json          # Node packages
│
└── COMPLETE_INSTALL.md       # This file!
```

---

## 🎓 Understanding the Analysis

### Confidence Score Breakdown

**70-100% (Strong Bet)**
- Player consistently hits this prop
- Multiple favorable factors
- Recent trend is positive
- High confidence recommendation

**58-69% (Bet)**
- Player often hits this prop
- Some favorable factors
- Decent odds

**45-57% (Neutral)**
- Toss-up, could go either way
- Mixed factors
- No clear advantage

**30-44% (Avoid)**
- Player rarely hits this prop
- Unfavorable factors
- Better options available

**0-29% (Strong Avoid)**
- Very low probability
- Multiple negative factors
- Strong recommendation against

### Analysis Factors

**Recent Trend** (-1 to +1)
- How player's performance is changing
- Positive = improving, Negative = declining

**Consistency** (0 to 1)
- How predictable the player is
- High = reliable, Low = unpredictable

**Playing Time** (0 to 1)
- Minutes per game
- High = more opportunities

**Home/Away**
- Performance differential
- Some players perform better at home

**Rest Days**
- Days since last game
- More rest can help or hurt

---

## 🚀 Next Steps

### Immediate Actions

1. ✅ Register your account
2. ✅ Upload your bet slip images
3. ✅ Analyze your first bet slip
4. ✅ Review the recommendations
5. ✅ Compare to actual outcomes

### Short Term

- Analyze multiple bet slips
- Test different players and props
- Track which analyses were accurate
- Learn the analysis patterns

### Long Term

- Deploy to production
- Add more sports (NFL, MLB)
- Implement subscription tiers
- Build mobile app
- Add social features

---

## 🎯 Quick Command Reference

### Backend Commands
```bash
# Activate venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Start server
uvicorn app.main:app --reload

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Check database
psql -U postgres -d propbet_db
```

### Frontend Commands
```bash
# Install packages
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Database Commands
```sql
-- Create database
CREATE DATABASE propbet_db;

-- List databases
\l

-- Connect to database
\c propbet_db

-- List tables
\dt

-- View table
SELECT * FROM users;
```

---

## 💡 Tips for Best Results

**Image Upload:**
- Use good lighting
- Avoid glare and shadows
- Make sure text is clear
- Screenshot or take photo straight-on
- Crop to just the bet slip

**Manual Entry:**
- Use full player names
- Double-check stat types (points, rebounds, etc.)
- Verify line values
- Include opponent for better analysis

**Analysis:**
- Review all factors, not just confidence
- Look at hit rate over last 10 games
- Consider recent trends
- Read the analysis notes
- Always do your own research too!

---

## ⚠️ Important Disclaimers

**This tool is for:**
- ✅ Educational purposes
- ✅ Informational analysis
- ✅ Entertainment
- ✅ Learning statistics

**This tool is NOT:**
- ❌ Financial advice
- ❌ Guaranteed predictions
- ❌ Professional betting service
- ❌ Risk-free

**Remember:**
- Only bet what you can afford to lose
- Gambling can be addictive
- Check your local laws
- Age 21+ only where legal
- Past performance ≠ future results

---

## 🤝 Getting Help

### Resources

1. **README.md** - Project overview
2. **SETUP_GUIDE.md** - Detailed setup
3. **This file** - Installation steps
4. **API Docs** - http://localhost:8000/docs

### Common Solutions

- Check both terminals for errors
- Verify all environment variables
- Test database connection
- Clear browser cache
- Restart servers
- Check API keys are valid

### Still Stuck?

1. Read the error message carefully
2. Check the troubleshooting section
3. Google the specific error
4. Check file paths and spelling
5. Verify all prerequisites are met

---

## 🎉 Congratulations!

You now have a fully functional, production-ready NBA prop bet analyzer with:

✅ Image upload and OCR
✅ Advanced statistical analysis
✅ User authentication
✅ Modern React interface
✅ Secure backend API
✅ Database persistence

**Time to start analyzing those bets! 🏀💰**

(Remember: Bet responsibly!)
