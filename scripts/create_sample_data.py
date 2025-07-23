#!/usr/bin/env python3
"""
Create sample training data for the loan approval model.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def create_sample_data():
    """Create comprehensive sample loan data for training."""
    
    np.random.seed(42)  # For reproducible results
    
    # Number of samples
    n_samples = 2000
    
    # Define value distributions
    employment_types = ['Salaried', 'Self-Employed', 'Government', 'Freelancer', 'Business Owner']
    employer_categories = ['A', 'B', 'C', 'SME', 'MNC']
    industries = ['Finance', 'IT', 'Healthcare', 'Retail', 'Manufacturing', 'Government', 'Education', 'Others']
    loan_purposes = ['Home', 'Personal', 'Education', 'Business', 'Vehicle', 'Medical', 'Others']
    collateral_types = ['Property', 'Vehicle', 'Fixed Deposit', 'None']
    city_tiers = ['Tier-1', 'Tier-2', 'Tier-3']
    bank_account_types = ['Basic', 'Savings', 'Premium', 'Current']
    
    # Generate sample data
    data = []
    
    for i in range(n_samples):
        # Basic demographics
        gender = np.random.choice(['Male', 'Female'])
        age = int(np.random.normal(35, 8))
        age = max(22, min(65, age))  # Clamp age
        married = np.random.choice(['Yes', 'No'], p=[0.7, 0.3])
        dependents = np.random.choice([0, 1, 2, 3, 4], p=[0.3, 0.35, 0.25, 0.08, 0.02])
        children = min(dependents, max(0, int(np.random.poisson(1.2))))
        education = np.random.choice(['Graduate', 'Not Graduate'], p=[0.75, 0.25])
        spouse_employed = (married == 'Yes') and (np.random.random() < 0.6)
        
        # Employment & Stability
        employment_type = np.random.choice(employment_types, p=[0.6, 0.2, 0.1, 0.05, 0.05])
        self_employed = 'Yes' if employment_type in ['Self-Employed', 'Business Owner', 'Freelancer'] else 'No'
        
        years_in_job = np.random.exponential(4)
        years_in_job = min(years_in_job, 25)
        
        if employment_type in ['Salaried', 'Government']:
            employer_category = np.random.choice(employer_categories, p=[0.15, 0.25, 0.3, 0.1, 0.2])
        else:
            employer_category = np.random.choice(['SME', 'C'], p=[0.7, 0.3])
        
        industry = np.random.choice(industries)
        
        # Income calculation based on profile
        base_income = 30000  # Base monthly income
        
        # Education multiplier
        if education == 'Graduate':
            base_income *= np.random.uniform(1.3, 2.0)
        
        # Employment type multiplier
        employment_multipliers = {
            'Government': np.random.uniform(1.2, 1.6),
            'Salaried': np.random.uniform(0.8, 2.5),
            'Self-Employed': np.random.uniform(0.6, 3.0),
            'Freelancer': np.random.uniform(0.5, 2.0),
            'Business Owner': np.random.uniform(0.4, 4.0)
        }
        base_income *= employment_multipliers[employment_type]
        
        # Industry multiplier
        industry_multipliers = {
            'Finance': 1.4, 'IT': 1.5, 'Healthcare': 1.2,
            'Government': 1.1, 'Education': 0.9, 'Retail': 0.8,
            'Manufacturing': 1.0, 'Others': 0.9
        }
        base_income *= industry_multipliers.get(industry, 1.0)
        
        # Experience multiplier
        base_income *= (1 + years_in_job * 0.05)
        
        # Age factor
        if age < 25:
            base_income *= 0.7
        elif age > 50:
            base_income *= 0.9
        
        applicant_income = max(15000, base_income + np.random.normal(0, base_income * 0.2))
        
        # Co-applicant income
        if spouse_employed:
            coapplicant_income = applicant_income * np.random.uniform(0.3, 0.8)
        else:
            coapplicant_income = 0
        
        total_income = applicant_income + coapplicant_income
        
        # Monthly expenses (50-80% of total income)
        city_tier = np.random.choice(city_tiers, p=[0.4, 0.4, 0.2])
        expense_ratio = np.random.uniform(0.5, 0.8)
        if city_tier == 'Tier-1':
            expense_ratio *= 1.2
        elif city_tier == 'Tier-3':
            expense_ratio *= 0.8
        
        monthly_expenses = total_income * expense_ratio
        
        # Other EMIs (0-30% of income)
        other_emis = total_income * np.random.uniform(0, 0.3)
        
        # Credit profile
        credit_score = int(np.random.normal(700, 80))
        credit_score = max(300, min(850, credit_score))
        
        # Credit history based on credit score
        if credit_score >= 650:
            credit_history = np.random.choice([1, 0], p=[0.9, 0.1])
        else:
            credit_history = np.random.choice([1, 0], p=[0.3, 0.7])
        
        no_of_credit_cards = int(np.random.poisson(2)) if credit_score > 600 else int(np.random.poisson(0.5))
        no_of_credit_cards = min(no_of_credit_cards, 8)
        
        loan_default_history = 0
        if credit_score < 600:
            loan_default_history = int(np.random.poisson(1))
        elif credit_score < 700:
            loan_default_history = np.random.choice([0, 1], p=[0.8, 0.2])
        
        avg_payment_delay = 0
        if credit_score < 650:
            avg_payment_delay = np.random.exponential(10)
        elif credit_score < 750:
            avg_payment_delay = np.random.exponential(3)
        
        # Loan details
        loan_purpose = np.random.choice(loan_purposes, p=[0.35, 0.25, 0.1, 0.1, 0.1, 0.05, 0.05])
        
        # Loan amount based on income and purpose
        if loan_purpose == 'Home':
            loan_amount = total_income * np.random.uniform(60, 120) / 1000  # Convert to thousands
        elif loan_purpose == 'Personal':
            loan_amount = total_income * np.random.uniform(6, 24) / 1000
        elif loan_purpose == 'Vehicle':
            loan_amount = total_income * np.random.uniform(12, 36) / 1000
        else:
            loan_amount = total_income * np.random.uniform(6, 60) / 1000
        
        loan_amount = max(50, loan_amount)  # Minimum loan amount in thousands
        
        # Loan term based on purpose
        if loan_purpose == 'Home':
            loan_term = np.random.choice([240, 300, 360], p=[0.2, 0.3, 0.5])
        elif loan_purpose == 'Vehicle':
            loan_term = np.random.choice([36, 48, 60, 84], p=[0.3, 0.3, 0.3, 0.1])
        else:
            loan_term = np.random.choice([12, 24, 36, 48, 60], p=[0.2, 0.3, 0.3, 0.15, 0.05])
        
        # Interest rate
        requested_interest_rate = np.random.uniform(7.5, 15.0)
        
        # Assets and lifestyle
        has_vehicle = np.random.random() < (0.3 + (total_income / 100000) * 0.4)
        has_life_insurance = np.random.random() < (0.4 + (total_income / 100000) * 0.3)
        property_area = np.random.choice(['Urban', 'Semiurban', 'Rural'], p=[0.5, 0.3, 0.2])
        
        # Banking info
        bank_account_type = np.random.choice(bank_account_types, p=[0.2, 0.5, 0.2, 0.1])
        bank_balance = total_income * np.random.uniform(0.5, 6)  # 2 weeks to 6 months income
        savings_score = np.random.uniform(5, 25)  # 5-25% savings rate
        
        # Collateral
        if loan_purpose == 'Home':
            collateral_type = 'Property'
            collateral_value = loan_amount * 1000 * np.random.uniform(1.2, 2.0)
        elif loan_purpose == 'Vehicle':
            collateral_type = 'Vehicle'
            collateral_value = loan_amount * 1000 * np.random.uniform(1.0, 1.3)
        else:
            collateral_type = np.random.choice(['None', 'Fixed Deposit'], p=[0.8, 0.2])
            collateral_value = loan_amount * 1000 * 0.1 if collateral_type != 'None' else 0
        
        # Geographic info
        pincode = f"{np.random.randint(100000, 999999)}"
        region_default_rate = np.random.uniform(2, 8)  # 2-8% regional default rate
        
        # Calculate approval probability with enhanced factors
        approval_score = 0
        
        # Credit score (35% weight)
        if credit_score >= 750:
            approval_score += 0.35
        elif credit_score >= 650:
            approval_score += 0.25
        elif credit_score >= 550:
            approval_score += 0.1
        
        # Income adequacy (25% weight)
        net_income = total_income - monthly_expenses - other_emis
        loan_emi = (loan_amount * 1000) / loan_term
        if net_income > loan_emi * 1.5:
            approval_score += 0.25
        elif net_income > loan_emi:
            approval_score += 0.15
        
        # Employment stability (20% weight)
        if employment_type == 'Government':
            approval_score += 0.2
        elif employment_type == 'Salaried' and years_in_job > 2:
            approval_score += 0.15
        elif years_in_job > 5:
            approval_score += 0.1
        
        # Debt burden (10% weight)
        total_emi = loan_emi + other_emis
        emi_ratio = total_emi / total_income
        if emi_ratio < 0.4:
            approval_score += 0.1
        elif emi_ratio < 0.5:
            approval_score += 0.05
        
        # Collateral and other factors (10% weight)
        if collateral_type != 'None':
            approval_score += 0.05
        if has_life_insurance:
            approval_score += 0.02
        if bank_account_type in ['Premium', 'Current']:
            approval_score += 0.02
        if credit_history == 1:
            approval_score += 0.01
        
        # Add randomness
        approval_score += np.random.uniform(-0.1, 0.1)
        
        # Final decision
        loan_status = 'Y' if approval_score > 0.5 else 'N'
        
        data.append({
            # Basic Demographics
            'Gender': gender,
            'Age': age,
            'Married': married,
            'Dependents': str(dependents),
            'Children': children,
            'Education': education,
            'SpouseEmployed': spouse_employed,
            
            # Employment
            'Self_Employed': self_employed,
            'EmploymentType': employment_type,
            'YearsInCurrentJob': round(years_in_job, 1),
            'EmployerCategory': employer_category,
            'Industry': industry,
            
            # Income & Expenses
            'ApplicantIncome': int(applicant_income),
            'CoapplicantIncome': int(coapplicant_income),
            'MonthlyExpenses': int(monthly_expenses),
            'OtherEMIs': int(other_emis),
            
            # Loan Details
            'LoanAmount': int(loan_amount),
            'Loan_Amount_Term': loan_term,
            'LoanPurpose': loan_purpose,
            'RequestedInterestRate': round(requested_interest_rate, 1),
            
            # Credit Profile
            'CreditScore': credit_score,
            'Credit_History': credit_history,
            'NoOfCreditCards': no_of_credit_cards,
            'LoanDefaultHistory': loan_default_history,
            'AvgPaymentDelayDays': round(avg_payment_delay, 1),
            
            # Assets & Lifestyle
            'HasVehicle': has_vehicle,
            'HasLifeInsurance': has_life_insurance,
            'Property_Area': property_area,
            
            # Banking
            'BankAccountType': bank_account_type,
            'BankBalance': int(bank_balance),
            'SavingsScore': round(savings_score, 1),
            
            # Collateral
            'CollateralType': collateral_type,
            'CollateralValue': int(collateral_value),
            
            # Geographic
            'CityTier': city_tier,
            'Pincode': pincode,
            'RegionDefaultRate': round(region_default_rate, 1),
            
            # Target
            'Loan_Status': loan_status
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Print comprehensive statistics
    print(f"Generated {len(df)} comprehensive loan applications")
    print(f"Approval rate: {(df['Loan_Status'] == 'Y').mean():.1%}")
    print(f"Average credit score: {df['CreditScore'].mean():.0f}")
    
    print(f"\nEmployment type distribution:")
    print(df['EmploymentType'].value_counts())
    
    print(f"\nLoan purpose distribution:")
    print(df['LoanPurpose'].value_counts())
    
    print(f"\nCredit score ranges:")
    print(f"  Excellent (750+): {(df['CreditScore'] >= 750).sum()} ({(df['CreditScore'] >= 750).mean():.1%})")
    print(f"  Good (650-749): {((df['CreditScore'] >= 650) & (df['CreditScore'] < 750)).sum()} ({((df['CreditScore'] >= 650) & (df['CreditScore'] < 750)).mean():.1%})")
    print(f"  Fair (550-649): {((df['CreditScore'] >= 550) & (df['CreditScore'] < 650)).sum()} ({((df['CreditScore'] >= 550) & (df['CreditScore'] < 650)).mean():.1%})")
    print(f"  Poor (<550): {(df['CreditScore'] < 550).sum()} ({(df['CreditScore'] < 550).mean():.1%})")
    
    print(f"\nCity tier distribution:")
    print(df['CityTier'].value_counts())
    
    print(f"\nCollateral distribution:")
    print(df['CollateralType'].value_counts())
    
    return df
        
    #     # Credit history (major factor)
    #     credit_history = np.random.choice([1, 0], p=[0.8, 0.2])
        
    #     # Calculate EMI ratio for loan approval logic
    #     emi = loan_amount / loan_amount_term * 1000  # Convert to monthly EMI estimate
    #     emi_ratio = emi / (total_income / 12) if total_income > 0 else 1
        
    #     # Loan approval logic (realistic business rules)
    #     approval_score = 0
        
    #     # Credit history is most important
    #     if credit_history == 1:
    #         approval_score += 0.4
        
    #     # EMI to income ratio
    #     if emi_ratio < 0.3:
    #         approval_score += 0.3
    #     elif emi_ratio < 0.5:
    #         approval_score += 0.1
        
    #     # Income level
    #     if total_income > 5000:
    #         approval_score += 0.2
    #     elif total_income > 3000:
    #         approval_score += 0.1
        
    #     # Education
    #     if education == 'Graduate':
    #         approval_score += 0.1
        
    #     # Add some randomness
    #     approval_score += np.random.uniform(-0.1, 0.1)
        
    #     # Final decision
    #     loan_status = 'Y' if approval_score > 0.5 else 'N'
        
    #     data.append({
    #         'Gender': gender,
    #         'Married': married,
    #         'Dependents': str(dependents),
    #         'Education': education,
    #         'Self_Employed': self_employed,
    #         'ApplicantIncome': round(applicant_income),
    #         'CoapplicantIncome': round(coapplicant_income),
    #         'LoanAmount': round(loan_amount),
    #         'Loan_Amount_Term': loan_amount_term,
    #         'Credit_History': credit_history,
    #         'Property_Area': property_area,
    #         'Loan_Status': loan_status
    #     })
    
    # # Create DataFrame
    # df = pd.DataFrame(data)
    
    # # Print statistics
    # print(f"Generated {len(df)} loan applications")
    # print(f"Approval rate: {(df['Loan_Status'] == 'Y').mean():.1%}")
    # print(f"Credit history distribution: {df['Credit_History'].value_counts().to_dict()}")
    # print(f"Education distribution: {df['Education'].value_counts().to_dict()}")
    
    # return df

def main():
    # Create data directory if it doesn't exist
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    
    # Generate comprehensive sample data
    df = create_sample_data()
    
    # Save to CSV
    output_file = "data/raw/comprehensive_loan_data.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\n✓ Comprehensive sample data saved to {output_file}")
    print(f"✓ Ready for training: python scripts/train_model.py --data {output_file}")
    print(f"\n📊 Dataset Summary:")
    print(f"   Total Records: {len(df)}")
    print(f"   Features: {len(df.columns) - 1}")  # -1 for target column
    print(f"   Approval Rate: {(df['Loan_Status'] == 'Y').mean():.1%}")
    print(f"   Average Loan Amount: ₹{df['LoanAmount'].mean():.0f}K")
    print(f"   Average Credit Score: {df['CreditScore'].mean():.0f}")

if __name__ == "__main__":
    main()