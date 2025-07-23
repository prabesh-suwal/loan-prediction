import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from typing import Dict, Any, Optional
import joblib
from pathlib import Path

class LoanDataTransformer(BaseEstimator, TransformerMixin):
    """Custom transformer for loan data preprocessing."""
    
    def __init__(self):
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.imputers: Dict[str, SimpleImputer] = {}
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: list = []
        self.is_fitted: bool = False
        
        # Define categorical and numerical columns
        self.categorical_cols = [
            'gender', 'married', 'education', 'self_employed', 'property_area'
        ]
        self.numerical_cols = [
            'applicant_income', 'coapplicant_income', 'loan_amount',
            'loan_amount_term', 'dependents'
        ]
        
    def fit(self, X: pd.DataFrame, y=None):
        """Fit the transformer on training data."""
        X = X.copy()
        
        # Store feature names
        self.feature_names = list(X.columns)
        
        # Fit label encoders for categorical columns
        for col in self.categorical_cols:
            if col in X.columns:
                le = LabelEncoder()
                # Handle missing values by adding 'Unknown' category
                X[col] = X[col].fillna('Unknown')
                le.fit(X[col])
                self.label_encoders[col] = le
        
        # Fit imputers for numerical columns
        for col in self.numerical_cols:
            if col in X.columns:
                imputer = SimpleImputer(strategy='median')
                imputer.fit(X[[col]])
                self.imputers[col] = imputer
        
        # Apply preprocessing to get final features for scaler
        X_processed = self._apply_preprocessing(X)
        
        # Fit scaler on processed features
        self.scaler = StandardScaler()
        self.scaler.fit(X_processed)
        
        self.is_fitted = True
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform the data using fitted transformers."""
        if not self.is_fitted:
            raise ValueError("Transformer must be fitted before transform")
        
        X = X.copy()
        return self._apply_preprocessing(X, scale=True)
    
    def _apply_preprocessing(self, X: pd.DataFrame, scale: bool = False) -> pd.DataFrame:
        """Apply all preprocessing steps."""
        
        # Handle missing values and encode categoricals
        for col in self.categorical_cols:
            if col in X.columns:
                X[col] = X[col].fillna('Unknown')
                if col in self.label_encoders:
                    # Handle unseen categories
                    le = self.label_encoders[col]
                    X[col] = X[col].apply(
                        lambda x: x if x in le.classes_ else 'Unknown'
                    )
                    X[col] = le.transform(X[col])
        
        # Impute numerical columns
        for col in self.numerical_cols:
            if col in X.columns and col in self.imputers:
                X[col] = self.imputers[col].transform(X[[col]]).flatten()
        
        # Feature engineering
        X = self._create_derived_features(X)
        
        # Ensure credit_history is binary
        if 'credit_history' in X.columns:
            X['credit_history'] = X['credit_history'].fillna(0).astype(int)
        
        # Scale features if requested
        if scale and self.scaler is not None:
            # Get numerical columns for scaling
            scale_cols = [col for col in X.columns if X[col].dtype in ['int64', 'float64']]
            if scale_cols:
                X[scale_cols] = self.scaler.transform(X[scale_cols])
        
        return X
    
    def _create_derived_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Create derived features."""
        
        # Total income
        if 'applicant_income' in X.columns and 'coapplicant_income' in X.columns:
            X['total_income'] = X['applicant_income'] + X['coapplicant_income']
        
        # EMI calculation
        if 'loan_amount' in X.columns and 'loan_amount_term' in X.columns:
            X['emi'] = X['loan_amount'] / X['loan_amount_term']
            X['emi'] = X['emi'].replace([np.inf, -np.inf], 0).fillna(0)
        
        # EMI to Income Ratio
        if 'emi' in X.columns and 'total_income' in X.columns:
            X['emi_income_ratio'] = X['emi'] / X['total_income'].replace(0, 1)
            X['emi_income_ratio'] = X['emi_income_ratio'].replace([np.inf, -np.inf], 0).fillna(0)
        
        # Loan amount to income ratio
        if 'loan_amount' in X.columns and 'total_income' in X.columns:
            X['loan_income_ratio'] = X['loan_amount'] / X['total_income'].replace(0, 1)
            X['loan_income_ratio'] = X['loan_income_ratio'].replace([np.inf, -np.inf], 0).fillna(0)
        
        return X
    
    def save(self, filepath: str) -> None:
        """Save the fitted transformer."""
        joblib.dump(self, filepath)
    
    @classmethod
    def load(cls, filepath: str) -> 'LoanDataTransformer':
        """Load a fitted transformer."""
        return joblib.load(filepath)