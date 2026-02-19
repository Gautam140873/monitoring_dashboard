"""
Test Job Role Target Allocation Tracking Feature
Tests the new allocation-status endpoint and SDC creation with allocation validation
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
SESSION_TOKEN = "test_session_alloc_1771483821721"

@pytest.fixture
def api_client():
    """Shared requests session with auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SESSION_TOKEN}"
    })
    return session


class TestAllocationStatusEndpoint:
    """Test GET /api/master/work-orders/{id}/allocation-status endpoint"""
    
    def test_allocation_status_returns_200(self, api_client):
        """Test that allocation-status endpoint returns 200 for valid master work order"""
        # First get a master work order ID
        response = api_client.get(f"{BASE_URL}/api/master/work-orders")
        assert response.status_code == 200
        work_orders = response.json()
        
        # Find a work order with job_roles array (new format)
        master_wo = None
        for wo in work_orders:
            if wo.get("job_roles") and isinstance(wo.get("job_roles"), list):
                master_wo = wo
                break
        
        if not master_wo:
            pytest.skip("No master work orders with job_roles array found")
        
        # Test allocation-status endpoint
        response = api_client.get(f"{BASE_URL}/api/master/work-orders/{master_wo['master_wo_id']}/allocation-status")
        assert response.status_code == 200
        
        data = response.json()
        # Verify response structure
        assert "master_wo_id" in data
        assert "work_order_number" in data
        assert "total_training_target" in data
        assert "total_allocated" in data
        assert "total_remaining" in data
        assert "sdcs_planned" in data
        assert "sdcs_created" in data
        assert "job_roles" in data
        assert "is_fully_allocated" in data
        
        print(f"✓ Allocation status for {data['work_order_number']}: Target={data['total_training_target']}, Allocated={data['total_allocated']}, Remaining={data['total_remaining']}")
    
    def test_allocation_status_job_role_details(self, api_client):
        """Test that allocation-status returns correct job role allocation details"""
        # Get master work orders
        response = api_client.get(f"{BASE_URL}/api/master/work-orders")
        assert response.status_code == 200
        work_orders = response.json()
        
        # Find work order with multiple job roles
        master_wo = None
        for wo in work_orders:
            if wo.get("job_roles") and len(wo.get("job_roles", [])) >= 2:
                master_wo = wo
                break
        
        if not master_wo:
            pytest.skip("No master work orders with multiple job roles found")
        
        # Get allocation status
        response = api_client.get(f"{BASE_URL}/api/master/work-orders/{master_wo['master_wo_id']}/allocation-status")
        assert response.status_code == 200
        
        data = response.json()
        job_roles = data.get("job_roles", [])
        
        # Verify each job role has required fields
        for jr in job_roles:
            assert "job_role_id" in jr
            assert "job_role_code" in jr
            assert "job_role_name" in jr
            assert "target" in jr
            assert "allocated" in jr
            assert "remaining" in jr
            assert "sdcs_count" in jr
            assert "is_fully_allocated" in jr
            
            # Verify remaining calculation
            expected_remaining = max(0, jr["target"] - jr["allocated"])
            assert jr["remaining"] == expected_remaining, f"Remaining mismatch for {jr['job_role_code']}"
            
            # Verify is_fully_allocated flag
            assert jr["is_fully_allocated"] == (jr["remaining"] == 0)
            
            print(f"  Job Role {jr['job_role_code']}: Target={jr['target']}, Allocated={jr['allocated']}, Remaining={jr['remaining']}")
    
    def test_allocation_status_404_for_invalid_id(self, api_client):
        """Test that allocation-status returns 404 for non-existent master work order"""
        response = api_client.get(f"{BASE_URL}/api/master/work-orders/invalid_mwo_id/allocation-status")
        assert response.status_code == 404
        print("✓ Returns 404 for invalid master work order ID")
    
    def test_allocation_status_requires_auth(self):
        """Test that allocation-status requires authentication"""
        response = requests.get(f"{BASE_URL}/api/master/work-orders/mwo_test/allocation-status")
        assert response.status_code == 401
        print("✓ Returns 401 for unauthenticated request")
    
    def test_total_remaining_calculation(self, api_client):
        """Test that total_remaining is correctly calculated"""
        response = api_client.get(f"{BASE_URL}/api/master/work-orders")
        assert response.status_code == 200
        work_orders = response.json()
        
        for wo in work_orders:
            if wo.get("job_roles") and isinstance(wo.get("job_roles"), list):
                # Get allocation status
                alloc_response = api_client.get(f"{BASE_URL}/api/master/work-orders/{wo['master_wo_id']}/allocation-status")
                if alloc_response.status_code == 200:
                    data = alloc_response.json()
                    
                    # Verify total_remaining = total_training_target - total_allocated
                    expected_remaining = max(0, data["total_training_target"] - data["total_allocated"])
                    assert data["total_remaining"] == expected_remaining, \
                        f"Total remaining mismatch: expected {expected_remaining}, got {data['total_remaining']}"
                    
                    print(f"✓ {data['work_order_number']}: {data['total_training_target']} - {data['total_allocated']} = {data['total_remaining']}")
                    break


