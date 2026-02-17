#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
import subprocess
import os

class SkillFlowAPITester:
    def __init__(self, base_url="https://sdc-manager.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_result(self, test_name, success, details="", response_data=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name} - {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def create_test_user(self):
        """Create test user and session using MongoDB"""
        print("\n🔧 Creating test user and session...")
        
        timestamp = int(datetime.now().timestamp())
        user_id = f"test-user-{timestamp}"
        session_token = f"test_session_{timestamp}"
        
        mongo_script = f'''
use('test_database');
var userId = '{user_id}';
var sessionToken = '{session_token}';
db.users.insertOne({{
  user_id: userId,
  email: 'test.user.{timestamp}@example.com',
  name: 'Test User HO',
  picture: 'https://via.placeholder.com/150',
  role: 'ho',
  assigned_sdc_id: null,
  created_at: new Date()
}});
db.user_sessions.insertOne({{
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
}});
print('Session token: ' + sessionToken);
print('User ID: ' + userId);
'''
        
        try:
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.session_token = session_token
                self.user_id = user_id
                print(f"✅ Test user created: {user_id}")
                print(f"✅ Session token: {session_token}")
                return True
            else:
                print(f"❌ MongoDB error: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Failed to create test user: {e}")
            return False

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make API request with authentication"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.session_token:
            headers['Authorization'] = f'Bearer {self.session_token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            return success, response_data, response.status_code
            
        except Exception as e:
            return False, str(e), 0

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, data, status = self.make_request('GET', '', expected_status=200)
        self.log_result("Root API endpoint", success, 
                       f"Status: {status}" if not success else "", data)

    def test_auth_me(self):
        """Test /auth/me endpoint"""
        success, data, status = self.make_request('GET', 'auth/me', expected_status=200)
        details = ""
        if not success:
            details = f"Status: {status}, Response: {data}"
        elif not isinstance(data, dict) or 'user_id' not in data:
            success = False
            details = "Invalid response format"
        
        self.log_result("Auth /me endpoint", success, details, data)

    def test_seed_data(self):
        """Test seed data endpoint (HO only)"""
        success, data, status = self.make_request('POST', 'seed-data', expected_status=200)
        details = ""
        if not success:
            details = f"Status: {status}, Response: {data}"
        elif not isinstance(data, dict) or 'message' not in data:
            success = False
            details = "Invalid response format"
        
        self.log_result("Seed sample data", success, details, data)

    def test_dashboard_overview(self):
        """Test dashboard overview endpoint"""
        success, data, status = self.make_request('GET', 'dashboard/overview', expected_status=200)
        details = ""
        if not success:
            details = f"Status: {status}, Response: {data}"
        elif not isinstance(data, dict) or 'commercial_health' not in data:
            success = False
            details = "Missing commercial_health in response"
        
        self.log_result("Dashboard overview", success, details, data)

    def test_sdcs_list(self):
        """Test SDCs list endpoint"""
        success, data, status = self.make_request('GET', 'sdcs', expected_status=200)
        details = ""
        if not success:
            details = f"Status: {status}, Response: {data}"
        elif not isinstance(data, list):
            success = False
            details = "Response should be a list"
        
        self.log_result("SDCs list", success, details, data)
        return data if success else []

    def test_sdc_detail(self, sdc_id):
        """Test SDC detail endpoint"""
        if not sdc_id:
            self.log_result("SDC detail", False, "No SDC ID available")
            return None
            
        success, data, status = self.make_request('GET', f'sdcs/{sdc_id}', expected_status=200)
        details = ""
        if not success:
            details = f"Status: {status}, Response: {data}"
        elif not isinstance(data, dict) or 'progress' not in data:
            success = False
            details = "Missing progress data in response"
        
        self.log_result(f"SDC detail ({sdc_id})", success, details, data)
        return data if success else None

    def test_financial_calculations(self, sdc_data):
        """Test financial calculations accuracy"""
        if not sdc_data or 'financial' not in sdc_data:
            self.log_result("Financial calculations", False, "No financial data available")
            return
        
        financial = sdc_data['financial']
        invoices = sdc_data.get('invoices', [])
        
        # Calculate expected values
        expected_billed = sum(inv.get('amount', 0) for inv in invoices)
        expected_paid = sum(inv.get('amount', 0) for inv in invoices if inv.get('status') == 'paid')
        expected_outstanding = expected_billed - expected_paid
        
        # Check calculations
        billed_correct = abs(financial.get('total_billed', 0) - expected_billed) < 0.01
        paid_correct = abs(financial.get('total_paid', 0) - expected_paid) < 0.01
        outstanding_correct = abs(financial.get('outstanding', 0) - expected_outstanding) < 0.01
        
        success = billed_correct and paid_correct and outstanding_correct
        details = ""
        if not success:
            details = f"Expected billed: {expected_billed}, got: {financial.get('total_billed', 0)}"
        
        self.log_result("Financial calculations", success, details)

    def test_holiday_aware_dates(self):
        """Test holiday-aware date calculation"""
        test_data = {
            "start_date": "2025-01-20",
            "training_hours": 40  # 5 days
        }
        
        success, data, status = self.make_request('POST', 'calculate-end-date', 
                                                data=test_data, expected_status=200)
        details = ""
        if not success:
            details = f"Status: {status}, Response: {data}"
        elif not isinstance(data, dict) or 'end_date' not in data:
            success = False
            details = "Missing end_date in response"
        
        self.log_result("Holiday-aware date calculation", success, details, data)

    def test_alerts_generation(self):
        """Test alerts generation (HO only)"""
        success, data, status = self.make_request('POST', 'alerts/generate', expected_status=200)
        details = ""
        if not success:
            details = f"Status: {status}, Response: {data}"
        elif not isinstance(data, dict) or 'message' not in data:
            success = False
            details = "Invalid response format"
        
        self.log_result("Alerts generation", success, details, data)

    def test_alerts_list(self):
        """Test alerts list endpoint"""
        success, data, status = self.make_request('GET', 'alerts', expected_status=200)
        details = ""
        if not success:
            details = f"Status: {status}, Response: {data}"
        elif not isinstance(data, list):
            success = False
            details = "Response should be a list"
        
        self.log_result("Alerts list", success, details, data)

    def test_role_based_access(self):
        """Test role-based access control"""
        # Test HO-only endpoints
        ho_endpoints = [
            ('POST', 'seed-data'),
            ('POST', 'alerts/generate'),
            ('GET', 'users')
        ]
        
        for method, endpoint in ho_endpoints:
            success, data, status = self.make_request(method, endpoint, 
                                                    expected_status=200 if method == 'GET' else 200)
            # Since we're using HO role, these should succeed
            self.log_result(f"HO access - {method} {endpoint}", success, 
                           f"Status: {status}" if not success else "")

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        cleanup_script = '''
use('test_database');
db.users.deleteMany({email: /test\.user\./});
db.user_sessions.deleteMany({session_token: /test_session/});
print('Test data cleaned up');
'''
        
        try:
            subprocess.run(['mongosh', '--eval', cleanup_script], 
                          capture_output=True, text=True, timeout=30)
            print("✅ Test data cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting SkillFlow CRM Backend API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        
        # Create test user
        if not self.create_test_user():
            print("❌ Failed to create test user. Exiting.")
            return False
        
        try:
            # Basic API tests
            self.test_root_endpoint()
            self.test_auth_me()
            
            # Seed data first
            self.test_seed_data()
            
            # Dashboard and data tests
            self.test_dashboard_overview()
            sdcs = self.test_sdcs_list()
            
            # Test SDC detail if we have SDCs
            sdc_data = None
            if sdcs and len(sdcs) > 0:
                sdc_data = self.test_sdc_detail(sdcs[0]['sdc_id'])
                if sdc_data:
                    self.test_financial_calculations(sdc_data)
            
            # Utility tests
            self.test_holiday_aware_dates()
            self.test_alerts_generation()
            self.test_alerts_list()
            
            # Security tests
            self.test_role_based_access()
            
        finally:
            # Always cleanup
            self.cleanup_test_data()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Print failed tests
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = SkillFlowAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())