#!/usr/bin/env python3
"""
Quick fix script to resolve common issues.
"""

import sys
import os
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_file_exists():
    """Check if all required files exist."""
    print("📁 Checking required files...")
    
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/api/__init__.py", 
        "app/api/v1/__init__.py",
        "app/api/v1/api.py",
        "app/api/v1/endpoints/__init__.py",
        "app/api/v1/endpoints/auth.py",
        "app/api/v1/endpoints/admin_dashboard.py",
        "app/core/__init__.py",
        "app/core/models/__init__.py",
        "app/core/models/schemas.py",
        "app/core/models/auth_schemas.py",
        "app/core/auth/__init__.py",
        "app/core/auth/auth_utils.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f"   ❌ Missing: {file_path}")
        else:
            print(f"   ✅ Found: {file_path}")
    
    return missing_files

def create_missing_init_files():
    """Create missing __init__.py files."""
    print("\n📝 Creating missing __init__.py files...")
    
    init_dirs = [
        "app",
        "app/api",
        "app/api/v1", 
        "app/api/v1/endpoints",
        "app/core",
        "app/core/models",
        "app/core/auth",
        "app/core/services",
        "app/core/repositories",
        "app/ml",
        "app/ml/models",
        "app/ml/preprocessing",
        "app/ml/explainer",
        "app/utils"
    ]
    
    for dir_path in init_dirs:
        init_file = Path(dir_path) / "__init__.py"
        if not init_file.exists():
            init_file.parent.mkdir(parents=True, exist_ok=True)
            init_file.write_text("# Auto-generated __init__.py\n")
            print(f"   ✅ Created: {init_file}")

def check_imports():
    """Check if imports work correctly."""
    print("\n🔍 Checking imports...")
    
    try:
        from app.config.settings import settings
        print("   ✅ Settings import - OK")
    except Exception as e:
        print(f"   ❌ Settings import failed: {e}")
    
    try:
        from app.config.database import get_db
        print("   ✅ Database import - OK")
    except Exception as e:
        print(f"   ❌ Database import failed: {e}")
    
    try:
        from app.core.models.schemas import LoanApplicationInput
        print("   ✅ Schemas import - OK")
    except Exception as e:
        print(f"   ❌ Schemas import failed: {e}")
    
    try:
        from app.core.models.auth_schemas import UserRole
        print("   ✅ Auth schemas import - OK")
    except Exception as e:
        print(f"   ❌ Auth schemas import failed: {e}")
    
    try:
        from app.api.v1.api import api_router
        print("   ✅ API router import - OK")
    except Exception as e:
        print(f"   ❌ API router import failed: {e}")

def test_database_connection():
    """Test database connection."""
    print("\n🔌 Testing database connection...")
    
    try:
        from app.config.settings import settings
        from sqlalchemy import create_engine, text
        
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("   ✅ Database connection - OK")
        return True
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

def check_users_table():
    """Check if users table has data."""
    print("\n👥 Checking users table...")
    
    try:
        from app.config.settings import settings
        from sqlalchemy import create_engine, text
        
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            print(f"   Users in database: {count}")
            
            if count == 0:
                print("   ⚠️  No users found - run: python scripts/seed_data.py")
            else:
                result = conn.execute(text("SELECT username, role FROM users"))
                for row in result:
                    username, role = row
                    print(f"   👤 {username} ({role})")
        return True
    except Exception as e:
        print(f"   ❌ Users table check failed: {e}")
        return False

def suggest_fixes():
    """Suggest fixes for common issues."""
    print("\n💡 Suggested fixes:")
    print("1. Create missing files:")
    print("   python scripts/quick_fix.py")
    print("\n2. Fix database issues:")
    print("   python scripts/fix_database.py")
    print("   python scripts/seed_data.py")
    print("\n3. Restart the application:")
    print("   uvicorn app.main:app --reload")
    print("\n4. Check endpoints:")
    print("   python scripts/debug_endpoints.py")
    print("\n5. Manual verification:")
    print("   curl http://localhost:8000/")
    print("   curl http://localhost:8000/health")
    print("   curl http://localhost:8000/docs")

def main():
    print("🔧 QUICK FIX TOOL")
    print("=" * 50)
    
    # Check files
    missing_files = check_file_exists()
    
    # Create missing __init__.py files
    create_missing_init_files()
    
    # Check imports
    check_imports()
    
    # Test database
    db_ok = test_database_connection()
    
    if db_ok:
        check_users_table()
    
    # Summary and suggestions
    print("\n" + "=" * 50)
    if missing_files:
        print("⚠️  Some files are missing. This might cause import errors.")
    else:
        print("✅ All required files are present.")
    
    suggest_fixes()

if __name__ == "__main__":
    main()