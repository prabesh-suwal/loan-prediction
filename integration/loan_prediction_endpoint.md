# 🔌 API Integration Guide - Loan Prediction Endpoint

## 📋 Endpoint Overview

**Endpoint**: `POST /api/v1/loans/predict`  
**Purpose**: Submit loan application and receive real-time approval decision with comprehensive risk analysis  
**Response Time**: < 500ms  
**Content-Type**: `application/json`  

## 🎯 Request Specification

### Base URL
```
Development: http://localhost:8000
Production: https://your-domain.com
```

### Complete Request Structure
```http
POST /api/v1/loans/predict
Content-Type: application/json
Accept: application/json

{
  // Request body fields detailed below
}
```

## 📝 Request Body Fields

### 👤 Basic Demographics (6 fields)

| Field | Type | Required | Allowed Values | Validation | Description |
|-------|------|----------|---------------|------------|-------------|
| `name` | string | ✅ | min_length=2, max_length=100 | Full name of the applicant |
| `email` | string | ✅ | Valid email format | Email address of the applicant |
| `gender` | string | ✅ | `"Male"`, `"Female"` | Exact match | Applicant's gender |
| `married` | string | ✅ | `"Yes"`, `"No"` | Exact match | Marital status |
| `dependents` | integer | ✅ | `0` to `10` | Range validation | Number of dependents |
| `education` | string | ✅ | `"Graduate"`, `"Not Graduate"` | Exact match | Education level |
| `age` | integer | ✅ | `18` to `80` | Range validation | Applicant's age in years |
| `children` | integer | ❌ | `0` to `10` | Range validation | Number of children (default: 0) |

### 💼 Employment & Stability (6 fields)

| Field | Type | Required | Allowed Values | Validation | Description |
|-------|------|----------|---------------|------------|-------------|
| `self_employed` | string | ✅ | `"Yes"`, `"No"` | Exact match | Self-employment status |
| `employment_type` | string | ❌ | `"Salaried"`, `"Self-Employed"`, `"Government"`, `"Freelancer"`, `"Business Owner"` | Enum validation | Type of employment (default: "Salaried") |
| `years_in_current_job` | number | ❌ | `0.0` to `50.0` | Range, 1 decimal | Years at current job (default: 2.0) |
| `employer_category` | string | ❌ | `"A"`, `"B"`, `"C"`, `"SME"`, `"MNC"` | Enum validation | Employer quality rating (default: "B") |
| `industry` | string | ❌ | `"Finance"`, `"IT"`, `"Healthcare"`, `"Retail"`, `"Manufacturing"`, `"Government"`, `"Education"`, `"Others"` | Enum validation | Industry sector (default: "Others") |
| `spouse_employed` | boolean | ❌ | `true`, `false` | Boolean validation | Spouse employment status (default: false) |

### 💰 Financial Information (4 fields)

| Field | Type | Required | Allowed Values | Validation | Description |
|-------|------|----------|---------------|------------|-------------|
| `applicant_income` | number | ✅ | `> 0` | Must be positive | Monthly income of applicant (in currency units) |
| `coapplicant_income` | number | ❌ | `>= 0` | Non-negative | Co-applicant monthly income (default: 0) |
| `monthly_expenses` | number | ✅ | `>= 0` | Non-negative | Total monthly expenses |
| `other_emis` | number | ❌ | `>= 0` | Non-negative | Other existing EMI obligations (default: 0) |

### 🏦 Loan Details (4 fields)

| Field | Type | Required | Allowed Values | Validation | Description |
|-------|------|----------|---------------|------------|-------------|
| `loan_amount` | number | ✅ | `> 0` | Must be positive | Requested loan amount (in thousands) |
| `loan_amount_term` | number | ✅ | `> 0` | Must be positive | Loan term in months |
| `loan_purpose` | string | ❌ | `"Home"`, `"Personal"`, `"Education"`, `"Business"`, `"Vehicle"`, `"Medical"`, `"Others"` | Enum validation | Purpose of loan (default: "Personal") |
| `requested_interest_rate` | number | ❌ | `5.0` to `30.0` | Range validation | Desired interest rate % (optional) |

