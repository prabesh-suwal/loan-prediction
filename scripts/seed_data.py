#!/usr/bin/env python3
"""
Seed initial data into the database.
"""

import sys
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent.parent))

from app.config.database import SessionLocal
from app.core.models.database import FeatureWeights

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
        print(f"Seeded {len(default_weights)} feature weights")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding feature weights: {e}")
    finally:
        db.close()

def main():
    print("Seeding initial data...")
    seed_feature_weights()
    print("Data seeding completed!")

if __name__ == "__main__":
    main()  