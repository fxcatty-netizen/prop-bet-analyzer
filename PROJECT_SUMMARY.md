# 🎉 PropBet Analyzer - Complete Project with Image Upload

## What You Have

A **production-ready NBA prop bet analysis SaaS application** with full image upload and OCR capabilities powered by Claude AI.

---

## ✨ Key Features

### 🖼️ **Image Upload with AI OCR** (NEW!)
- Drag and drop bet slip images
- Claude AI automatically extracts all props
- Supports PNG, JPG, GIF formats
- Handles Same Game Parlays (SGP)
- Smart parsing of player names, stats, lines

### 📊 **Advanced Analysis Engine**
- Analyzes 10+ statistical factors
- Hit rate from last 10 games
- Confidence scoring (0-100)
- Recent trend analysis
- Consistency metrics
- Playing time evaluation

### 🎯 **Smart Recommendations**
- Strong Bet (70-100% confidence)
- Bet (58-69%)
- Neutral (45-57%)
- Avoid (30-44%)
- Strong Avoid (0-29%)

### 🔐 **Security & Auth**
- JWT token authentication
- Bcrypt password hashing
- Secure session management
- User-specific data isolation

### 💻 **Modern Tech Stack**
- **Backend**: Python 3.10+, FastAPI, PostgreSQL
- **Frontend**: React 18, TypeScript, Tailwind CSS
- **APIs**: BallDontLie (NBA stats), Anthropic Claude (OCR)
- **Deployment Ready**: Docker-ready, production configs

---

## 📁 What's Included

### Backend Files
```
backend/
├── app/
│   ├── api/
│   │   ├── auth.py          ✅ Login/register
│   │   └── bets.py          ✅ Bet slip CRUD + image upload
│   ├── core/
│   │   └── analysis_engine.py  ✅ Prop analysis algorithms
│   ├── models/
│   │   ├── user.py          ✅ User model
│   │   └── bet.py           ✅ BetSlip, PropBet, Analysis models
│   ├── schemas/
│   │   ├── user.py          ✅ API validation schemas
│   │   └── bet.py           ✅ Bet slip schemas
│   ├── services/
│   │   ├── balldontlie.py   ✅ NBA stats API wrapper
│   │   └── claude_ocr.py    ✅ Image OCR service (NEW!)
│   ├── utils/
│   │   └── security.py      ✅ JWT & password hashing
│   ├── config.py            ✅ App configuration
│   ├── database.py          ✅ Database connection
│   ├── dependencies.py      ✅ Auth dependencies
│   └── main.py              ✅ FastAPI app
├── alembic/                 ✅ Database migrations
├── .env.example             ✅ Environment template
└── requirements.txt         ✅ Python dependencies
```

### Frontend Files
```
frontend/
├── src/
│   ├── components/
│   │   └── BetSlipUpload.tsx   ✅ Image upload component (NEW!)
│   ├── pages/
│   │   ├── Login.tsx           ✅ Login page
│   │   ├── Register.tsx        ✅ Registration page
│   │   ├── Dashboard.tsx       ✅ User dashboard (NEW!)
│   │   ├── CreateBetSlip.tsx   ✅ Create bet slip (NEW!)
│   │   └── Analysis.tsx        ✅ Analysis results
│   ├── services/
│   │   └── api.ts              ✅ Backend API client
│   ├── hooks/
│   │   └── useAuth.ts          ✅ Authentication hook
│   ├── types/
│   │   └── index.ts            ✅ TypeScript types
│   ├── App.tsx                 ✅ Main app component (NEW!)
│   ├── main.tsx                ✅ Entry point (NEW!)
│   └── index.css               ✅ Tailwind styles (NEW!)
├── index.html                  ✅ HTML template
├── package.json                ✅ Node dependencies
├── tsconfig.json               ✅ TypeScript config
├── tailwind.config.js          ✅ Tailwind config
└── vite.config.ts              ✅ Vite config
```

### Documentation
```
├── README.md                    ✅ Project overview
├── GETTING_STARTED.md           ✅ Detailed setup guide
├── SETUP_GUIDE.md               ✅ Technical guide
├── COMPLETE_INSTALL.md          ✅ Step-by-step install (NEW!)
├── COMMANDS.md                  ✅ Quick command reference (NEW!)
└── quickstart.bat               ✅ Windows auto-setup script
```

---

## 🚀 Quick Start (3 Steps)

### 1. Create Database
```sql
CREATE DATABASE propbet_db;
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
# Edit .env with your keys
alembic upgrade head
uvicorn app.main:app --reload
```

### 3. Frontend Setup (New Terminal)
```bash
cd frontend
npm install
npm run dev
```

**Open:** http://localhost:5173

---

## 🔑 Required API Keys

### Already Configured
✅ **BallDontLie API**: `469863e1-e277-4a1e-bd6b-78445301c342`

### You Need to Add
📝 **Anthropic API Key**: Get from https://console.anthropic.com
- Sign up for Claude API
- Create API key
- Add to `backend/.env` as `ANTHROPIC_API_KEY`

💡 **Why?** Powers the image upload OCR feature. Without it, manual entry still works!

---

