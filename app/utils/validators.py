from typing import Dict, Any, List
from pydantic import ValidationError
import logging

from app.utils.exceptions import ValidationError as CustomValidationError

logger = logging.getLogger(__name__)

class LoanValidator:
    """Validator for loan application data."""
    
    def __init__(self):
        self.required_fields = [
            'gender', 'married', 'dependents', 'education', 'self_employed',
            'applicant_income', 'coapplicant_income', 'loan_amount',
            'loan_amount_term', 'credit_history', 'property_area'
        ]
        
        self.valid_values = {
            'gender': ['Male', 'Female'],
            'married': ['Yes', 'No'],
            'education': ['Graduate', 'Not Graduate'],
            'self_employed': ['Yes', 'No'],
            'property_area': ['Urban', 'Semiurban', 'Rural'],
            'credit_history': [0, 1]
        }
    
    def validate_loan_application(self, data: Dict[str, Any]) -> None:
        """Validate loan application data."""
        errors = []
        
        # Check required fields
        for field in self.required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Field '{field}' is required")
        
        if errors:
            raise CustomValidationError(f"Missing required fields: {', '.join(errors)}")
        
        # Validate field values
        for field, valid_vals in self.valid_values.items():
            if field in data and data[field] not in valid_vals:
                errors.append(f"Field '{field}' must be one of {valid_vals}")
        
        # Validate numerical constraints
        if data.get('applicant_income', 0) <= 0:
            errors.append("Applicant income must be positive")
        
        if data.get('coapplicant_income', 0) < 0:
            errors.append("Co-applicant income cannot be negative")
        
        if data.get('loan_amount', 0) <= 0:
            errors.append("Loan amount must be positive")
        
        if data.get('loan_amount_term', 0) <= 0:
            errors.append("Loan amount term must be positive")
        
        if data.get('dependents', 0) < 0:
            errors.append("Number of dependents cannot be negative")
        
        # Business logic validations
        total_income = data.get('applicant_income', 0) + data.get('coapplicant_income', 0)
        if total_income < 1000:
            errors.append("Total household income is too low")
        
        # EMI validation
        if data.get('loan_amount') and data.get('loan_amount_term'):
            emi = data['loan_amount'] / data['loan_amount_term']
            emi_ratio = emi / total_income if total_income > 0 else float('inf')
            
            if emi_ratio > 0.8:  # EMI should not exceed 80% of income
                errors.append("EMI to income ratio is too high (>80%)")
        
        if errors:
            raise CustomValidationError(f"Validation errors: {'; '.join(errors)}")
