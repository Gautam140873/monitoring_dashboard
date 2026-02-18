"""
SkillFlow Resource API Tests
Tests for infrastructure, managers, and resource assignment endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test session token (created for HO user)
TEST_SESSION_TOKEN = "test_session_1771399975226"

@pytest.fixture
def api_client():
    """Shared requests session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TEST_SESSION_TOKEN}"
    })
    return session


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_auth_me_returns_user(self, api_client):
        """Test /api/auth/me returns authenticated user"""
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        assert "role" in data
        assert data["role"] == "ho"  # HO role required for master data


class TestInfrastructureEndpoints:
    """Infrastructure resource endpoint tests"""
    
    def test_list_available_infrastructure(self, api_client):
        """Test GET /api/resources/infrastructure/available returns available centers"""
        response = api_client.get(f"{BASE_URL}/api/resources/infrastructure/available")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify structure of infrastructure items
        if len(data) > 0:
            infra = data[0]
            assert "infra_id" in infra
            assert "center_name" in infra
            assert "district" in infra
            assert "address_line1" in infra
            assert "city" in infra
            assert "state" in infra
            assert "pincode" in infra
            assert infra["status"] == "available"
            print(f"Found {len(data)} available infrastructure centers")
    
    def test_list_all_infrastructure(self, api_client):
        """Test GET /api/resources/infrastructure returns all centers"""
        response = api_client.get(f"{BASE_URL}/api/resources/infrastructure")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} total infrastructure centers")
    
    def test_infrastructure_assign_and_release(self, api_client):
        """Test infrastructure assignment and release workflow"""
        # First get available infrastructure
        response = api_client.get(f"{BASE_URL}/api/resources/infrastructure/available")
        assert response.status_code == 200
        available = response.json()
        
        if len(available) == 0:
            pytest.skip("No available infrastructure to test")
        
        infra_id = available[0]["infra_id"]
        
        # Assign infrastructure
        assign_response = api_client.post(
            f"{BASE_URL}/api/resources/infrastructure/{infra_id}/assign",
            params={"work_order_id": "test_wo_pytest"}
        )
        assert assign_response.status_code == 200
        assert "assigned" in assign_response.json()["message"].lower()
        print(f"Successfully assigned infrastructure {infra_id}")
        
        # Verify it's no longer in available list
        available_after = api_client.get(f"{BASE_URL}/api/resources/infrastructure/available").json()
        infra_ids_after = [i["infra_id"] for i in available_after]
        assert infra_id not in infra_ids_after, "Assigned infrastructure should not be in available list"
        
        # Release infrastructure
        release_response = api_client.post(
            f"{BASE_URL}/api/resources/infrastructure/{infra_id}/release"
        )
        assert release_response.status_code == 200
        assert "released" in release_response.json()["message"].lower()
        print(f"Successfully released infrastructure {infra_id}")
        
        # Verify it's back in available list
        available_final = api_client.get(f"{BASE_URL}/api/resources/infrastructure/available").json()
        infra_ids_final = [i["infra_id"] for i in available_final]
        assert infra_id in infra_ids_final, "Released infrastructure should be in available list"


class TestManagerEndpoints:
    """Center Manager resource endpoint tests"""
    
    def test_list_available_managers(self, api_client):
        """Test GET /api/resources/managers/available returns available managers"""
        response = api_client.get(f"{BASE_URL}/api/resources/managers/available")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            manager = data[0]
            assert "manager_id" in manager
            assert "name" in manager
            assert "email" in manager
            assert manager["status"] == "available"
            print(f"Found {len(data)} available managers")


class TestMasterDataEndpoints:
    """Master Data endpoint tests"""
    
    def test_list_job_roles(self, api_client):
        """Test GET /api/master/job-roles returns job roles"""
        response = api_client.get(f"{BASE_URL}/api/master/job-roles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            jr = data[0]
            assert "job_role_id" in jr
            assert "job_role_code" in jr
            assert "job_role_name" in jr
            assert "rate_per_hour" in jr
            assert "total_training_hours" in jr
            print(f"Found {len(data)} job roles")
    
    def test_list_master_work_orders(self, api_client):
        """Test GET /api/master/work-orders returns work orders"""
        response = api_client.get(f"{BASE_URL}/api/master/work-orders")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            wo = data[0]
            assert "master_wo_id" in wo
            assert "work_order_number" in wo
            print(f"Found {len(data)} master work orders")


class TestSDCCreationFromMaster:
    """SDC Creation from Master Work Order tests"""
    
    def test_get_master_work_order_details(self, api_client):
        """Test GET /api/master/work-orders/{id} returns work order with SDC info"""
        # First get list of work orders
        list_response = api_client.get(f"{BASE_URL}/api/master/work-orders")
        assert list_response.status_code == 200
        work_orders = list_response.json()
        
        if len(work_orders) == 0:
            pytest.skip("No master work orders to test")
        
        master_wo_id = work_orders[0]["master_wo_id"]
        
        # Get details
        detail_response = api_client.get(f"{BASE_URL}/api/master/work-orders/{master_wo_id}")
        assert detail_response.status_code == 200
        data = detail_response.json()
        
        assert "master_wo_id" in data
        assert "work_order_number" in data
        assert "sdcs_created" in data
        print(f"Work order {data['work_order_number']} has {len(data.get('sdcs_created', []))} SDCs created")


class TestResourcesSummary:
    """Resources summary endpoint tests"""
    
    def test_resources_summary(self, api_client):
        """Test GET /api/resources/summary returns resource counts"""
        response = api_client.get(f"{BASE_URL}/api/resources/summary")
        assert response.status_code == 200
        data = response.json()
        
        assert "trainers" in data
        assert "managers" in data
        assert "infrastructure" in data
        
        # Verify structure
        assert "total" in data["trainers"]
        assert "available" in data["trainers"]
        assert "total" in data["managers"]
        assert "available" in data["managers"]
        assert "total" in data["infrastructure"]
        assert "available" in data["infrastructure"]
        
        print(f"Resources: {data['trainers']['total']} trainers, {data['managers']['total']} managers, {data['infrastructure']['total']} centers")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
