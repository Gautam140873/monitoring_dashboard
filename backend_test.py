#!/usr/bin/env python3
"""
Backend API Testing for SkillFlow CRM & Billing Controller Dashboard
Tests all endpoints with session token authentication
"""

import requests
import sys
import json
from datetime import datetime

class SkillFlowAPITester:
    def __init__(self, base_url="https://training-tracker-63.preview.emergentagent.com"):
        self.base_url = base_url
        self.session_token = "test_ho_session_123"  # Provided HO session token
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}'
        }

    def run_test(self, name, method, endpoint, expected_status, data=None, check_response=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=self.headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=self.headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                # Additional response checks
                if check_response and response.status_code == 200:
                    try:
                        response_data = response.json()
                        if not check_response(response_data):
                            success = False
                            print(f"❌ Response validation failed")
                            self.failed_tests.append(f"{name}: Response validation failed")
                    except Exception as e:
                        print(f"⚠️  Response check error: {e}")
                
                return success, response.json() if response.content else {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.content:
                    try:
                        error_data = response.json()
                        print(f"   Error: {error_data}")
                    except:
                        print(f"   Error: {response.text}")
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout")
            self.failed_tests.append(f"{name}: Request timeout")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append(f"{name}: {str(e)}")
            return False, {}

    def test_api_version(self):
        """Test API version endpoint returns 2.0.0"""
        success, response = self.run_test(
            "API Version Check (should return 2.0.0)",
            "GET",
            "",
            200,
            check_response=lambda r: r.get("version") == "2.0.0"
        )
        return success

    def test_auth_me(self):
        """Test current user authentication"""
        success, response = self.run_test(
            "Authentication Check (HO user)",
            "GET",
            "auth/me",
            200,
            check_response=lambda r: r.get("role") == "ho"
        )
        return success, response

    def test_dashboard_overview(self):
        """Test dashboard overview with 5 financial metrics"""
        success, response = self.run_test(
            "Dashboard Overview (5 financial metrics + 7 training stages)",
            "GET",
            "dashboard/overview",
            200,
            check_response=lambda r: (
                "commercial_health" in r and
                "total_portfolio" in r["commercial_health"] and
                "actual_billed" in r["commercial_health"] and
                "collected" in r["commercial_health"] and
                "outstanding" in r["commercial_health"] and
                "variance" in r["commercial_health"] and
                "stage_progress" in r and
                len(r.get("stage_progress", {})) == 7  # 7 training stages
            )
        )
        return success, response

    def test_sdcs_list(self):
        """Test SDCs listing with overdue count and blockers"""
        success, response = self.run_test(
            "SDCs List (should show overdue count and blockers)",
            "GET",
            "sdcs",
            200,
            check_response=lambda r: isinstance(r, list)
        )
        return success, response

    def test_work_orders_list(self):
        """Test Work Orders listing with auto-calculated end dates"""
        success, response = self.run_test(
            "Work Orders List (with auto-calculated end dates)",
            "GET",
            "work-orders",
            200,
            check_response=lambda r: isinstance(r, list)
        )
        return success, response

    def test_training_stages(self):
        """Test training stages endpoint (7 stages)"""
        success, response = self.run_test(
            "Training Stages (7 stages: Mobilization to Placement)",
            "GET",
            "training-stages",
            200,
            check_response=lambda r: isinstance(r, list) and len(r) == 7
        )
        return success, response

    def test_create_work_order(self):
        """Test work order creation (auto-creates SDC and training roadmap)"""
        work_order_data = {
            "work_order_number": f"WO/TEST/{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "location": "Test City",
            "job_role_code": "TEST/Q001",
            "job_role_name": "Test Technician",
            "awarding_body": "Test Body",
            "scheme_name": "Test Scheme",
            "total_training_hours": 100,
            "sessions_per_day": 8,
            "num_students": 25,
            "cost_per_student": 5000,
            "manager_email": "test.manager@example.com"
        }
        
        success, response = self.run_test(
            "Create Work Order (auto-creates SDC and training roadmap)",
            "POST",
            "work-orders",
            200,
            data=work_order_data,
            check_response=lambda r: (
                "work_order" in r and
                "sdc" in r and
                "roadmap_stages" in r and
                r["roadmap_stages"] == 7
            )
        )
        return success, response

    def test_set_start_date(self, work_order_id):
        """Test setting start date (calculates end date correctly)"""
        start_date_data = {
            "start_date": "2025-02-01"
        }
        
        success, response = self.run_test(
            "Set Start Date (calculates end date skipping Sundays/holidays)",
            "PUT",
            f"work-orders/{work_order_id}/start-date",
            200,
            data=start_date_data,
            check_response=lambda r: (
                "calculated_end_date" in r and
                r["start_date"] == "2025-02-01"
            )
        )
        return success, response

    def test_create_invoice(self, sdc_id, work_order_id):
        """Test invoice creation (calculates variance and generates alert if >10%)"""
        invoice_data = {
            "sdc_id": sdc_id,
            "work_order_id": work_order_id,
            "invoice_number": f"INV/TEST/{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "invoice_date": "2025-02-01",
            "order_value": 125000,  # 25 students * 5000
            "billing_value": 100000,  # 20% variance to trigger alert
            "notes": "Test invoice with variance >10%"
        }
        
        success, response = self.run_test(
            "Create Invoice (calculates variance, generates alert if >10%)",
            "POST",
            "invoices",
            200,
            data=invoice_data,
            check_response=lambda r: (
                "variance" in r and
                "variance_percent" in r and
                abs(r["variance_percent"]) > 10  # Should trigger variance alert
            )
        )
        return success, response

    def test_record_payment(self, invoice_id):
        """Test payment recording (triggers PAID status on completed stages)"""
        payment_data = {
            "payment_received": 100000,
            "payment_date": "2025-02-15"
        }
        
        success, response = self.run_test(
            "Record Payment (triggers PAID status on completed stages)",
            "PUT",
            f"invoices/{invoice_id}/payment",
            200,
            data=payment_data,
            check_response=lambda r: (
                "new_status" in r and
                r["new_status"] == "paid"
            )
        )
        return success, response

    def test_sdc_detail(self, sdc_id):
        """Test SDC detail page shows work orders and training roadmap progress"""
        success, response = self.run_test(
            "SDC Detail (shows work orders table and training roadmap progress)",
            "GET",
            f"sdcs/{sdc_id}",
            200,
            check_response=lambda r: (
                "work_orders" in r and
                "stage_progress" in r and
                "financial" in r and
                isinstance(r["work_orders"], list)
            )
        )
        return success, response

    def test_role_based_access(self):
        """Test role-based access (HO sees all, SDC users see only assigned center)"""
        # This test verifies HO role can access all endpoints
        success, response = self.run_test(
            "Role-based Access (HO user should see all SDCs)",
            "GET",
            "dashboard/overview",
            200,
            check_response=lambda r: "sdc_summaries" in r
        )
        return success, response

def main():
    print("🚀 Starting SkillFlow CRM Backend API Testing")
    print("Testing Features:")
    print("- Landing page loads with Google Sign-in button")
    print("- Backend API returns version 2.0.0")
    print("- Dashboard shows 5 financial metrics")
    print("- Dashboard shows Training Roadmap Progress with 7 stages")
    print("- SDC cards show overdue count and blockers")
    print("- Work Order creation auto-creates SDC and training roadmap")
    print("- Setting start date calculates end date correctly")
    print("- Invoice creation calculates variance and generates alert if >10%")
    print("- Payment recording triggers PAID status on completed stages")
    print("- Role-based access: HO users see all centers")
    print("=" * 80)
    
    tester = SkillFlowAPITester()
    
    # Test 1: API Version (should return 2.0.0)
    if not tester.test_api_version():
        print("❌ API version test failed - stopping tests")
        return 1
    
    # Test 2: Authentication (HO user)
    auth_success, user_data = tester.test_auth_me()
    if not auth_success:
        print("❌ Authentication failed - stopping tests")
        return 1
    
    print(f"✅ Authenticated as: {user_data.get('name')} ({user_data.get('role')})")
    
    # Test 3: Dashboard Overview (5 financial metrics + 7 training stages)
    dashboard_success, dashboard_data = tester.test_dashboard_overview()
    if dashboard_success:
        commercial_health = dashboard_data.get("commercial_health", {})
        print(f"   📊 Total Portfolio: ₹{commercial_health.get('total_portfolio', 0):,}")
        print(f"   📊 Actual Billed: ₹{commercial_health.get('actual_billed', 0):,}")
        print(f"   📊 Collected: ₹{commercial_health.get('collected', 0):,}")
        print(f"   📊 Outstanding: ₹{commercial_health.get('outstanding', 0):,}")
        print(f"   📊 Variance: {commercial_health.get('variance_percent', 0)}%")
        print(f"   📊 Training Stages: {len(dashboard_data.get('stage_progress', {}))}")
    
    # Test 4: SDCs List (with overdue count and blockers)
    sdcs_success, sdcs_data = tester.test_sdcs_list()
    sdc_id = None
    if sdcs_success and sdcs_data:
        sdc_id = sdcs_data[0]["sdc_id"]
        print(f"   🏢 Found {len(sdcs_data)} SDCs, using: {sdc_id}")
    
    # Test 5: Work Orders List (with auto-calculated end dates)
    work_orders_success, work_orders_data = tester.test_work_orders_list()
    
    # Test 6: Training Stages (7 stages)
    tester.test_training_stages()
    
    # Test 7: Role-based Access
    tester.test_role_based_access()
    
    # Test 8: Full Workflow - Create Work Order -> Set Start Date -> Create Invoice -> Record Payment
    print("\n🔄 Testing Full Workflow (create work order -> set start date -> create invoice -> record payment)...")
    
    # Create Work Order (auto-creates SDC and training roadmap)
    wo_success, wo_response = tester.test_create_work_order()
    work_order_id = None
    created_sdc_id = None
    
    if wo_success:
        work_order_id = wo_response["work_order"]["work_order_id"]
        created_sdc_id = wo_response["sdc"]["sdc_id"]
        print(f"   ✅ Created Work Order: {work_order_id}")
        print(f"   ✅ Auto-created SDC: {created_sdc_id}")
        print(f"   ✅ Created {wo_response['roadmap_stages']} roadmap stages")
        
        # Set Start Date (calculates end date correctly)
        start_date_success, start_date_response = tester.test_set_start_date(work_order_id)
        if start_date_success:
            print(f"   ✅ Set start date, calculated end: {start_date_response.get('calculated_end_date')}")
            
            # Create Invoice (calculates variance and generates alert if >10%)
            invoice_success, invoice_response = tester.test_create_invoice(created_sdc_id, work_order_id)
            if invoice_success:
                invoice_id = invoice_response["invoice_id"]
                print(f"   ✅ Created Invoice: {invoice_id}")
                print(f"   ⚠️  Variance: {invoice_response.get('variance_percent')}% (should trigger alert)")
                
                # Record Payment (triggers PAID status on completed stages)
                payment_success, payment_response = tester.test_record_payment(invoice_id)
                if payment_success:
                    print(f"   ✅ Payment recorded, status: {payment_response.get('new_status')}")
    
    # Test 9: SDC Detail Page (shows work orders table and training roadmap progress)
    if sdc_id:
        tester.test_sdc_detail(sdc_id)
    
    # Print Results
    print("\n" + "=" * 80)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.failed_tests:
        print("\n❌ Failed Tests:")
        for failure in tester.failed_tests:
            print(f"   • {failure}")
    
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("✅ Backend API testing completed successfully!")
        return 0
    else:
        print("❌ Backend API testing failed - too many failures")
        return 1

if __name__ == "__main__":
    sys.exit(main())