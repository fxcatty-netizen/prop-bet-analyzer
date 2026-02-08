# PropBet Analyzer 🏀

AI-powered NBA prop bet analysis tool that helps you make smarter betting decisions using real-time player statistics, matchup analysis, and historical performance data.

## 🌟 Features

- **Intelligent Prop Analysis**: Analyzes player props using 10+ statistical factors
- **Real-Time Data**: Integrates with BallDontLie API for up-to-date NBA statistics
- **Confidence Scoring**: 0-100 confidence scores for each prop bet
- **Hit Rate Tracking**: Historical performance analysis (last 10 games)
- **Smart Recommendations**: Automated bet suggestions based on data analysis
- **Parlay Builder**: Suggests optimal prop combinations for parlays
- **User Authentication**: Secure JWT-based authentication
- **Bet History**: Track and review past analyses

## 📋 Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for frontend)
- **PostgreSQL 14+**
- **Git** (recommended)

## 🚀 Quick Start

### 1. Clone or Download the Project

Navigate to where you saved the `prop-bet-analyzer` folder on your desktop.

### 2. Backend Setup

```bash
cd prop-bet-analyzer/backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env  # Windows
# cp .env.example .env  # Mac/Linux

# Edit .env and set your PostgreSQL credentials
# DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/propbet_db
```

### 3. Database Setup

Create PostgreSQL database:

```sql
-- In psql or pgAdmin
CREATE DATABASE propbet_db;
```

Run migrations:

```bash
# Still in backend directory with venv activated
alembic upgrade head
```

### 4. Start Backend Server

```bash
uvicorn app.main:app --reload
```

Backend will be running at: http://localhost:8000

API Docs at: http://localhost:8000/docs

### 5. Frontend Setup (New Terminal)

```bash
cd prop-bet-analyzer/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be running at: http://localhost:5173

## 📱 Using the Application

### Register & Login

1. Open http://localhost:5173
2. Click "Register" and create an account
3. Login with your credentials

### Analyze Bet Slips

1. Click "New Analysis" or "Create Bet Slip"
2. Add your props:
   ```
   Player: Anthony Black
   Stat: points
   Line: 15.5
   Over/Under: over
   Opponent: Cleveland Cavaliers
   ```
3. Add more props as needed
4. Click "Analyze"

### View Results

The analysis will show:
- **Confidence Score** (0-100): How confident the model is
- **Hit Rate**: % of times player hit this prop recently
- **Average Stats**: Player's recent averages
- **Factors**: Breakdown of what's affecting the prop
- **Recommendation**: Strong Bet, Bet, Neutral, Avoid, Strong Avoid

## 🏗️ Architecture

### Backend (FastAPI + Python)

```
backend/
├── app/
│   ├── api/              # REST API endpoints
│   │   ├── auth.py       # Authentication routes
│   │   └── bets.py       # Bet slip routes
│   ├── core/             # Core business logic
│   │   └── analysis_engine.py   # Prop analysis algorithms
│   ├── models/           # SQLAlchemy database models
│   ├── schemas/          # Pydantic validation schemas
│   ├── services/         # External API integrations
│   │   └── balldontlie.py       # NBA stats API wrapper
│   └── utils/            # Utilities (security, etc.)
├── alembic/              # Database migrations
└── requirements.txt      # Python dependencies
```

### Frontend (React + TypeScript)

```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   ├── pages/            # Page components
│   ├── services/         # API client
│   ├── hooks/            # Custom React hooks
│   └── types/            # TypeScript types
└── package.json          # Node dependencies
```

## 🔧 Configuration

### Backend (.env)

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/propbet_db
SECRET_KEY=your-secret-key-here
BALLDONTLIE_API_KEY=469863e1-e277-4a1e-bd6b-78445301c342
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### API Rate Limits

- BallDontLie Free Tier: 30 requests/minute
- Cached data expires after 1 hour
- Consider upgrading for production use

## 📊 Analysis Methodology

The analysis engine evaluates props using:

1. **Historical Hit Rate** (40%): How often player hit this prop recently
2. **Statistical Average** (25%): Player's average vs the line
3. **Trend Analysis** (15%): Recent performance trajectory
4. **Consistency** (10%): Performance variance
5. **Playing Time** (10%): Minutes per game

### Confidence Tiers

- **70-100%**: Strong Bet ⭐⭐⭐
- **58-69%**: Bet ⭐⭐
- **45-57%**: Neutral ⭐
- **30-44%**: Avoid ⚠️
- **0-29%**: Strong Avoid 🚫

## 🧪 Testing

### Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpass123"
  }'

# Test in browser
Visit: http://localhost:8000/docs
```

