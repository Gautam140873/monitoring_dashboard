"""
SkillFlow CRM API Tests
Tests for Dashboard, SDC Detail, and Work Order endpoints
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test session token - created in MongoDB
SESSION_TOKEN = os.environ.get('TEST_SESSION_TOKEN', 'test_session_1771330326224')


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SESSION_TOKEN}"
    })
    return session


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_auth_me_returns_user_data(self, api_client):
        """Test GET /api/auth/me returns authenticated user"""
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        assert "role" in data
        assert data["role"] in ["ho", "sdc"]
        print(f"✓ Auth endpoint returned user: {data['email']} with role: {data['role']}")


class TestDashboardEndpoints:
    """Dashboard overview endpoint tests"""
    
    def test_dashboard_overview_returns_data(self, api_client):
        """Test GET /api/dashboard/overview returns SDC summaries"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/overview")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify commercial health metrics
        assert "commercial_health" in data
        health = data["commercial_health"]
        assert "total_portfolio" in health
        assert "actual_billed" in health
        assert "outstanding" in health
        assert "collected" in health
        assert "variance" in health
        
        # Verify stage progress
        assert "stage_progress" in data
        stages = data["stage_progress"]
        expected_stages = ["mobilization", "dress_distribution", "study_material", 
                         "classroom_training", "assessment", "ojt", "placement"]
        for stage in expected_stages:
            assert stage in stages, f"Missing stage: {stage}"
        
        # Verify SDC summaries
        assert "sdc_summaries" in data
        assert isinstance(data["sdc_summaries"], list)
        assert len(data["sdc_summaries"]) > 0, "Expected at least one SDC summary"
        
        print(f"✓ Dashboard overview returned {len(data['sdc_summaries'])} SDC summaries")
        print(f"  Total Portfolio: {health['total_portfolio']}")
        print(f"  Outstanding: {health['outstanding']}")
    
    def test_dashboard_sdc_summaries_have_required_fields(self, api_client):
        """Test SDC summaries contain all required fields"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/overview")
        assert response.status_code == 200
        
        data = response.json()
        for sdc in data["sdc_summaries"]:
            assert "sdc_id" in sdc
            assert "name" in sdc
            assert "location" in sdc
            assert "progress" in sdc
            assert "financial" in sdc
            assert "work_orders_count" in sdc
            
            # Verify financial fields
            fin = sdc["financial"]
            assert "portfolio" in fin
            assert "billed" in fin
            assert "paid" in fin
            assert "outstanding" in fin
        
        print(f"✓ All SDC summaries have required fields")


class TestSDCDetailEndpoints:
    """SDC Detail endpoint tests - Critical for bug fix verification"""
    
    def test_get_sdc_detail_gurugram(self, api_client):
        """Test GET /api/sdcs/sdc_gurugram returns SDC details"""
        response = api_client.get(f"{BASE_URL}/api/sdcs/sdc_gurugram")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["sdc_id"] == "sdc_gurugram"
        assert "name" in data
        assert "location" in data
        assert "work_orders" in data
        assert "stage_progress" in data
        assert "financial" in data
        assert "invoices" in data
        
        print(f"✓ SDC Gurugram detail returned successfully")
        print(f"  Work Orders: {len(data['work_orders'])}")
        print(f"  Invoices: {len(data['invoices'])}")
    
    def test_get_sdc_detail_jaipur(self, api_client):
        """Test GET /api/sdcs/sdc_jaipur returns SDC details"""
        response = api_client.get(f"{BASE_URL}/api/sdcs/sdc_jaipur")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["sdc_id"] == "sdc_jaipur"
        assert "stage_progress" in data
        
        # Verify stage progress structure
        for stage_id, stage_data in data["stage_progress"].items():
            assert "name" in stage_data
            assert "order" in stage_data
            assert "target" in stage_data
            assert "completed" in stage_data
            assert "percent" in stage_data
        
        print(f"✓ SDC Jaipur detail returned with stage progress")
    
    def test_get_sdc_detail_delhi(self, api_client):
        """Test GET /api/sdcs/sdc_delhi returns SDC details"""
        response = api_client.get(f"{BASE_URL}/api/sdcs/sdc_delhi")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["sdc_id"] == "sdc_delhi"
        print(f"✓ SDC Delhi detail returned successfully")
    
    def test_get_sdc_detail_mumbai(self, api_client):
        """Test GET /api/sdcs/sdc_mumbai returns SDC details"""
        response = api_client.get(f"{BASE_URL}/api/sdcs/sdc_mumbai")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["sdc_id"] == "sdc_mumbai"
        print(f"✓ SDC Mumbai detail returned successfully")
    
    def test_get_sdc_detail_nonexistent_returns_404(self, api_client):
        """Test GET /api/sdcs/nonexistent returns 404"""
        response = api_client.get(f"{BASE_URL}/api/sdcs/sdc_nonexistent")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Non-existent SDC correctly returns 404")


class TestWorkOrderEndpoints:
    """Work Order creation and management tests"""
    
    def test_create_work_order_success(self, api_client):
        """Test POST /api/work-orders creates work order and SDC"""
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
        assert "message" in data
        assert "work_order" in data
        assert "sdc" in data
        assert "roadmap_stages" in data
        
        # Verify work order data
        wo = data["work_order"]
        assert wo["work_order_number"] == payload["work_order_number"]
        assert wo["num_students"] == payload["num_students"]
        assert wo["total_contract_value"] == payload["num_students"] * payload["cost_per_student"]
        
        # Verify SDC was created
        sdc = data["sdc"]
        assert "sdc_id" in sdc
        assert sdc["location"] == payload["location"]
        
        # Verify roadmap stages created
        assert data["roadmap_stages"] == 7
        
        print(f"✓ Work Order created: {wo['work_order_id']}")
        print(f"  SDC created: {sdc['sdc_id']}")
        print(f"  Contract Value: {wo['total_contract_value']}")
    
    def test_list_work_orders(self, api_client):
        """Test GET /api/work-orders returns list"""
        response = api_client.get(f"{BASE_URL}/api/work-orders")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Expected at least one work order"
        
        # Verify work order structure
        wo = data[0]
        assert "work_order_id" in wo
        assert "work_order_number" in wo
        assert "sdc_id" in wo
        assert "num_students" in wo
        assert "total_contract_value" in wo
        
        print(f"✓ Work orders list returned {len(data)} items")


class TestAlertsEndpoints:
    """Alerts endpoint tests"""
    
    def test_get_alerts(self, api_client):
        """Test GET /api/alerts returns alerts list"""
        response = api_client.get(f"{BASE_URL}/api/alerts")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Alerts endpoint returned {len(data)} alerts")


class TestSDCListEndpoint:
    """SDC list endpoint tests"""
    
    def test_list_sdcs(self, api_client):
        """Test GET /api/sdcs returns SDC list"""
        response = api_client.get(f"{BASE_URL}/api/sdcs")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5, f"Expected at least 5 SDCs, got {len(data)}"
        
        # Verify SDC structure
        for sdc in data:
            assert "sdc_id" in sdc
            assert "name" in sdc
            assert "location" in sdc
        
        print(f"✓ SDC list returned {len(data)} SDCs")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
