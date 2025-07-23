#!/usr/bin/env python3
"""
Script to train the loan approval model with proper error handling.
"""

import pandas as pd
import numpy as np
import argparse
import sys
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, precision_score, recall_score, f1_score
import joblib

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_and_prepare_data(data_path):
    """Load and prepare training data."""
    print(f"Loading data from {data_path}...")
    
    try:
        df = pd.read_csv(data_path)
        print(f"✓ Loaded {len(df)} records")
        
        # Check required columns
        required_columns = [
            'Gender', 'Married', 'Dependents', 'Education', 'Self_Employed',
            'ApplicantIncome', 'CoapplicantIncome', 'LoanAmount',
            'Loan_Amount_Term', 'Credit_History', 'Property_Area', 'Loan_Status'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Basic data info
        print(f"Approval rate: {(df['Loan_Status'] == 'Y').mean():.1%}")
        print(f"Missing values: {df.isnull().sum().sum()}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None

def preprocess_data(df):
    """Enhanced preprocessing for comprehensive training data."""
    print("Preprocessing comprehensive data...")
    
    # Make a copy
    data = df.copy()
    
    # Handle missing values
    for col in data.columns:
        if data[col].dtype == 'object':
            data[col] = data[col].fillna(data[col].mode()[0] if not data[col].mode().empty else 'Unknown')
        else:
            data[col] = data[col].fillna(data[col].median())
    
    # Enhanced categorical mappings
    categorical_mappings = {
        'Gender': {'Male': 1, 'Female': 0},
        'Married': {'Yes': 1, 'No': 0},
        'Education': {'Graduate': 1, 'Not Graduate': 0},
        'Self_Employed': {'Yes': 1, 'No': 0},
        'SpouseEmployed': {True: 1, False: 0},
        'Property_Area': {'Urban': 2, 'Semiurban': 1, 'Rural': 0},
        'Loan_Status': {'Y': 1, 'N': 0},
        
        # Employment mappings
        'EmploymentType': {
            'Government': 4, 'Salaried': 3, 'Self-Employed': 2, 
            'Business Owner': 1, 'Freelancer': 0
        },
        'EmployerCategory': {'A': 4, 'MNC': 3, 'B': 2, 'SME': 1, 'C': 0},
        'Industry': {
            'Finance': 6, 'IT': 5, 'Government': 4, 'Healthcare': 3,
            'Manufacturing': 2, 'Education': 1, 'Retail': 0, 'Others': 0
        },
        
        # Loan mappings
        'LoanPurpose': {
            'Home': 5, 'Education': 4, 'Business': 3, 'Vehicle': 2,
            'Personal': 1, 'Medical': 0, 'Others': 0
        },
        
        # Asset mappings
        'HasVehicle': {True: 1, False: 0},
        'HasLifeInsurance': {True: 1, False: 0},
        'BankAccountType': {'Premium': 3, 'Current': 2, 'Savings': 1, 'Basic': 0},
        'CollateralType': {'Property': 3, 'Vehicle': 2, 'Fixed Deposit': 1, 'None': 0},
        'CityTier': {'Tier-1': 2, 'Tier-2': 1, 'Tier-3': 0}
    }
    
    for col, mapping in categorical_mappings.items():
        if col in data.columns:
            data[col] = data[col].map(mapping).fillna(0)
    
    # Handle dependents (convert to numeric)
    if 'Dependents' in data.columns:
        data['Dependents'] = data['Dependents'].astype(str).str.replace('+', '', regex=False)
        data['Dependents'] = pd.to_numeric(data['Dependents'], errors='coerce').fillna(0)
    
    # Create enhanced derived features
    data['TotalIncome'] = data['ApplicantIncome'] + data['CoapplicantIncome']
    data['NetIncome'] = data['TotalIncome'] - data.get('MonthlyExpenses', 0)
    data['EMI'] = data['LoanAmount'] / data['Loan_Amount_Term'] * 1000  # Convert to monthly EMI
    data['TotalEMI'] = data['EMI'] + data.get('OtherEMIs', 0)
    data['EMI_Income_Ratio'] = data['TotalEMI'] / (data['TotalIncome'] / 12)
    data['Debt_To_Income_Ratio'] = data['TotalEMI'] / data['TotalIncome']
    
    # Credit-related features
    data['Credit_Utilization'] = data.get('NoOfCreditCards', 0) / 10  # Normalize credit cards
    data['Default_Risk_Score'] = (
        data.get('LoanDefaultHistory', 0) * 20 + 
        data.get('AvgPaymentDelayDays', 0) / 30 * 10
    )
    
    # Income stability features
    data['Income_Per_Year_Experience'] = data['TotalIncome'] / (data.get('YearsInCurrentJob', 1) + 1)
    data['Savings_Capacity'] = (data.get('SavingsScore', 0) / 100) * data['TotalIncome']
    
    # Collateral coverage
    data['Collateral_Coverage'] = (data.get('CollateralValue', 0) / 
                                  (data['LoanAmount'] * 1000 + 1))  # Avoid division by zero
    
    # Age-related features
    if 'Age' in data.columns:
        data['Age_Group'] = pd.cut(data['Age'], bins=[0, 25, 35, 45, 55, 100], 
                                  labels=[0, 1, 2, 3, 4]).astype(float)
    
    # Geographic risk
    data['Geographic_Risk'] = data.get('RegionDefaultRate', 5) / 100
    
    # Replace infinite values
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.fillna(0)
    
    print(f"✓ Enhanced preprocessing complete. Shape: {data.shape}")
    print(f"✓ Created {len([col for col in data.columns if col.endswith('_Ratio') or col.endswith('_Score')])} derived features")
    
    return data

def train_model(X, y, model_type='xgboost'):
    """Train the enhanced model."""
    print(f"Training {model_type} model with {X.shape[1]} features...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Training set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    print(f"Class distribution - Approved: {y_train.sum()}, Rejected: {len(y_train) - y_train.sum()}")
    
    # Train model based on type
    if model_type.lower() == 'xgboost':
        try:
            import xgboost as xgb
            model = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                eval_metric='logloss',
                scale_pos_weight=len(y_train[y_train==0]) / len(y_train[y_train==1])  # Handle class imbalance
            )
        except ImportError:
            print("XGBoost not available, using RandomForest instead")
            model = RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
    elif model_type.lower() == 'randomforest':
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            random_state=42,
            class_weight='balanced',
            min_samples_split=5,
            min_samples_leaf=2
        )
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    
    # Train model
    model.fit(X_train, y_train)
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    print(f"Training accuracy: {train_score:.3f}")
    print(f"Test accuracy: {test_score:.3f}")
    
    # Predictions for detailed report
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Rejected', 'Approved']))
    
    # Feature importance
    if hasattr(model, 'feature_importances_'):
        feature_importance = dict(zip(X.columns, model.feature_importances_))
        print("\n🔝 Top 15 Most Important Features:")
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:15]
        for i, (feature, importance) in enumerate(sorted_features, 1):
            print(f"  {i:2d}. {feature}: {importance:.4f}")
    
    # Model performance by risk categories
    print("\n📊 Performance Analysis:")
    print(f"   Precision (Approved): {precision_score(y_test, y_pred):.3f}")
    print(f"   Recall (Approved): {recall_score(y_test, y_pred):.3f}")
    print(f"   F1-Score (Approved): {f1_score(y_test, y_pred):.3f}")
    
    return model, test_score, feature_importance

