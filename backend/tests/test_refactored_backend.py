"""
SkillFlow CRM - Refactored Backend API Tests
Tests all API endpoints after modular refactoring from monolithic server.py
Verifies: Auth, Dashboard, SDCs, Master Data (Job Roles, Work Orders), Resources, Users
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://crm-dashboard-195.preview.emergentagent.com').rstrip('/')

# Valid session token for HO user
SESSION_TOKEN = os.environ.get('TEST_SESSION_TOKEN', 'KsyilFW4rNRvJWDJbaQeJhzXqq045BVgbmPEH4ttS7U')


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SESSION_TOKEN}"
    })
    return session


# ==================== ROOT & TRAINING STAGES ====================
class TestRootEndpoints:
    """Test root API endpoint and training stages"""
    
    def test_api_root_returns_version(self, api_client):
        """Test GET /api/ returns correct version after refactoring"""
        response = api_client.get(f"{BASE_URL}/api/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "3.0.0" in data["version"], f"Expected version 3.0.0, got {data['version']}"
        assert "Modular" in data["version"], "Expected 'Modular' in version string"
        print(f"✓ API root: {data['message']} - {data['version']}")
    
    def test_training_stages_endpoint(self, api_client):
        """Test GET /api/training-stages returns stages list"""
        response = api_client.get(f"{BASE_URL}/api/training-stages")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 7, f"Expected 7 training stages, got {len(data)}"
        
        expected_stages = ["mobilization", "dress_distribution", "study_material", 
                         "classroom_training", "assessment", "ojt", "placement"]
        for stage in data:
            assert "stage_id" in stage
            assert "name" in stage
            assert "order" in stage
            assert stage["stage_id"] in expected_stages
        print(f"✓ Training stages: {len(data)} stages returned")


# ==================== AUTHENTICATION ====================
class TestAuthEndpoints:
    """Authentication router tests (/api/auth/*)"""
    
    def test_auth_me_returns_user_data(self, api_client):
        """Test GET /api/auth/me returns authenticated user"""
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        assert "name" in data
        assert "role" in data
        assert data["role"] == "ho", f"Expected role 'ho', got {data['role']}"
        print(f"✓ Auth /me: {data['email']} (role: {data['role']})")
    
    def test_auth_me_without_token_returns_401(self):
        """Test GET /api/auth/me without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Auth /me without token: 401 Unauthorized")


# ==================== DASHBOARD ====================
class TestDashboardEndpoints:
    """Dashboard router tests (/api/dashboard/*)"""
    
    def test_dashboard_overview(self, api_client):
        """Test GET /api/dashboard/overview returns metrics"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/overview")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify commercial health
        assert "commercial_health" in data
        health = data["commercial_health"]
        assert "total_portfolio" in health
        assert "actual_billed" in health
        assert "outstanding" in health
        assert "collected" in health
        assert "variance" in health
        
        # Verify stage progress
        assert "stage_progress" in data
        
        # Verify SDC summaries
        assert "sdc_summaries" in data
        assert "sdc_count" in data
        assert "work_orders_count" in data
        
        print(f"✓ Dashboard overview: {data['sdc_count']} SDCs, {data['work_orders_count']} work orders")
        print(f"  Portfolio: {health['total_portfolio']}, Outstanding: {health['outstanding']}")
    
    def test_dashboard_alerts(self, api_client):
        """Test GET /api/dashboard/alerts returns alerts list"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/alerts")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Dashboard alerts: {len(data)} alerts")


# ==================== SDCs ====================
class TestSDCEndpoints:
    """SDC router tests (/api/sdcs/*)"""
    
    def test_list_sdcs(self, api_client):
        """Test GET /api/sdcs returns SDC list"""
        response = api_client.get(f"{BASE_URL}/api/sdcs")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        
        for sdc in data:
            assert "sdc_id" in sdc
            assert "name" in sdc
            assert "location" in sdc
        
        print(f"✓ SDCs list: {len(data)} SDCs")
    
    def test_get_sdc_detail(self, api_client):
        """Test GET /api/sdcs/{sdc_id} returns SDC details"""
        # First get list to find an SDC
        list_response = api_client.get(f"{BASE_URL}/api/sdcs")
        sdcs = list_response.json()
        
        if len(sdcs) > 0:
            sdc_id = sdcs[0]["sdc_id"]
            response = api_client.get(f"{BASE_URL}/api/sdcs/{sdc_id}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            data = response.json()
            assert data["sdc_id"] == sdc_id
            assert "work_orders" in data
            assert "stage_progress" in data
            assert "financial" in data
            assert "invoices" in data
            
            print(f"✓ SDC detail ({sdc_id}): {len(data['work_orders'])} work orders")
        else:
            pytest.skip("No SDCs available for testing")
    
    def test_get_sdc_process_status(self, api_client):
        """Test GET /api/sdcs/{sdc_id}/process-status returns process stages"""
        list_response = api_client.get(f"{BASE_URL}/api/sdcs")
        sdcs = list_response.json()
        
        if len(sdcs) > 0:
            sdc_id = sdcs[0]["sdc_id"]
            response = api_client.get(f"{BASE_URL}/api/sdcs/{sdc_id}/process-status")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            data = response.json()
            assert "sdc_id" in data
            assert "stages" in data
            assert "deliverables" in data
            assert "overall_progress" in data
            
            print(f"✓ SDC process status ({sdc_id}): {data['overall_progress']}% progress")
        else:
            pytest.skip("No SDCs available for testing")
    
    def test_get_nonexistent_sdc_returns_404(self, api_client):
        """Test GET /api/sdcs/nonexistent returns 404"""
        response = api_client.get(f"{BASE_URL}/api/sdcs/sdc_nonexistent_xyz")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Non-existent SDC: 404 Not Found")


# ==================== MASTER DATA - JOB ROLES ====================
class TestJobRolesEndpoints:
    """Master Data router tests - Job Roles (/api/master/job-roles/*)"""
    
    def test_list_job_roles(self, api_client):
        """Test GET /api/master/job-roles returns job roles list"""
        response = api_client.get(f"{BASE_URL}/api/master/job-roles")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Job roles list: {len(data)} job roles")
    
    def test_list_active_job_roles(self, api_client):
        """Test GET /api/master/job-roles/active returns active job roles"""
        response = api_client.get(f"{BASE_URL}/api/master/job-roles/active")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        for jr in data:
            assert jr.get("is_active", True) == True
        print(f"✓ Active job roles: {len(data)} active")
    
    def test_create_job_role(self, api_client):
        """Test POST /api/master/job-roles creates new job role"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        payload = {
            "job_role_code": f"TEST/Q{timestamp}",
            "job_role_name": f"Test Job Role {timestamp}",
            "category": "A",
            "total_training_hours": 200,
            "awarding_body": "Test Body",
            "scheme_name": "Test Scheme"
        }
        
        response = api_client.post(f"{BASE_URL}/api/master/job-roles", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "job_role_id" in data
        assert data["job_role_code"] == payload["job_role_code"]
        assert data["rate_per_hour"] == 46.0  # Category A rate
        
        print(f"✓ Created job role: {data['job_role_id']}")
        return data["job_role_id"]


# ==================== MASTER DATA - WORK ORDERS ====================
class TestMasterWorkOrdersEndpoints:
    """Master Data router tests - Work Orders (/api/master/work-orders/*)"""
    
    def test_list_master_work_orders(self, api_client):
        """Test GET /api/master/work-orders returns master work orders"""
        response = api_client.get(f"{BASE_URL}/api/master/work-orders")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Master work orders: {len(data)} orders")
    
    def test_get_master_summary(self, api_client):
        """Test GET /api/master/summary returns master data summary"""
        response = api_client.get(f"{BASE_URL}/api/master/summary")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "job_roles" in data
        assert "work_orders" in data
        assert "financials" in data
        assert "sdcs" in data
        
        print(f"✓ Master summary: {data['job_roles']['total']} job roles, {data['work_orders']['total']} work orders")


# ==================== RESOURCES - TRAINERS ====================
class TestTrainersEndpoints:
    """Resources router tests - Trainers (/api/resources/trainers/*)"""
    
    def test_list_trainers(self, api_client):
        """Test GET /api/resources/trainers returns trainers list"""
        response = api_client.get(f"{BASE_URL}/api/resources/trainers")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Trainers list: {len(data)} trainers")
    
    def test_list_available_trainers(self, api_client):
        """Test GET /api/resources/trainers/available returns available trainers"""
        response = api_client.get(f"{BASE_URL}/api/resources/trainers/available")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        for trainer in data:
            assert trainer.get("status") == "available"
        print(f"✓ Available trainers: {len(data)}")
    
    def test_create_trainer(self, api_client):
        """Test POST /api/resources/trainers creates new trainer"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        payload = {
            "name": f"Test Trainer {timestamp}",
            "email": f"trainer{timestamp}@test.com",
            "phone": "9876543210",
            "qualification": "B.Tech",
            "specialization": "IT",
            "experience_years": 5
        }
        
        response = api_client.post(f"{BASE_URL}/api/resources/trainers", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "trainer_id" in data
        assert data["name"] == payload["name"]
        assert data["status"] == "available"
        
        print(f"✓ Created trainer: {data['trainer_id']}")


# ==================== RESOURCES - MANAGERS ====================
class TestManagersEndpoints:
    """Resources router tests - Managers (/api/resources/managers/*)"""
    
    def test_list_managers(self, api_client):
        """Test GET /api/resources/managers returns managers list"""
        response = api_client.get(f"{BASE_URL}/api/resources/managers")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Managers list: {len(data)} managers")
    
    def test_list_available_managers(self, api_client):
        """Test GET /api/resources/managers/available returns available managers"""
        response = api_client.get(f"{BASE_URL}/api/resources/managers/available")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Available managers: {len(data)}")
    
    def test_create_manager(self, api_client):
        """Test POST /api/resources/managers creates new manager"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        payload = {
            "name": f"Test Manager {timestamp}",
            "email": f"manager{timestamp}@test.com",
            "phone": "9876543210",
            "qualification": "MBA",
            "experience_years": 8
        }
        
        response = api_client.post(f"{BASE_URL}/api/resources/managers", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "manager_id" in data
        assert data["name"] == payload["name"]
        assert data["status"] == "available"
        
        print(f"✓ Created manager: {data['manager_id']}")


# ==================== RESOURCES - INFRASTRUCTURE ====================
class TestInfrastructureEndpoints:
    """Resources router tests - Infrastructure (/api/resources/infrastructure/*)"""
    
    def test_list_infrastructure(self, api_client):
        """Test GET /api/resources/infrastructure returns infrastructure list"""
        response = api_client.get(f"{BASE_URL}/api/resources/infrastructure")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Infrastructure list: {len(data)} items")
    
    def test_list_available_infrastructure(self, api_client):
        """Test GET /api/resources/infrastructure/available returns available infrastructure"""
        response = api_client.get(f"{BASE_URL}/api/resources/infrastructure/available")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Available infrastructure: {len(data)}")
    
    def test_create_infrastructure(self, api_client):
        """Test POST /api/resources/infrastructure creates new infrastructure"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        payload = {
            "center_name": f"Test Center {timestamp}",
            "center_code": f"TC{timestamp}",
            "district": "Test District",
            "address_line1": "123 Test Street",
            "city": "Test City",
            "state": "Test State",
            "pincode": "123456",
            "total_capacity": 50
        }
        
        response = api_client.post(f"{BASE_URL}/api/resources/infrastructure", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "infra_id" in data
        assert data["center_name"] == payload["center_name"]
        assert data["status"] == "available"
        
        print(f"✓ Created infrastructure: {data['infra_id']}")


# ==================== RESOURCES SUMMARY ====================
class TestResourcesSummaryEndpoints:
    """Resources router tests - Summary (/api/resources/summary)"""
    
    def test_resources_summary(self, api_client):
        """Test GET /api/resources/summary returns resources summary"""
        response = api_client.get(f"{BASE_URL}/api/resources/summary")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "trainers" in data
        assert "managers" in data
        assert "infrastructure" in data
        
        # Verify trainers summary
        assert "total" in data["trainers"]
        assert "available" in data["trainers"]
        assert "assigned" in data["trainers"]
        
        print(f"✓ Resources summary: {data['trainers']['total']} trainers, {data['managers']['total']} managers, {data['infrastructure']['total']} infrastructure")


# ==================== USERS ====================
class TestUsersEndpoints:
    """Users router tests (/api/users/*)"""
    
    def test_list_users(self, api_client):
        """Test GET /api/users returns users list"""
        response = api_client.get(f"{BASE_URL}/api/users")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        
        for user in data:
            assert "user_id" in user
            assert "email" in user
            assert "role" in user
        
        print(f"✓ Users list: {len(data)} users")
    
    def test_audit_logs(self, api_client):
        """Test GET /api/users/audit/logs returns audit logs"""
        response = api_client.get(f"{BASE_URL}/api/users/audit/logs")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "logs" in data
        assert "total" in data
        assert isinstance(data["logs"], list)
        
        print(f"✓ Audit logs: {data['total']} total logs")
    
    def test_deleted_items(self, api_client):
        """Test GET /api/users/deleted/items returns deleted items"""
        response = api_client.get(f"{BASE_URL}/api/users/deleted/items")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        
        print(f"✓ Deleted items: {data['total']} recoverable items")


# ==================== WORK ORDERS (Main) ====================
class TestWorkOrdersEndpoints:
    """Work Orders endpoints in main server.py (/api/work-orders/*)"""
    
    def test_list_work_orders(self, api_client):
        """Test GET /api/work-orders returns work orders list"""
        response = api_client.get(f"{BASE_URL}/api/work-orders")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        
        for wo in data:
            assert "work_order_id" in wo
            assert "work_order_number" in wo
            assert "sdc_id" in wo
        
        print(f"✓ Work orders list: {len(data)} work orders")
    
    def test_create_work_order(self, api_client):
        """Test POST /api/work-orders creates work order"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        payload = {
            "work_order_number": f"WO/TEST/{timestamp}",
            "location": f"TestCity{timestamp}",
            "job_role_code": "CSC/Q0801",
            "job_role_name": "Field Technician Computing",
            "awarding_body": "NSDC PMKVY",
            "scheme_name": "PMKVY 4.0",
            "total_training_hours": 200,
            "sessions_per_day": 8,
            "num_students": 25,
            "cost_per_student": 8000,
            "manager_email": "test@example.com"
        }
        
        response = api_client.post(f"{BASE_URL}/api/work-orders", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "work_order" in data
        assert "sdc" in data
        assert "message" in data
        
        wo = data["work_order"]
        assert wo["work_order_number"] == payload["work_order_number"]
        assert wo["total_contract_value"] == payload["num_students"] * payload["cost_per_student"]
        
        print(f"✓ Created work order: {wo['work_order_id']}")


# ==================== INVOICES ====================
class TestInvoicesEndpoints:
    """Invoice endpoints (/api/invoices/*)"""
    
    def test_list_invoices(self, api_client):
        """Test GET /api/invoices returns invoices list"""
        response = api_client.get(f"{BASE_URL}/api/invoices")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Invoices list: {len(data)} invoices")
    
    def test_create_invoice(self, api_client):
        """Test POST /api/invoices creates invoice"""
        # First get an SDC
        sdcs_response = api_client.get(f"{BASE_URL}/api/sdcs")
        sdcs = sdcs_response.json()
        
        if len(sdcs) > 0:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            payload = {
                "sdc_id": sdcs[0]["sdc_id"],
                "invoice_number": f"INV/TEST/{timestamp}",
                "invoice_date": "2026-01-15",
                "order_value": 100000,
                "billing_value": 95000
            }
            
            response = api_client.post(f"{BASE_URL}/api/invoices", json=payload)
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            data = response.json()
            assert "invoice_id" in data
            assert data["variance"] == payload["order_value"] - payload["billing_value"]
            
            print(f"✓ Created invoice: {data['invoice_id']}")
        else:
            pytest.skip("No SDCs available for invoice creation")


# ==================== HOLIDAYS ====================
class TestHolidaysEndpoints:
    """Holiday endpoints (/api/holidays/*)"""
    
    def test_list_holidays(self, api_client):
        """Test GET /api/holidays returns holidays list"""
        response = api_client.get(f"{BASE_URL}/api/holidays")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Holidays list: {len(data)} holidays")
    
    def test_create_holiday(self, api_client):
        """Test POST /api/holidays creates holiday"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        payload = {
            "date": "2026-12-25",
            "name": f"Test Holiday {timestamp}",
            "year": 2026,
            "is_local": False
        }
        
        response = api_client.post(f"{BASE_URL}/api/holidays", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "holiday_id" in data
        assert data["name"] == payload["name"]
        
        print(f"✓ Created holiday: {data['holiday_id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