## 📖 How to Use

### Upload Bet Slip Image
1. Click "New Bet Slip"
2. Click "Upload Image"
3. Drag/drop your bet slip screenshot
4. Click "Analyze Image"
5. Props extracted automatically!
6. Review and click "Analyze Bet Slip"

### Manual Entry
1. Click "New Bet Slip"
2. Click "Manual Entry"
3. Fill in prop details
4. Click "Add Prop"
5. Repeat for each prop
6. Click "Analyze Bet Slip"

### View Analysis
- Overall confidence score
- Individual prop analysis
- Hit rates and averages
- Factor breakdown
- Recommendations

---

## 📊 Example Analysis

```
Anthony Black - Points Over 15.5
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Confidence: 72% ⭐⭐⭐ (Strong Bet)
Hit Rate: 70% in last 10 games
Average: 17.2 points
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Factors:
✓ Recent Trend: +0.8 (Improving)
✓ Consistency: 0.9 (Very consistent)
✓ Playing Time: 0.85 (34 min/game)

Recommendation: STRONG BET

Analysis: Player has hit this prop in 70% 
of last 10 games. Player's average (17.2) 
is 1.7 above the line. Player is trending 
up recently. Player has been very consistent.
```

---

## 🛠️ Technical Details

### API Endpoints
- `POST /auth/register` - Create account
- `POST /auth/login` - Get JWT token
- `GET /auth/me` - Get user info
- `POST /bets/upload` - Upload image (NEW!)
- `POST /bets/` - Create bet slip
- `GET /bets/` - List bet slips
- `POST /bets/{id}/analyze` - Analyze
- `DELETE /bets/{id}` - Delete

### Database Schema
- **users**: Authentication
- **bet_slips**: Bet slip records
- **prop_bets**: Individual props
- **analyses**: Analysis results

### Tech Highlights
- **Async/Await**: Non-blocking I/O
- **SQLAlchemy ORM**: Type-safe database
- **Alembic Migrations**: Version control for DB
- **Pydantic Validation**: Request/response schemas
- **React Hooks**: Modern React patterns
- **TypeScript**: Type safety
- **Tailwind CSS**: Utility-first styling

---

## 🎯 What Makes This Special

### 1. Image Upload with Claude OCR
- No manual typing needed
- Extracts all props automatically
- Handles complex bet slip layouts
- Understands sports betting terminology

### 2. Production Ready
- Proper authentication & security
- Database migrations
- Error handling
- Input validation
- Rate limiting ready

### 3. Clean Architecture
- Separation of concerns
- Reusable components
- Type safety
- Well documented

### 4. Scalable Design
- Easy to add new sports
- Extensible analysis factors
- API-first architecture
- Ready for deployment

---

## 📚 Documentation Guide

**Start Here:**
1. **README.md** - Project overview
2. **COMMANDS.md** - Copy-paste commands
3. **COMPLETE_INSTALL.md** - Full walkthrough

**For Details:**
- **SETUP_GUIDE.md** - Technical setup
- **GETTING_STARTED.md** - First-time setup
- **API Docs** - http://localhost:8000/docs

---

## 🐛 Common Issues

### Image Upload Not Working
```
✓ Check ANTHROPIC_API_KEY in backend/.env
✓ Verify API key at console.anthropic.com
✓ Check image file size (<10MB)
✓ Use clear, well-lit images
```

### Props Show 50% Confidence
```
✓ Check player name spelling
✓ Use full names: "Anthony Black"
✓ Verify BALLDONTLIE_API_KEY
✓ Check backend logs for errors
```

### Can't Connect to Backend
```
✓ Backend running on port 8000
✓ Frontend CORS configured
✓ Test: curl http://localhost:8000/health
```

---

## 🚀 Next Steps

### Immediate
1. Set up the application
2. Add your Anthropic API key
3. Upload your bet slip images
4. Get your first analysis

### Short Term
- Analyze multiple bet slips
- Track accuracy
- Learn the factors
- Refine strategy

### Long Term
- Deploy to production (Railway + Vercel)
- Add subscription tiers (Stripe)
- Expand to NFL, MLB
- Build mobile app
- Add social features

---

## ⚠️ Important Notes

### This Is:
✅ Educational tool
✅ Statistical analysis
✅ Information resource
✅ Entertainment

### This Is NOT:
❌ Financial advice
❌ Guaranteed predictions
❌ Professional betting service
❌ Risk-free

### Remember:
- Bet responsibly
- Only risk what you can afford
- Check local gambling laws
- Past performance ≠ future results
- Age 21+ only

---

## 🎉 You're Ready!

Everything you need is here:
✅ Complete source code
✅ Step-by-step guides
✅ API documentation
✅ Example commands
✅ Troubleshooting tips

**Start with COMMANDS.md for quick setup!**

---

## 📞 Support

1. Read COMPLETE_INSTALL.md
2. Check COMMANDS.md
3. Review troubleshooting sections
4. Test API at /docs endpoint
5. Check terminal logs for errors

---

**Built with ❤️ for smarter sports betting analysis**

🏀 Good luck with your bets! 🎯

(Remember: Always bet responsibly!)