### 📊 Credit Profile (5 fields)

| Field | Type | Required | Allowed Values | Validation | Description |
|-------|------|----------|---------------|------------|-------------|
| `credit_score` | integer | ❌ | `300` to `850` | Range validation | Credit bureau score (default: 650) |
| `credit_history` | integer | ✅ | `0`, `1` | Exact values | Credit history: 1=Good, 0=Poor |
| `no_of_credit_cards` | integer | ❌ | `0` to `20` | Range validation | Number of credit cards (default: 1) |
| `loan_default_history` | integer | ❌ | `0` to `10` | Range validation | Past loan defaults count (default: 0) |
| `avg_payment_delay_days` | number | ❌ | `0.0` to `365.0` | Range validation | Average payment delay in days (default: 0) |

### 🏠 Assets & Lifestyle (3 fields)

| Field | Type | Required | Allowed Values | Validation | Description |
|-------|------|----------|---------------|------------|-------------|
| `has_vehicle` | boolean | ❌ | `true`, `false` | Boolean validation | Vehicle ownership (default: false) |
| `has_life_insurance` | boolean | ❌ | `true`, `false` | Boolean validation | Life insurance coverage (default: false) |
| `property_area` | string | ✅ | `"Urban"`, `"Semiurban"`, `"Rural"` | Exact match | Property location type |

### 🏧 Banking Information (3 fields)

| Field | Type | Required | Allowed Values | Validation | Description |
|-------|------|----------|---------------|------------|-------------|
| `bank_account_type` | string | ❌ | `"Basic"`, `"Savings"`, `"Premium"`, `"Current"` | Enum validation | Bank account type (default: "Savings") |
| `bank_balance` | number | ❌ | `>= 0` | Non-negative | Current bank balance (default: 50000) |
| `savings_score` | number | ❌ | `0.0` to `100.0` | Range validation | Savings rate % (default: 10.0) |

### 🔒 Collateral Information (2 fields)

| Field | Type | Required | Allowed Values | Validation | Description |
|-------|------|----------|---------------|------------|-------------|
| `collateral_type` | string | ❌ | `"Property"`, `"Vehicle"`, `"Fixed Deposit"`, `"None"` | Enum validation | Type of collateral (default: "None") |
| `collateral_value` | number | ❌ | `>= 0` | Non-negative | Collateral value in currency units (default: 0) |

### 📍 Geographic Information (3 fields)

| Field | Type | Required | Allowed Values | Validation | Description |
|-------|------|----------|---------------|------------|-------------|
| `city_tier` | string | ❌ | `"Tier-1"`, `"Tier-2"`, `"Tier-3"` | Enum validation | City classification (default: "Tier-2") |
| `pincode` | string | ❌ | 6-digit number | Regex: `^[0-9]{6}$` | Area pincode (default: "110001") |
| `region_default_rate` | number | ❌ | `0.0` to `100.0` | Range validation | Regional default rate % (default: 5.0) |

## 📨 Complete Request Example

### Minimal Request (Only Required Fields)
```json
{
  "gender": "Male",
  "married": "Yes",
  "dependents": 1,
  "education": "Graduate",
  "age": 32,
  "self_employed": "No",
  "applicant_income": 85000,
  "monthly_expenses": 60000,
  "loan_amount": 1500,
  "loan_amount_term": 360,
  "credit_history": 1,
  "property_area": "Urban"
}
```

