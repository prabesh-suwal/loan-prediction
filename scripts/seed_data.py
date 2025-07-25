#!/usr/bin/env python3
"""
Seed initial data into the database including default superadmin user.
"""

import sys
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent.parent))

from app.config.database import SessionLocal
from app.core.models.database import FeatureWeights, User
from app.core.models.auth_schemas import UserRole
from app.core.auth.auth_utils import get_password_hash

def seed_superadmin_user():
    """Create default superadmin user."""
    
    db = SessionLocal()
    
    try:
        # Check if superadmin already exists
        existing_admin = db.query(User).filter(User.role == UserRole.SUPERADMIN).first()
        if existing_admin:
            print("Superadmin user already exists. Skipping...")
            return
        
        # Create default superadmin
        superadmin = User(
            username="superadmin",
            email="admin@loanapproval.com",
            full_name="Super Administrator",
            hashed_password=get_password_hash("admin123"),  # Change this in production!
            role=UserRole.SUPERADMIN,
            is_active=True,
            is_disabled=False
        )
        
        db.add(superadmin)
        db.commit()
        
        print("✓ Created default superadmin user:")
        print("  Username: superadmin")
        print("  Email: admin@loanapproval.com")
        print("  Password: admin123")
        print("  ⚠️  IMPORTANT: Change the default password after first login!")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating superadmin user: {e}")
    finally:
        db.close()

def seed_demo_bm_user():
    """Create a demo bank manager user."""
    
    db = SessionLocal()
    
    try:
        # Check if demo BM already exists
        existing_bm = db.query(User).filter(User.username == "bankmanager").first()
        if existing_bm:
            print("Demo bank manager user already exists. Skipping...")
            return
        
        # Create demo bank manager
        bank_manager = User(
            username="bankmanager",
            email="bm@loanapproval.com",
            full_name="Bank Manager Demo",
            hashed_password=get_password_hash("bm123"),  # Change this in production!
            role=UserRole.BM,
            is_active=True,
            is_disabled=False
        )
        
        db.add(bank_manager)
        db.commit()
        
        print("✓ Created demo bank manager user:")
        print("  Username: bankmanager")
        print("  Email: bm@loanapproval.com")
        print("  Password: bm123")
        print("  ⚠️  IMPORTANT: Change the default password after first login!")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating bank manager user: {e}")
    finally:
        db.close()

def seed_feature_weights():
    """Seed initial feature weights."""
    
    db = SessionLocal()
    
    try:
        # Check if weights already exist
        existing = db.query(FeatureWeights).first()
        if existing:
            print("Feature weights already exist. Skipping...")
            return
        
        # Default feature weights
        default_weights = [
            ("credit_history", 2.5, "Credit history is the most important factor"),
            ("total_income", 2.0, "Total household income"),
            ("emi_income_ratio", 1.8, "EMI to income ratio"),
            ("loan_amount", 1.5, "Loan amount requested"),
            ("education", 1.2, "Education level"),
            ("property_area", 1.1, "Property location"),
            ("self_employed", 1.0, "Employment type"),
            ("married", 0.9, "Marital status"),
            ("dependents", 0.8, "Number of dependents"),
            ("gender", 0.5, "Gender (lowest weight for fairness)")
        ]
        
        for feature_name, weight, description in default_weights:
            feature_weight = FeatureWeights(
                feature_name=feature_name,
                weight=weight,
                description=description,
                is_active=True
            )
            db.add(feature_weight)
        
        db.commit()
        print(f"✓ Seeded {len(default_weights)} feature weights")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding feature weights: {e}")
    finally:
        db.close()

def main():
    print("🌱 Seeding initial data...")
    print("=" * 50)
    
    # Seed default users
    seed_superadmin_user()
    seed_demo_bm_user()
    
    # Seed feature weights
    seed_feature_weights()
    
    print("=" * 50)
    print("🎉 Data seeding completed!")
    print("\n📋 Default Login Credentials:")
    print("1. Superadmin:")
    print("   Username: superadmin")
    print("   Password: admin123")
    print("\n2. Bank Manager:")
    print("   Username: bankmanager") 
    print("   Password: bm123")
    print("\n⚠️  SECURITY WARNING:")
    print("   - Change all default passwords immediately!")
    print("   - Use strong passwords in production!")
    print("   - Enable additional security measures!")

if __name__ == "__main__":
    main()