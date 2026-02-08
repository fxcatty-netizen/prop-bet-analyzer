#!/usr/bin/env python3
"""
File Verification Script for PropBet Analyzer
Run this to check if all required files exist
"""

import os
from pathlib import Path

def check_files():
    """Check if all required files exist"""
    
    # Get the script's directory
    base_dir = Path(__file__).parent
    
    # Required backend files
    backend_files = [
        "backend/app/__init__.py",
        "backend/app/main.py",
        "backend/app/config.py",
        "backend/app/database.py",
        "backend/app/dependencies.py",
        "backend/app/api/__init__.py",
        "backend/app/api/auth.py",
        "backend/app/api/bets.py",
        "backend/app/models/__init__.py",
        "backend/app/models/user.py",
        "backend/app/models/bet.py",
        "backend/app/schemas/__init__.py",
        "backend/app/schemas/user.py",
        "backend/app/schemas/bet.py",
        "backend/app/services/__init__.py",
        "backend/app/services/balldontlie.py",
        "backend/app/services/claude_ocr.py",
        "backend/app/core/__init__.py",
        "backend/app/core/analysis_engine.py",
        "backend/app/utils/__init__.py",
        "backend/app/utils/security.py",
        "backend/requirements.txt",
        "backend/.env.example",
    ]
    
    # Required frontend files
    frontend_files = [
        "frontend/src/main.tsx",
        "frontend/src/App.tsx",
        "frontend/src/index.css",
        "frontend/src/components/BetSlipUpload.tsx",
        "frontend/src/pages/Login.tsx",
        "frontend/src/pages/Register.tsx",
        "frontend/src/pages/Dashboard.tsx",
        "frontend/src/pages/CreateBetSlip.tsx",
        "frontend/src/pages/Analysis.tsx",
        "frontend/src/services/api.ts",
        "frontend/src/hooks/useAuth.ts",
        "frontend/src/types/index.ts",
        "frontend/package.json",
        "frontend/tsconfig.json",
        "frontend/vite.config.ts",
        "frontend/tailwind.config.js",
        "frontend/index.html",
    ]
    
    missing_backend = []
    missing_frontend = []
    
    print("=" * 60)
    print("PropBet Analyzer - File Verification")
    print("=" * 60)
    print()
    
    # Check backend files
    print("Checking Backend Files...")
    for file_path in backend_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} - MISSING!")
            missing_backend.append(file_path)
    
    print()
    
    # Check frontend files
    print("Checking Frontend Files...")
    for file_path in frontend_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} - MISSING!")
            missing_frontend.append(file_path)
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    if not missing_backend and not missing_frontend:
        print("✅ All files present! You're ready to install.")
        print()
        print("Next steps:")
        print("1. Create PostgreSQL database: propbet_db")
        print("2. cd backend")
        print("3. python -m venv venv")
        print("4. venv\\Scripts\\activate")
        print("5. pip install -r requirements.txt")
        return True
    else:
        print(f"❌ Missing {len(missing_backend) + len(missing_frontend)} files")
        print()
        if missing_backend:
            print("Missing Backend Files:")
            for f in missing_backend:
                print(f"  - {f}")
        if missing_frontend:
            print("Missing Frontend Files:")
            for f in missing_frontend:
                print(f"  - {f}")
        print()
        print("Please re-download the project or contact support.")
        return False

if __name__ == "__main__":
    try:
        check_files()
    except Exception as e:
        print(f"Error running verification: {e}")
        print("Make sure you're running this from the prop-bet-analyzer folder")