### Complete Request (All Fields)
```json
{
  "gender": "Male",
  "married": "Yes",
  "dependents": 1,
  "education": "Graduate",
  "age": 32,
  "children": 1,
  "spouse_employed": true,
  "self_employed": "No",
  "employment_type": "Salaried",
  "years_in_current_job": 3.5,
  "employer_category": "MNC",
  "industry": "IT",
  "applicant_income": 85000,
  "coapplicant_income": 45000,
  "monthly_expenses": 60000,
  "other_emis": 15000,
  "loan_amount": 1500,
  "loan_amount_term": 360,
  "loan_purpose": "Home",
  "requested_interest_rate": 8.5,
  "credit_score": 750,
  "credit_history": 1,
  "no_of_credit_cards": 3,
  "loan_default_history": 0,
  "avg_payment_delay_days": 2.5,
  "has_vehicle": true,
  "has_life_insurance": true,
  "property_area": "Urban",
  "bank_account_type": "Premium",
  "bank_balance": 500000,
  "savings_score": 15.5,
  "collateral_type": "Property",
  "collateral_value": 2000000,
  "city_tier": "Tier-1",
  "pincode": "110001",
  "region_default_rate": 3.2
}
```

## 📤 Response Specification

### Success Response (200 OK)
```json
{
  "application_id": "LOAN_20250722_A1B2C3D4",
  "loan_decision": "Yes",
  "risk_score": 22,
  "risk_category": "Low",
  "justification": "Application approved based on excellent credit score, stable employment, and adequate income.",
  "recommendation": "Approve",
  "confidence_score": 0.89,
  "key_risk_factors": [],
  "key_positive_factors": [
    "Excellent credit score",
    "High income level",
    "Property collateral"
  ],
  "suggested_loan_amount": 1650000,
  "debt_to_income_ratio": 0.38,
  "credit_risk_score": 15,
  "income_risk_score": 25,
  "employment_risk_score": 10
}
```

### Response Field Details

| Field | Type | Description | Possible Values |
|-------|------|-------------|-----------------|
| `application_id` | string | Unique application identifier | "LOAN_YYYYMMDD_XXXXXXXX" |
| `loan_decision` | string | Final approval decision | "Yes", "No" |
| `risk_score` | integer | Overall risk score (0-100) | 0=lowest risk, 100=highest risk |
| `risk_category` | string | Risk classification | "Low", "Medium", "High" |
| `justification` | string | Human-readable explanation | Detailed reasoning for decision |
| `recommendation` | string | System recommendation | "Approve", "Reject", "Conditionally Approve" |
| `confidence_score` | number | Model confidence (0-1) | Higher = more confident |
| `key_risk_factors` | array | Primary risk factors | List of risk elements |
| `key_positive_factors` | array | Primary positive factors | List of positive elements |
| `suggested_loan_amount` | number | AI-suggested amount | Based on income analysis |
| `debt_to_income_ratio` | number | Debt ratio (0-1+) | 0.35 = 35% debt ratio |
| `credit_risk_score` | integer | Credit-specific risk (0-100) | Credit history, score, defaults |
| `income_risk_score` | integer | Income-specific risk (0-100) | Income adequacy, EMI burden |
| `employment_risk_score` | integer | Employment risk (0-100) | Job stability, type |

## ❌ Error Responses

### Validation Error (422 Unprocessable Entity)
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "credit_score"],
      "msg": "Credit score must be between 300 and 850",
      "input": 900,
      "ctx": {"limit_value": 850}
    }
  ]
}
```

### Service Unavailable (503 Service Unavailable)
```json
{
  "detail": "ML model not loaded. Please try again later."
}
```

### Internal Server Error (500 Internal Server Error)
```json
{
  "detail": "Prediction failed: Internal processing error"
}
```

## 🔧 Frontend Implementation Guidelines

### 1. Form Validation (Client-Side)

```javascript
// Field validation rules
const validationRules = {
  gender: {
    required: true,
    options: ['Male', 'Female']
  },
  age: {
    required: true,
    min: 18,
    max: 80,
    type: 'integer'
  },
  applicant_income: {
    required: true,
    min: 1,
    type: 'number'
  },
  credit_score: {
    required: false,
    min: 300,
    max: 850,
    type: 'integer',
    default: 650
  },
  pincode: {
    required: false,
    pattern: /^[0-9]{6}$/,
    default: '110001'
  }
  // ... add all fields
};