## 🐛 Troubleshooting

### Backend Won't Start

**Issue**: Database connection error
```bash
# Check PostgreSQL is running
# Verify credentials in .env match your PostgreSQL setup
```

**Issue**: ModuleNotFoundError
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Frontend Won't Start

**Issue**: npm ERR!
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Issue**: CORS errors
```bash
# Check backend CORS_ORIGINS in .env includes frontend URL
# Default: http://localhost:5173
```

### Analysis Returns 50% Confidence

This means player data wasn't found. Ensure:
- Player name is spelled correctly
- Player is in NBA database
- BallDontLie API key is valid

## 🚧 Known Limitations

1. **MVP Version**: This is the Minimum Viable Product
2. **Manual Input Only**: Image upload/OCR not yet implemented
3. **Basic Analytics**: Advanced ML predictions coming in v2
4. **Limited Caching**: Redis recommended for production
5. **Local Only**: Deployment guide coming soon

## 📈 Roadmap

### Phase 2 (Coming Soon)
- ✅ Image upload for bet slips
- ✅ OCR for automatic prop parsing
- ✅ Advanced ML predictions
- ✅ Historical accuracy tracking
- ✅ Subscription tiers

### Phase 3 (Future)
- Mobile app
- Real-time odds integration
- Social features (sharing)
- Multiple sports (NFL, MLB)

## 🤝 Contributing

This is a personal project, but feedback welcome!

## 📄 License

MIT License - Free to use and modify

## ⚠️ Disclaimer

**This tool is for informational and educational purposes only.**

- Not financial or betting advice
- Gambling involves risk
- Only bet what you can afford to lose
- Check local gambling laws
- Age 21+ only

## 📞 Support

Having issues? Check:

1. This README
2. SETUP_GUIDE.md (detailed instructions)
3. Backend logs in terminal
4. Frontend console (F12 in browser)
5. API docs: http://localhost:8000/docs

## 🎯 Example Usage

### Analyzing the Uploaded Bet Slip

Based on your uploaded images, here's how to input that bet:

```json
{
  "name": "SGP - Magic vs Cavs + Lakers vs Bulls",
  "prop_bets": [
    {
      "player_name": "Anthony Black",
      "stat_type": "points",
      "line": 15,
      "over_under": "over",
      "opponent_name": "Cleveland Cavaliers"
    },
    {
      "player_name": "Anthony Black",
      "stat_type": "rebounds",
      "line": 4,
      "over_under": "over",
      "opponent_name": "Cleveland Cavaliers"
    },
    {
      "player_name": "Anthony Black",
      "stat_type": "assists",
      "line": 4,
      "over_under": "over",
      "opponent_name": "Cleveland Cavaliers"
    },
    {
      "player_name": "Coby White",
      "stat_type": "points",
      "line": 15,
      "over_under": "over",
      "opponent_name": "Los Angeles Lakers"
    },
    {
      "player_name": "Coby White",
      "stat_type": "assists",
      "line": 4,
      "over_under": "over",
      "opponent_name": "Los Angeles Lakers"
    }
  ]
}
```

The analyzer will fetch each player's recent stats and provide detailed analysis!

---

**Built with ❤️ for smarter sports betting**