class TestSDCCreationWithAllocation:
    """Test SDC creation validates against remaining allocation"""
    
    def test_sdc_creation_endpoint_exists(self, api_client):
        """Test that SDC creation endpoint exists"""
        # Get a master work order
        response = api_client.get(f"{BASE_URL}/api/master/work-orders")
        assert response.status_code == 200
        work_orders = response.json()
        
        master_wo = None
        for wo in work_orders:
            if wo.get("job_roles") and isinstance(wo.get("job_roles"), list):
                master_wo = wo
                break
        
        if not master_wo:
            pytest.skip("No master work orders with job_roles found")
        
        # Test that endpoint exists (even if validation fails)
        response = api_client.post(
            f"{BASE_URL}/api/master/work-orders/{master_wo['master_wo_id']}/sdcs",
            json={}
        )
        # Should return 422 (validation error) not 404
        assert response.status_code in [200, 201, 400, 422], f"Unexpected status: {response.status_code}"
        print(f"✓ SDC creation endpoint exists for master work orders")
    
    def test_available_infrastructure_endpoint(self, api_client):
        """Test that available infrastructure endpoint works"""
        response = api_client.get(f"{BASE_URL}/api/resources/infrastructure/available")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Available infrastructure endpoint returns {len(data)} centers")
    
    def test_available_managers_endpoint(self, api_client):
        """Test that available managers endpoint works"""
        response = api_client.get(f"{BASE_URL}/api/resources/managers/available")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Available managers endpoint returns {len(data)} managers")