// Validation function
function validateField(fieldName, value) {
  const rule = validationRules[fieldName];
  
  if (rule.required && !value) {
    return 'This field is required';
  }
  
  if (rule.options && !rule.options.includes(value)) {
    return `Must be one of: ${rule.options.join(', ')}`;
  }
  
  if (rule.min && value < rule.min) {
    return `Must be at least ${rule.min}`;
  }
  
  if (rule.max && value > rule.max) {
    return `Must be at most ${rule.max}`;
  }
  
  if (rule.pattern && !rule.pattern.test(value)) {
    return 'Invalid format';
  }
  
  return null; // Valid
}
```

### 2. API Call Implementation

```javascript
// API call function
async function submitLoanApplication(formData) {
  try {
    // Validate required fields
    const requiredFields = [
      'gender', 'married', 'dependents', 'education', 'age',
      'self_employed', 'applicant_income', 'monthly_expenses',
      'loan_amount', 'loan_amount_term', 'credit_history', 'property_area'
    ];
    
    for (const field of requiredFields) {
      if (!formData[field] && formData[field] !== 0) {
        throw new Error(`${field} is required`);
      }
    }
    
    // Make API call
    const response = await fetch('/api/v1/loans/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(formData)
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'API request failed');
    }
    
    const result = await response.json();
    return result;
    
  } catch (error) {
    console.error('Loan application submission failed:', error);
    throw error;
  }
}

// Usage example
const formData = {
  gender: 'Male',
  married: 'Yes',
  dependents: 1,
  education: 'Graduate',
  age: 32,
  self_employed: 'No',
  applicant_income: 85000,
  monthly_expenses: 60000,
  loan_amount: 1500,
  loan_amount_term: 360,
  credit_history: 1,
  property_area: 'Urban'
};

submitLoanApplication(formData)
  .then(result => {
    console.log('Loan decision:', result.loan_decision);
    console.log('Risk score:', result.risk_score);
    // Handle success
  })
  .catch(error => {
    console.error('Error:', error.message);
    // Handle error
  });
```

### 3. Form Field Recommendations

#### Smart Defaults
```javascript
const smartDefaults = {
  children: 0,
  spouse_employed: false,
  employment_type: 'Salaried',
  years_in_current_job: 2.0,
  employer_category: 'B',
  industry: 'Others',
  coapplicant_income: 0,
  other_emis: 0,
  loan_purpose: 'Personal',
  credit_score: 650,
  no_of_credit_cards: 1,
  loan_default_history: 0,
  avg_payment_delay_days: 0,
  has_vehicle: false,
  has_life_insurance: false,
  bank_account_type: 'Savings',
  bank_balance: 50000,
  savings_score: 10.0,
  collateral_type: 'None',
  collateral_value: 0,
  city_tier: 'Tier-2',
  pincode: '110001',
  region_default_rate: 5.0
};
```

#### Conditional Field Logic
```javascript
// Show/hide fields based on other selections
function updateFieldVisibility(formData) {
  // Show spouse employment only if married
  const showSpouseEmployed = formData.married === 'Yes';
  
  // Show co-applicant income only if spouse is employed
  const showCoapplicantIncome = showSpouseEmployed && formData.spouse_employed;
  
  // Show collateral value only if collateral type is not 'None'
  const showCollateralValue = formData.collateral_type !== 'None';
  
  return {
    spouse_employed: showSpouseEmployed,
    coapplicant_income: showCoapplicantIncome,
    collateral_value: showCollateralValue
  };
}
```

### 4. Response Handling

```javascript
function handleLoanResponse(response) {
  const { 
    application_id,
    loan_decision, 
    risk_score, 
    risk_category,
    justification,
    recommendation,
    confidence_score,
    key_risk_factors,
    key_positive_factors,
    suggested_loan_amount
  } = response;
  
  // Update UI based on decision
  if (loan_decision === 'Yes') {
    showApprovalUI({
      applicationId: application_id,
      riskScore: risk_score,
      riskCategory: risk_category,
      explanation: justification,
      suggestedAmount: suggested_loan_amount,
      positiveFactors: key_positive_factors
    });
  } else {
    showRejectionUI({
      applicationId: application_id,
      riskScore: risk_score,
      explanation: justification,
      riskFactors: key_risk_factors
    });
  }
  
  // Show risk analysis
  displayRiskAnalysis({
    overall: risk_score,
    category: risk_category,
    confidence: confidence_score,
    breakdown: {
      credit: response.credit_risk_score,
      income: response.income_risk_score,
      employment: response.employment_risk_score
    }
  });
}
```

## 🚨 Common Validation Errors & Solutions

### 1. Enum Value Errors
```javascript
// Problem: Case sensitivity
❌ "gender": "male"  // lowercase
✅ "gender": "Male"  // correct case

