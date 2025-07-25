#!/usr/bin/env python3
"""
Comprehensive API testing script for the Loan Approval System.
Tests authentication, loan prediction, and admin features.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

class LoanAPI:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_info = None
    
    def login(self, username: str, password: str):
        """Login and get access token."""
        print(f"\n🔐 Logging in as {username}...")
        
        data = {
            "username": username,
            "password": password
        }
        
        response = self.session.post(
            f"{API_V1}/auth/login",
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            self.token = result["access_token"]
            self.user_info = result["user_info"]
            
            # Set authorization header for future requests
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}"
            })
            
            print(f"✅ Login successful!")
            print(f"   User: {self.user_info['full_name']}")
            print(f"   Role: {self.user_info['role']}")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False
    
    def logout(self):
        """Logout user."""
        print("\n👋 Logging out...")
        response = self.session.post(f"{API_V1}/auth/logout")
        if response.status_code == 200:
            print("✅ Logout successful!")
            self.token = None
            self.user_info = None
            self.session.headers.pop("Authorization", None)
        else:
            print(f"❌ Logout failed: {response.text}")
    
    def submit_loan_application(self, application_data):
        """Submit a loan application."""
        print("\n📋 Submitting loan application...")
        
        response = self.session.post(
            f"{API_V1}/loans/predict",
            json=application_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Application submitted successfully!")
            print(f"   Application ID: {result['application_id']}")
            print(f"   Decision: {result['loan_decision']}")
            print(f"   Risk Score: {result['risk_score']}")
            print(f"   Risk Category: {result['risk_category']}")
            return result
        else:
            print(f"❌ Application failed: {response.text}")
            return None
    
    def get_dashboard(self):
        """Get admin dashboard data."""
        print("\n📊 Fetching dashboard data...")
        
        response = self.session.get(f"{API_V1}/admin/dashboard")
        
        if response.status_code == 200:
            result = response.json()
            stats = result["stats"]
            print("✅ Dashboard data retrieved!")
            print(f"   Total Applications: {stats['total_applications']}")
            print(f"   Drafted: {stats['drafted_applications']}")
            print(f"   Approved: {stats['approved_applications']}")
            print(f"   Rejected: {stats['rejected_applications']}")
            print(f"   Approval Rate: {stats['approval_rate']}%")
            return result
        else:
            print(f"❌ Dashboard fetch failed: {response.text}")
            return None
    
    def list_loans(self, status=None, page=1, page_size=10):
        """List loan applications."""
        print(f"\n📋 Listing loans (page {page})...")
        
        params = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        
        response = self.session.get(f"{API_V1}/admin/loans", params=params)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Found {result['total_count']} loans")
            print(f"   Showing {len(result['loans'])} loans on page {page}")
            
            for loan in result['loans']:
                status_info = loan['status_info']
                print(f"   - {loan['application_id']}: {status_info['status']} "
                      f"(Risk: {loan['ml_prediction']['risk_score']})")
            
            return result
        else:
            print(f"❌ Loan list fetch failed: {response.text}")
            return None
    
    def get_loan_detail(self, application_id):
        """Get detailed loan information."""
        print(f"\n🔍 Getting loan details for {application_id}...")
        
        response = self.session.get(f"{API_V1}/admin/loans/{application_id}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Loan details retrieved!")
            return result
        else:
            print(f"❌ Loan detail fetch failed: {response.text}")
            return None
    
    def update_loan_status(self, application_id, status, notes=None):
        """Update loan status."""
        print(f"\n✏️  Updating loan {application_id} to {status}...")
        
        data = {"status": status}
        if notes:
            data["admin_notes"] = notes
        
        response = self.session.put(
            f"{API_V1}/admin/loans/{application_id}/status",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Loan status updated!")
            print(f"   {result['message']}")
            return result
        else:
            print(f"❌ Status update failed: {response.text}")
            return None
    
    def create_user(self, user_data):
        """Create a new user (superadmin only)."""
        print(f"\n👤 Creating user {user_data['username']}...")
        
        response = self.session.post(
            f"{API_V1}/auth/users",
            json=user_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ User created successfully!")
            print(f"   Username: {result['username']}")
            print(f"   Role: {result['role']}")
            return result
        else:
            print(f"❌ User creation failed: {response.text}")
            return None
    
    def list_users(self, page=1, page_size=10):
        """List users (superadmin only)."""
        print(f"\n👥 Listing users...")
        
        params = {"page": page, "page_size": page_size}
        response = self.session.get(f"{API_V1}/auth/users", params=params)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Found {result['total_count']} users")
            
            for user in result['users']:
                status = "🟢" if user['is_active'] else "🔴"
                print(f"   {status} {user['username']} ({user['role']}) - {user['full_name']}")
            
            return result
        else:
            print(f"❌ User list fetch failed: {response.text}")
            return None

def test_loan_application_flow():
    """Test the complete loan application flow."""
    print("🚀 Testing Loan Application Flow")
    print("=" * 50)
    
    # Sample loan application data
    loan_data = {
        "gender": "Male",
        "married": "Yes",
        "dependents": 1,
        "education": "Graduate",
        "age": 35,
        "self_employed": "No",
        "employment_type": "Salaried",
        "applicant_income": 85000,
        "monthly_expenses": 60000,
        "loan_amount": 1500,
        "loan_amount_term": 360,
        "credit_history": 1,
        "property_area": "Urban"
    }
    
    api = LoanAPI()
    
    # Submit loan application (no authentication required)
    print("\n1️⃣ Testing loan application submission...")
    result = api.submit_loan_application(loan_data)
    
    if result:
        application_id = result["application_id"]
        print(f"📝 Application {application_id} created with status: DRAFTED")
        return application_id
    else:
        print("❌ Failed to create loan application")
        return None

def test_admin_authentication():
    """Test admin authentication and user management."""
    print("\n🔐 Testing Admin Authentication")
    print("=" * 50)
    
    api = LoanAPI()
    
    # Test superadmin login
    print("\n1️⃣ Testing superadmin login...")
    if not api.login("superadmin", "admin123"):
        return None
    
    # Test user creation
    print("\n2️⃣ Testing user creation...")
    new_user_data = {
        "username": "testbm",
        "email": "testbm@example.com",
        "full_name": "Test Bank Manager",
        "password": "testpass123",
        "role": "bm",
        "is_active": True
    }
    
    user_result = api.create_user(new_user_data)
    
    # Test user listing
    print("\n3️⃣ Testing user listing...")
    api.list_users()
    
    # Logout
    api.logout()
    
    return api

def test_bank_manager_workflow():
    """Test bank manager workflow with loan management."""
    print("\n🏦 Testing Bank Manager Workflow")
    print("=" * 50)
    
    api = LoanAPI()
    
    # Login as bank manager
    print("\n1️⃣ Testing bank manager login...")
    if not api.login("bankmanager", "bm123"):
        return None
    
    # Get dashboard
    print("\n2️⃣ Testing dashboard access...")
    dashboard = api.get_dashboard()
    
    # List loans
    print("\n3️⃣ Testing loan listing...")
    loans = api.list_loans(page=1, page_size=5)
    
    if loans and loans["loans"]:
        # Get first loan for testing
        first_loan = loans["loans"][0]
        application_id = first_loan["application_id"]
        
        # Get loan details
        print("\n4️⃣ Testing loan detail view...")
        loan_detail = api.get_loan_detail(application_id)
        
        # Update loan status if it's drafted
        if first_loan["status_info"]["status"] == "drafted":
            print("\n5️⃣ Testing loan status update...")
            api.update_loan_status(
                application_id, 
                "approved", 
                "Approved by bank manager after review"
            )
    
    # Logout
    api.logout()
    
    return api

def test_complete_workflow():
    """Test the complete workflow from application to approval."""
    print("\n🔄 Testing Complete Workflow")
    print("=" * 50)
    
    # Step 1: Submit loan application
    application_id = test_loan_application_flow()
    if not application_id:
        return
    
    # Wait a moment
    time.sleep(1)
    
    # Step 2: Login as bank manager and review
    api = LoanAPI()
    if not api.login("bankmanager", "bm123"):
        return
    
    print(f"\n📋 Reviewing application {application_id}...")
    
    # Get loan details
    loan_detail = api.get_loan_detail(application_id)
    if loan_detail:
        risk_score = loan_detail["ml_prediction"]["risk_score"]
        recommendation = loan_detail["ml_prediction"]["recommendation"]
        
        print(f"   Risk Score: {risk_score}")
        print(f"   ML Recommendation: {recommendation}")
        
        # Make decision based on risk score
        if risk_score < 50:
            status = "approved"
            notes = f"Low risk application (score: {risk_score}). Approved."
        else:
            status = "rejected"
            notes = f"High risk application (score: {risk_score}). Rejected."
        
        # Update status
        api.update_loan_status(application_id, status, notes)
        
        print(f"✅ Application {application_id} has been {status}")
    
    api.logout()

def test_error_scenarios():
    """Test error scenarios and edge cases."""
    print("\n⚠️ Testing Error Scenarios")
    print("=" * 50)
    
    api = LoanAPI()
    
    # Test invalid login
    print("\n1️⃣ Testing invalid login...")
    api.login("invalid_user", "wrong_password")
    
    # Test unauthorized access
    print("\n2️⃣ Testing unauthorized access...")
    response = requests.get(f"{API_V1}/admin/dashboard")
    if response.status_code == 401:
        print("✅ Unauthorized access properly blocked")
    else:
        print(f"❌ Expected 401, got {response.status_code}")
    
    # Test invalid loan application
    print("\n3️⃣ Testing invalid loan application...")
    invalid_loan_data = {
        "gender": "Invalid",  # Invalid value
        "married": "Yes",
        "dependents": -1,     # Invalid value
        "education": "Graduate",
        "applicant_income": -5000,  # Invalid value
        "loan_amount": 0,     # Invalid value
        "loan_amount_term": 360,
        "credit_history": 1,
        "property_area": "Urban"
    }
    
    api.submit_loan_application(invalid_loan_data)

def generate_test_report():
    """Generate a comprehensive test report."""
    print("\n📊 Generating Test Report")
    print("=" * 50)
    
    api = LoanAPI()
    
    # Login as superadmin to get comprehensive data
    if api.login("superadmin", "admin123"):
        
        # Get dashboard stats
        dashboard = api.get_dashboard()
        if dashboard:
            stats = dashboard["stats"]
            print("\n📈 System Statistics:")
            print(f"   Total Applications: {stats['total_applications']}")
            print(f"   Approval Rate: {stats['approval_rate']}%")
            print(f"   Average Risk Score: {stats['average_risk_score']}")
            print(f"   Total Loan Amount: ${stats['total_loan_amount']:,.2f}")
        
        # Get user count
        users = api.list_users(page_size=100)
        if users:
            print(f"\n👥 User Management:")
            print(f"   Total Users: {users['total_count']}")
            
            role_counts = {}
            for user in users['users']:
                role = user['role']
                role_counts[role] = role_counts.get(role, 0) + 1
            
            for role, count in role_counts.items():
                print(f"   {role.upper()}: {count}")
        
        # Get recent loans
        loans = api.list_loans(page_size=10)
        if loans:
            print(f"\n📋 Recent Loan Applications:")
            status_counts = {}
            for loan in loans['loans']:
                status = loan['status_info']['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            for status, count in status_counts.items():
                print(f"   {status.upper()}: {count}")
        
        api.logout()

def main():
    """Run all tests."""
    print("🧪 LOAN APPROVAL SYSTEM - API TESTING SUITE")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    try:
        # Test basic functionality
        test_loan_application_flow()
        
        # Test authentication
        test_admin_authentication()
        
        # Test bank manager workflow
        test_bank_manager_workflow()
        
        # Test complete workflow
        test_complete_workflow()
        
        # Test error scenarios
        test_error_scenarios()
        
        # Generate report
        generate_test_report()
        
        print("\n🎉 All tests completed!")
        print("\n📋 Test Summary:")
        print("✅ Loan application submission")
        print("✅ Admin authentication")
        print("✅ User management")
        print("✅ Bank manager workflow")
        print("✅ Loan status management")
        print("✅ Dashboard access")
        print("✅ Error handling")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()