def save_model_and_preprocessor(model, feature_names, model_path, preprocessor_path, feature_importance):
    """Save model and create enhanced preprocessor info."""
    print("Saving enhanced model and preprocessor...")
    
    # Create directories
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    Path(preprocessor_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save model
    joblib.dump(model, model_path)
    print(f"✓ Enhanced model saved to {model_path}")
    
    # Create comprehensive preprocessor info
    preprocessor_info = {
        'feature_names': list(feature_names),
        'feature_importance': feature_importance,
        'categorical_mappings': {
            'Gender': {'Male': 1, 'Female': 0},
            'Married': {'Yes': 1, 'No': 0},
            'Education': {'Graduate': 1, 'Not Graduate': 0},
            'Self_Employed': {'Yes': 1, 'No': 0},
            'SpouseEmployed': {True: 1, False: 0},
            'Property_Area': {'Urban': 2, 'Semiurban': 1, 'Rural': 0},
            
            # Enhanced mappings
            'EmploymentType': {
                'Government': 4, 'Salaried': 3, 'Self-Employed': 2, 
                'Business Owner': 1, 'Freelancer': 0
            },
            'EmployerCategory': {'A': 4, 'MNC': 3, 'B': 2, 'SME': 1, 'C': 0},
            'Industry': {
                'Finance': 6, 'IT': 5, 'Government': 4, 'Healthcare': 3,
                'Manufacturing': 2, 'Education': 1, 'Retail': 0, 'Others': 0
            },
            'LoanPurpose': {
                'Home': 5, 'Education': 4, 'Business': 3, 'Vehicle': 2,
                'Personal': 1, 'Medical': 0, 'Others': 0
            },
            'HasVehicle': {True: 1, False: 0},
            'HasLifeInsurance': {True: 1, False: 0},
            'BankAccountType': {'Premium': 3, 'Current': 2, 'Savings': 1, 'Basic': 0},
            'CollateralType': {'Property': 3, 'Vehicle': 2, 'Fixed Deposit': 1, 'None': 0},
            'CityTier': {'Tier-1': 2, 'Tier-2': 1, 'Tier-3': 0}
        },
        'model_type': str(type(model).__name__),
        'feature_categories': {
            'credit_features': [
                'CreditScore', 'Credit_History', 'NoOfCreditCards', 
                'LoanDefaultHistory', 'AvgPaymentDelayDays', 'Credit_Utilization', 'Default_Risk_Score'
            ],
            'income_features': [
                'ApplicantIncome', 'CoapplicantIncome', 'TotalIncome', 'NetIncome',
                'MonthlyExpenses', 'OtherEMIs', 'BankBalance', 'SavingsScore', 'Savings_Capacity'
            ],
            'employment_features': [
                'EmploymentType', 'YearsInCurrentJob', 'EmployerCategory', 
                'Industry', 'Income_Per_Year_Experience'
            ],
            'loan_features': [
                'LoanAmount', 'Loan_Amount_Term', 'LoanPurpose', 'EMI', 
                'EMI_Income_Ratio', 'Debt_To_Income_Ratio'
            ],
            'collateral_features': [
                'CollateralType', 'CollateralValue', 'Collateral_Coverage'
            ]
        }
    }
    
    joblib.dump(preprocessor_info, preprocessor_path)
    print(f"✓ Enhanced preprocessor info saved to {preprocessor_path}")

def main():
    parser = argparse.ArgumentParser(description='Train comprehensive loan approval model')
    parser.add_argument('--data', required=True, help='Path to training CSV file')
    parser.add_argument('--model-type', default='xgboost', choices=['randomforest', 'xgboost'])
    
    args = parser.parse_args()
    
    print("🚀 Starting Enhanced Model Training...")
    print("=" * 60)
    
    # Load data
    df = load_and_prepare_data(args.data)
    if df is None:
        sys.exit(1)
    
    # Preprocess
    processed_data = preprocess_data(df)
    
    # Prepare features and target
    target_col = 'Loan_Status'
    exclude_cols = [target_col, 'Pincode']  # Exclude target and non-numeric identifiers
    feature_cols = [col for col in processed_data.columns if col not in exclude_cols]
    
    X = processed_data[feature_cols]
    y = processed_data[target_col]
    
    print(f"\n📊 Training Data Summary:")
    print(f"   Total Features: {len(feature_cols)}")
    print(f"   Samples: {len(X)}")
    print(f"   Target distribution: Approved={y.sum()}, Rejected={len(y)-y.sum()}")
    print(f"   Approval rate: {y.mean():.1%}")
    
    # Train model
    model, accuracy, feature_importance = train_model(X, y, args.model_type)
    
    # Save model with enhanced features
    model_path = "data/models/loan_model.pkl"
    preprocessor_path = "data/models/preprocessor.pkl"
    
    save_model_and_preprocessor(model, X.columns, model_path, preprocessor_path, feature_importance)
    
    print(f"\n" + "=" * 60)
    print(f"🎉 Enhanced Training Completed Successfully!")
    print(f"   Final Test Accuracy: {accuracy:.3f}")
    print(f"   Model Type: {args.model_type}")
    print(f"   Features Used: {len(feature_cols)}")
    print(f"   Model saved to: {model_path}")
    print(f"\n📋 Next Steps:")
    print("1. Restart your FastAPI application to load the new model")
    print("2. Test predictions with the enhanced features")
    print("3. Check the API docs at http://localhost:8000/docs for the new schema")

if __name__ == "__main__":
    main()