// Problem: Invalid option
❌ "employment_type": "Employee"
✅ "employment_type": "Salaried"
```

### 2. Numeric Range Errors
```javascript
// Problem: Out of range
❌ "age": 17          // too young
✅ "age": 18          // minimum age

❌ "credit_score": 900 // too high
✅ "credit_score": 850 // maximum score
```

### 3. Data Type Errors
```javascript
// Problem: String instead of number
❌ "applicant_income": "85000"
✅ "applicant_income": 85000

// Problem: Number instead of boolean
❌ "has_vehicle": 1
✅ "has_vehicle": true
```

### 4. Missing Required Fields
```javascript
// Problem: Missing required field
❌ {
  "gender": "Male",
  // missing other required fields
}

✅ {
  "gender": "Male",
  "married": "Yes",
  "dependents": 1,
  "education": "Graduate",
  "age": 32,
  "self_employed": "No",
  "applicant_income": 85000,
  "monthly_expenses": 60000,
  "loan_amount": 1500,
  "loan_amount_term": 360,
  "credit_history": 1,
  "property_area": "Urban"
}
```

## 📊 Test Scenarios for Frontend

### Test Case 1: Minimum Viable Request
```json
{
  "gender": "Female",
  "married": "No",
  "dependents": 0,
  "education": "Graduate",
  "age": 25,
  "self_employed": "No",
  "applicant_income": 50000,
  "monthly_expenses": 30000,
  "loan_amount": 200,
  "loan_amount_term": 120,
  "credit_history": 1,
  "property_area": "Urban"
}
```

### Test Case 2: High-Risk Profile
```json
{
  "gender": "Male",
  "married": "No",
  "dependents": 3,
  "education": "Not Graduate",
  "age": 55,
  "self_employed": "Yes",
  "employment_type": "Freelancer",
  "years_in_current_job": 0.5,
  "applicant_income": 25000,
  "monthly_expenses": 22000,
  "other_emis": 8000,
  "loan_amount": 500,
  "loan_amount_term": 180,
  "credit_score": 520,
  "credit_history": 0,
  "loan_default_history": 2,
  "property_area": "Rural"
}
```

### Test Case 3: Excellent Profile
```json
{
  "gender": "Female",
  "married": "Yes",
  "dependents": 1,
  "education": "Graduate",
  "age": 35,
  "spouse_employed": true,
  "self_employed": "No",
  "employment_type": "Government",
  "years_in_current_job": 8.5,
  "employer_category": "A",
  "industry": "Government",
  "applicant_income": 95000,
  "coapplicant_income": 65000,
  "monthly_expenses": 80000,
  "loan_amount": 2500,
  "loan_amount_term": 300,
  "credit_score": 785,
  "credit_history": 1,
  "has_life_insurance": true,
  "collateral_type": "Property",
  "collateral_value": 4500000,
  "property_area": "Urban"
}
```

## 🔗 Additional Resources

- **Interactive API Documentation**: `http://localhost:8000/docs`
- **Health Check Endpoint**: `GET /health`
- **Model Information**: `GET /api/v1/model/info`

This comprehensive guide should provide your frontend developer with everything needed for successful API integration! 🚀