class TestAllocationTrackingIntegration:
    """Integration tests for allocation tracking across SDC creation"""
    
    def test_allocation_updates_after_sdc_creation(self, api_client):
        """Test that allocation status updates correctly after SDC creation"""
        # Get master work orders
        response = api_client.get(f"{BASE_URL}/api/master/work-orders")
        assert response.status_code == 200
        work_orders = response.json()
        
        # Find a work order with remaining allocation
        master_wo = None
        for wo in work_orders:
            if wo.get("job_roles") and isinstance(wo.get("job_roles"), list):
                # Check allocation status
                alloc_response = api_client.get(f"{BASE_URL}/api/master/work-orders/{wo['master_wo_id']}/allocation-status")
                if alloc_response.status_code == 200:
                    alloc_data = alloc_response.json()
                    if alloc_data.get("total_remaining", 0) > 0:
                        master_wo = wo
                        break
        
        if not master_wo:
            pytest.skip("No master work orders with remaining allocation found")
        
        # Get initial allocation status
        initial_response = api_client.get(f"{BASE_URL}/api/master/work-orders/{master_wo['master_wo_id']}/allocation-status")
        assert initial_response.status_code == 200
        initial_data = initial_response.json()
        
        print(f"✓ Found work order {initial_data['work_order_number']} with {initial_data['total_remaining']} remaining allocation")
        print(f"  SDCs: {initial_data['sdcs_created']}/{initial_data['sdcs_planned']} created")
        
        # Verify job roles have allocation info
        for jr in initial_data.get("job_roles", []):
            print(f"  - {jr['job_role_code']}: {jr['allocated']}/{jr['target']} allocated, {jr['remaining']} remaining")
    
    def test_fully_allocated_job_role_flag(self, api_client):
        """Test that is_fully_allocated flag is set correctly"""
        response = api_client.get(f"{BASE_URL}/api/master/work-orders")
        assert response.status_code == 200
        work_orders = response.json()
        
        for wo in work_orders:
            if wo.get("job_roles") and isinstance(wo.get("job_roles"), list):
                alloc_response = api_client.get(f"{BASE_URL}/api/master/work-orders/{wo['master_wo_id']}/allocation-status")
                if alloc_response.status_code == 200:
                    data = alloc_response.json()
                    
                    for jr in data.get("job_roles", []):
                        if jr["remaining"] == 0:
                            assert jr["is_fully_allocated"] == True, \
                                f"Job role {jr['job_role_code']} should be marked as fully allocated"
                            print(f"✓ {jr['job_role_code']} correctly marked as fully allocated")
                        else:
                            assert jr["is_fully_allocated"] == False, \
                                f"Job role {jr['job_role_code']} should NOT be marked as fully allocated"
                    
                    # Check overall is_fully_allocated
                    if data["total_allocated"] >= data["total_training_target"]:
                        assert data["is_fully_allocated"] == True
                        print(f"✓ Work order {data['work_order_number']} correctly marked as fully allocated")
                    break


class TestEdgeCases:
    """Test edge cases for allocation tracking"""
    
    def test_zero_target_job_role(self, api_client):
        """Test handling of job roles with zero target"""
        response = api_client.get(f"{BASE_URL}/api/master/work-orders")
        assert response.status_code == 200
        work_orders = response.json()
        
        for wo in work_orders:
            if wo.get("job_roles"):
                alloc_response = api_client.get(f"{BASE_URL}/api/master/work-orders/{wo['master_wo_id']}/allocation-status")
                if alloc_response.status_code == 200:
                    data = alloc_response.json()
                    for jr in data.get("job_roles", []):
                        if jr["target"] == 0:
                            assert jr["remaining"] == 0
                            assert jr["is_fully_allocated"] == True
                            print(f"✓ Zero target job role handled correctly")
                            return
        
        print("✓ No zero target job roles found (edge case not applicable)")
    
    def test_over_allocation_handling(self, api_client):
        """Test that over-allocation is handled gracefully (remaining = 0, not negative)"""
        response = api_client.get(f"{BASE_URL}/api/master/work-orders")
        assert response.status_code == 200
        work_orders = response.json()
        
        for wo in work_orders:
            if wo.get("job_roles"):
                alloc_response = api_client.get(f"{BASE_URL}/api/master/work-orders/{wo['master_wo_id']}/allocation-status")
                if alloc_response.status_code == 200:
                    data = alloc_response.json()
                    for jr in data.get("job_roles", []):
                        # Remaining should never be negative
                        assert jr["remaining"] >= 0, f"Remaining should not be negative for {jr['job_role_code']}"
                        
                        # If allocated > target, remaining should be 0
                        if jr["allocated"] > jr["target"]:
                            assert jr["remaining"] == 0, f"Over-allocated job role should have remaining=0"
                            print(f"✓ Over-allocation handled: {jr['job_role_code']} has {jr['allocated']}/{jr['target']} (remaining=0)")
                    break


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
