# 📝 STEP-BY-STEP COMMAND GUIDE

Copy and paste these commands exactly as shown.

---

## 🗄️ STEP 1: DATABASE SETUP

### Create PostgreSQL Database

```sql
-- Open psql (Windows Command Prompt as Administrator):
psql -U postgres

-- Or on Mac/Linux:
psql postgres

-- Then run these commands:
CREATE DATABASE propbet_db;

-- Verify it was created:
\l

-- Exit:
\q
```

✅ **Database created!**

---

## 🐍 STEP 2: BACKEND SETUP

### Open Command Prompt/Terminal

Navigate to the backend folder:

```bash
cd prop-bet-analyzer/backend
```

### Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
```

**Mac/Linux:**
```bash
python3 -m venv venv
```

### Activate Virtual Environment

**Windows Command Prompt:**
```cmd
venv\Scripts\activate
```

**Windows PowerShell:**
```powershell
venv\Scripts\Activate.ps1
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` in your prompt now!

### Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Wait 2-3 minutes for installation to complete.

### Create Environment File

**Windows:**
```cmd
copy .env.example .env
```

**Mac/Linux:**
```bash
cp .env.example .env
```

### Generate SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Copy the output!** You'll paste it in the next step.

### Edit .env File

Open `backend/.env` in a text editor and update these lines:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/propbet_db
SECRET_KEY=PASTE_THE_SECRET_KEY_YOU_GENERATED_HERE
ANTHROPIC_API_KEY=your-claude-api-key-from-console.anthropic.com
```

**Important:** Replace:
- `YOUR_PASSWORD` with your PostgreSQL password
- `PASTE_THE_SECRET_KEY...` with the key you just generated
- `your-claude-api-key...` with your actual Anthropic API key

Save the file!

### Run Database Migrations

```bash
alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> xxxxx, Initial migration
```

### Start Backend Server

```bash
uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

✅ **Backend is running!**

**Test it:** Open http://localhost:8000/docs in your browser

**Keep this terminal open!**

---

## ⚛️ STEP 3: FRONTEND SETUP

### Open New Terminal

Open a **second** command prompt/terminal window.

Navigate to frontend folder:

```bash
cd prop-bet-analyzer/frontend
```

### Install Node Dependencies

```bash
npm install
```

Wait 3-5 minutes for installation.

### Create Environment File (Optional)

Create `frontend/.env.local`:

```bash
# Windows
echo VITE_API_URL=http://localhost:8000 > .env.local

# Mac/Linux
echo "VITE_API_URL=http://localhost:8000" > .env.local
```

### Start Frontend Server

```bash
npm run dev
```

**Expected output:**
```
  VITE v5.0.11  ready in 500 ms
  ➜  Local:   http://localhost:5173/
```

✅ **Frontend is running!**

**Keep this terminal open too!**

---

## 🌐 STEP 4: OPEN THE APP

Open your web browser and go to:

```
http://localhost:5173
```

---

## 👤 STEP 5: CREATE ACCOUNT

### Register

1. Click "Register" or "Create Account"
2. Fill in the form:
   - Email: `test@example.com`
   - Username: `testuser`
   - Password: `password123`
3. Click "Create Account"

### Login

1. Enter your credentials
2. Click "Sign In"
3. You're in!

---

## 📊 STEP 6: ANALYZE A BET SLIP

### Option A: Upload Image

1. Click "New Bet Slip"
2. Click "Upload Image" tab
3. Select a bet slip image
4. Click "Analyze Image"
5. Wait for props to be extracted
6. Click "Analyze Bet Slip"

### Option B: Manual Entry

1. Click "New Bet Slip"
2. Fill in prop details:
   - Player Name: `Anthony Black`
   - Stat Type: `points`
   - Line: `15.5`
   - Over/Under: `over`
3. Click "Add Prop"
4. Add more props (repeat step 2)
5. Click "Analyze Bet Slip"

---

## 🎉 YOU'RE DONE!

The analysis will show:
- Confidence scores
- Hit rates
- Recommendations
- Detailed factor breakdown

---

## 🛑 STOPPING THE APP

When you're done for the day:

### Terminal 1 (Backend):
```
Press Ctrl+C
deactivate
```

### Terminal 2 (Frontend):
```
Press Ctrl+C
```

---

## 🔄 RESTARTING THE APP

### Next Time You Use It:

**Terminal 1 (Backend):**
```bash
cd prop-bet-analyzer/backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

**Terminal 2 (Frontend):**
```bash
cd prop-bet-analyzer/frontend
npm run dev
```

**Open:** http://localhost:5173

---

## 🐛 IF SOMETHING GOES WRONG

### Backend Won't Start

**Check PostgreSQL is running:**
```bash
# Windows: Open Services, find postgresql, start it
# Mac: brew services start postgresql@14
# Linux: sudo systemctl start postgresql
```

**Test database connection:**
```bash
psql -U postgres -d propbet_db
```

If this fails, your DATABASE_URL in .env is wrong.

### Frontend Won't Start

**Clear node_modules and reinstall:**
```bash
cd frontend
rmdir /s node_modules  # Windows
rm -rf node_modules    # Mac/Linux
npm install
```

### Can't See Backend API Docs

**Make sure backend is running:**
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

### Image Upload Not Working

**Check your Anthropic API key:**
1. Go to console.anthropic.com
2. Verify your API key is correct
3. Update ANTHROPIC_API_KEY in backend/.env
4. Restart backend server

---

## 📞 QUICK TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Can't connect to database | Check PostgreSQL is running, verify DATABASE_URL |
| ModuleNotFoundError | Activate venv: `venv\Scripts\activate` |
| Port 8000 in use | Kill process or use --port 8001 |
| npm not found | Install Node.js from nodejs.org |
| Frontend can't reach backend | Check backend is running on port 8000 |
| Analysis returns 50% | Check player name spelling |
| Image upload fails | Verify ANTHROPIC_API_KEY in .env |

---

## ✅ SUCCESS CHECKLIST

- [ ] PostgreSQL database created
- [ ] Backend virtual environment activated
- [ ] All Python packages installed
- [ ] .env file configured with all keys
- [ ] Database migrations run successfully
- [ ] Backend starts without errors
- [ ] Can access http://localhost:8000/docs
- [ ] Frontend npm packages installed
- [ ] Frontend starts without errors
- [ ] Can access http://localhost:5173
- [ ] Can register a new user
- [ ] Can login successfully
- [ ] Can create a bet slip
- [ ] Can upload an image (OCR works)
- [ ] Analysis returns real data

If all checked, you're ready! 🎉

---

## 🎯 WHAT YOU'VE BUILT

A complete SaaS application with:

✅ **Backend API (Python/FastAPI)**
- REST API endpoints
- JWT authentication
- PostgreSQL database
- BallDontLie API integration
- Claude AI OCR for images
- Advanced analysis algorithms

✅ **Frontend (React/TypeScript)**
- Modern, responsive UI
- Image upload with drag-and-drop
- Manual prop entry forms
- Analysis visualization
- User authentication

✅ **Analysis Features**
- Automatic prop extraction from images
- Statistical analysis (10+ factors)
- Confidence scoring (0-100)
- Smart recommendations
- Historical hit rates

**Time to analyze some bets! 🏀**
