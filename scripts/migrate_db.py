#!/usr/bin/env python3
"""
Robust database migration script with comprehensive error handling.
"""

import os
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def create_directories():
    """Create necessary directories."""
    directories = [
        "data/models",
        "data/raw", 
        "data/processed",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def test_database_connection():
    """Test database connection."""
    print("🔌 Testing database connection...")
    
    try:
        from app.config.settings import settings
        print(f"✓ Settings loaded - DB URL: {settings.database_url}")
        
        from sqlalchemy import create_engine, text
        
        # Create engine with connection testing
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10}
        )
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✓ Connected to PostgreSQL: {version[:50]}...")
            
        return engine
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return None
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure PostgreSQL is running: sudo systemctl status postgresql")
        print("2. Check if database exists: psql -U postgres -l | grep loan_db")
        print("3. Create database if needed: sudo -u postgres createdb loan_db")
        print("4. Verify credentials in .env file")
        return None

def create_tables(engine):
    """Create database tables."""
    print("\n📋 Creating database tables...")
    
    try:
        # Import models
        from app.core.models.database import Base, LoanApplication, FeatureWeights, ModelMetrics
        
        print("✓ Database models imported successfully")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✓ Database tables created successfully!")
        
        # List created tables
        print("\n📊 Created tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        return False

def verify_tables(engine):
    """Verify tables were created."""
    print("\n🔍 Verifying table creation...")
    
    try:
        from sqlalchemy import text, inspect
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = ['loan_applications', 'feature_weights', 'model_metrics']
        
        for table in expected_tables:
            if table in tables:
                print(f"✓ Table '{table}' exists")
                
                # Get column info
                columns = inspector.get_columns(table)
                print(f"  Columns: {len(columns)}")
                for col in columns[:3]:  # Show first 3 columns
                    print(f"    - {col['name']} ({col['type']})")
                if len(columns) > 3:
                    print(f"    ... and {len(columns) - 3} more columns")
            else:
                print(f"❌ Table '{table}' missing")
                
        return len([t for t in expected_tables if t in tables]) == len(expected_tables)
        
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False

def main():
    print("🚀 Starting database migration...")
    print("=" * 50)
    
    # Step 1: Create directories
    create_directories()
    
    # Step 2: Test database connection
    engine = test_database_connection()
    if not engine:
        print("\n❌ Migration failed - database connection issue")
        sys.exit(1)
    
    # Step 3: Create tables
    if not create_tables(engine):
        print("\n❌ Migration failed - table creation issue")
        sys.exit(1)
    
    # Step 4: Verify tables
    if not verify_tables(engine):
        print("\n⚠️  Migration completed with warnings - some tables may be missing")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Database migration completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run: python scripts/seed_data.py")
    print("2. Start application: uvicorn app.main:app --reload")
    print("3. Test API: curl http://localhost:8000/health")

if __name__ == "__main__":
    main()