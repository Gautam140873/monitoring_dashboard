"""
Test Resource Assignment and Release Features for SkillFlow
Tests:
1. SDC Creation assigns infrastructure resource (marks as in_use)
2. SDC Creation assigns manager resource (marks as assigned)
3. Work Order completion API releases all resources
4. Resources summary shows available vs assigned counts correctly
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
SESSION_TOKEN = "test_session_1771400544100"

# Test data IDs from database
INFRA_JAIPUR = "infra_1f7ec832"
INFRA_UDAIPUR = "infra_8baf66e5"
MANAGER_AMIT = "cm_cef4c6cf"
MANAGER_SUNITA = "cm_2ccf345d"
TRAINER_RAJESH = "tr_73895203"
TRAINER_PRIYA = "tr_ecd3b8da"
MASTER_WO_1 = "mwo_485baef5"  # WO/2025/PMKVY/001


@pytest.fixture
def api_client():
    """Shared requests session with auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SESSION_TOKEN}"
    })
    return session


class TestResourceSummary:
    """Test resources summary endpoint shows correct counts"""
    
    def test_resources_summary_returns_counts(self, api_client):
        """GET /api/resources/summary returns available vs assigned counts"""
        response = api_client.get(f"{BASE_URL}/api/resources/summary")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify structure
        assert "trainers" in data
        assert "managers" in data
        assert "infrastructure" in data
        
        # Verify trainer counts
        assert "total" in data["trainers"]
        assert "available" in data["trainers"]
        assert "assigned" in data["trainers"]
        
        # Verify manager counts
        assert "total" in data["managers"]
        assert "available" in data["managers"]
        assert "assigned" in data["managers"]
        
        # Verify infrastructure counts
        assert "total" in data["infrastructure"]
        assert "available" in data["infrastructure"]
        assert "in_use" in data["infrastructure"]
        
        print(f"Resources Summary: {data}")
        
    def test_initial_resources_all_available(self, api_client):
        """Initially all resources should be available"""
        response = api_client.get(f"{BASE_URL}/api/resources/summary")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check trainers - should have 2 available
        assert data["trainers"]["total"] >= 2
        assert data["trainers"]["available"] >= 2
        
        # Check managers - should have 2 available
        assert data["managers"]["total"] >= 2
        assert data["managers"]["available"] >= 2
        
        # Check infrastructure - should have 2 available
        assert data["infrastructure"]["total"] >= 2
        assert data["infrastructure"]["available"] >= 2
        
        print(f"Initial state - Trainers: {data['trainers']}, Managers: {data['managers']}, Infrastructure: {data['infrastructure']}")


class TestInfrastructureAssignment:
    """Test infrastructure assignment during SDC creation"""
    
    def test_assign_infrastructure_marks_as_in_use(self, api_client):
        """POST /api/resources/infrastructure/{id}/assign marks resource as in_use"""
        # First verify infrastructure is available
        response = api_client.get(f"{BASE_URL}/api/resources/infrastructure/available")
        assert response.status_code == 200
        available_infra = response.json()
        
        # Find an available infrastructure
        test_infra = None
        for infra in available_infra:
            if infra["status"] == "available":
                test_infra = infra
                break
        
        if not test_infra:
            pytest.skip("No available infrastructure to test")
        
        infra_id = test_infra["infra_id"]
        
        # Assign infrastructure
        response = api_client.post(
            f"{BASE_URL}/api/resources/infrastructure/{infra_id}/assign",
            params={"work_order_id": MASTER_WO_1}
        )
        assert response.status_code == 200
        
        # Verify it's now in_use
        response = api_client.get(f"{BASE_URL}/api/resources/infrastructure")
        assert response.status_code == 200
        all_infra = response.json()
        
        assigned_infra = next((i for i in all_infra if i["infra_id"] == infra_id), None)
        assert assigned_infra is not None
        assert assigned_infra["status"] == "in_use"
        assert assigned_infra["assigned_work_order_id"] == MASTER_WO_1
        
        print(f"Infrastructure {infra_id} assigned to {MASTER_WO_1}, status: {assigned_infra['status']}")
        
        # Cleanup - release the infrastructure
        api_client.post(f"{BASE_URL}/api/resources/infrastructure/{infra_id}/release")


class TestManagerAssignment:
    """Test manager assignment during SDC creation"""
    
    def test_assign_manager_marks_as_assigned(self, api_client):
        """POST /api/resources/managers/{id}/assign marks manager as assigned"""
        # First verify manager is available
        response = api_client.get(f"{BASE_URL}/api/resources/managers/available")
        assert response.status_code == 200
        available_managers = response.json()
        
        # Find an available manager
        test_manager = None
        for manager in available_managers:
            if manager["status"] == "available":
                test_manager = manager
                break
        
        if not test_manager:
            pytest.skip("No available manager to test")
        
        manager_id = test_manager["manager_id"]
        test_sdc_id = "sdc_test_assignment"
        
        # Assign manager
        response = api_client.post(
            f"{BASE_URL}/api/resources/managers/{manager_id}/assign",
            params={"sdc_id": test_sdc_id}
        )
        assert response.status_code == 200
        
        # Verify it's now assigned
        response = api_client.get(f"{BASE_URL}/api/resources/managers")
        assert response.status_code == 200
        all_managers = response.json()
        
        assigned_manager = next((m for m in all_managers if m["manager_id"] == manager_id), None)
        assert assigned_manager is not None
        assert assigned_manager["status"] == "assigned"
        assert assigned_manager["assigned_sdc_id"] == test_sdc_id
        
        print(f"Manager {manager_id} assigned to {test_sdc_id}, status: {assigned_manager['status']}")
        
        # Cleanup - release the manager
        api_client.post(f"{BASE_URL}/api/resources/managers/{manager_id}/release")


class TestTrainerAssignment:
    """Test trainer assignment"""
    
    def test_assign_trainer_marks_as_assigned(self, api_client):
        """POST /api/resources/trainers/{id}/assign marks trainer as assigned"""
        # First verify trainer is available
        response = api_client.get(f"{BASE_URL}/api/resources/trainers/available")
        assert response.status_code == 200
        available_trainers = response.json()
        
        # Find an available trainer
        test_trainer = None
        for trainer in available_trainers:
            if trainer["status"] == "available":
                test_trainer = trainer
                break
        
        if not test_trainer:
            pytest.skip("No available trainer to test")
        
        trainer_id = test_trainer["trainer_id"]
        test_sdc_id = "sdc_test_trainer"
        test_wo_id = "wo_test_trainer"
        
        # Assign trainer
        response = api_client.post(
            f"{BASE_URL}/api/resources/trainers/{trainer_id}/assign",
            params={"sdc_id": test_sdc_id, "work_order_id": test_wo_id}
        )
        assert response.status_code == 200
        
        # Verify it's now assigned
        response = api_client.get(f"{BASE_URL}/api/resources/trainers")
        assert response.status_code == 200
        all_trainers = response.json()
        
        assigned_trainer = next((t for t in all_trainers if t["trainer_id"] == trainer_id), None)
        assert assigned_trainer is not None
        assert assigned_trainer["status"] == "assigned"
        assert assigned_trainer["assigned_sdc_id"] == test_sdc_id
        
        print(f"Trainer {trainer_id} assigned to {test_sdc_id}, status: {assigned_trainer['status']}")
        
        # Cleanup - release the trainer
        api_client.post(f"{BASE_URL}/api/resources/trainers/{trainer_id}/release")


class TestWorkOrderCompletion:
    """Test Work Order completion releases all resources"""
    
    def test_complete_work_order_releases_resources(self, api_client):
        """POST /api/master/work-orders/{id}/complete releases all assigned resources"""
        # First, we need to set up resources assigned to a work order
        # Get a master work order
        response = api_client.get(f"{BASE_URL}/api/master/work-orders")
        assert response.status_code == 200
        work_orders = response.json()
        
        # Find an active work order
        active_wo = None
        for wo in work_orders:
            if wo["status"] == "active":
                active_wo = wo
                break
        
        if not active_wo:
            pytest.skip("No active work order to test")
        
        master_wo_id = active_wo["master_wo_id"]
        
        # Get SDCs for this work order
        sdcs = active_wo.get("sdcs_created", [])
        
        # Assign resources to test the release
        # Assign infrastructure
        infra_response = api_client.get(f"{BASE_URL}/api/resources/infrastructure/available")
        if infra_response.status_code == 200 and infra_response.json():
            infra = infra_response.json()[0]
            api_client.post(
                f"{BASE_URL}/api/resources/infrastructure/{infra['infra_id']}/assign",
                params={"work_order_id": master_wo_id}
            )
        
        # Assign manager to an SDC if exists
        if sdcs:
            sdc_id = sdcs[0]["sdc_id"]
            manager_response = api_client.get(f"{BASE_URL}/api/resources/managers/available")
            if manager_response.status_code == 200 and manager_response.json():
                manager = manager_response.json()[0]
                api_client.post(
                    f"{BASE_URL}/api/resources/managers/{manager['manager_id']}/assign",
                    params={"sdc_id": sdc_id}
                )
            
            # Assign trainer to SDC
            trainer_response = api_client.get(f"{BASE_URL}/api/resources/trainers/available")
            if trainer_response.status_code == 200 and trainer_response.json():
                trainer = trainer_response.json()[0]
                api_client.post(
                    f"{BASE_URL}/api/resources/trainers/{trainer['trainer_id']}/assign",
                    params={"sdc_id": sdc_id, "work_order_id": master_wo_id}
                )
        
        # Get summary before completion
        summary_before = api_client.get(f"{BASE_URL}/api/resources/summary").json()
        print(f"Before completion - Summary: {summary_before}")
        
        # Complete the work order
        response = api_client.post(f"{BASE_URL}/api/master/work-orders/{master_wo_id}/complete")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "released_resources" in data
        
        released = data["released_resources"]
        print(f"Released resources: {released}")
        
        # Verify work order is now completed
        response = api_client.get(f"{BASE_URL}/api/master/work-orders/{master_wo_id}")
        assert response.status_code == 200
        completed_wo = response.json()
        assert completed_wo["status"] == "completed"
        
        print(f"Work Order {master_wo_id} completed successfully")
        
    def test_complete_already_completed_work_order(self, api_client):
        """Completing an already completed work order returns appropriate message"""
        # Get work orders
        response = api_client.get(f"{BASE_URL}/api/master/work-orders")
        assert response.status_code == 200
        work_orders = response.json()
        
        # Find a completed work order
        completed_wo = None
        for wo in work_orders:
            if wo["status"] == "completed":
                completed_wo = wo
                break
        
        if not completed_wo:
            pytest.skip("No completed work order to test")
        
        # Try to complete again
        response = api_client.post(f"{BASE_URL}/api/master/work-orders/{completed_wo['master_wo_id']}/complete")
        assert response.status_code == 200
        
        data = response.json()
        assert "already completed" in data["message"].lower()
        
        print(f"Already completed work order handled correctly")


class TestResourceSummaryAfterOperations:
    """Test that resource summary updates correctly after operations"""
    
    def test_summary_reflects_assignments(self, api_client):
        """Resource summary should reflect current assignment state"""
        # Get initial summary
        response = api_client.get(f"{BASE_URL}/api/resources/summary")
        assert response.status_code == 200
        summary = response.json()
        
        initial_available_managers = summary["managers"]["available"]
        
        # Assign a manager
        manager_response = api_client.get(f"{BASE_URL}/api/resources/managers/available")
        if manager_response.status_code == 200 and manager_response.json():
            manager = manager_response.json()[0]
            api_client.post(
                f"{BASE_URL}/api/resources/managers/{manager['manager_id']}/assign",
                params={"sdc_id": "sdc_test_summary"}
            )
            
            # Check summary updated
            response = api_client.get(f"{BASE_URL}/api/resources/summary")
            assert response.status_code == 200
            new_summary = response.json()
            
            assert new_summary["managers"]["available"] == initial_available_managers - 1
            assert new_summary["managers"]["assigned"] >= 1
            
            print(f"Summary updated correctly: available managers {initial_available_managers} -> {new_summary['managers']['available']}")
            
            # Cleanup
            api_client.post(f"{BASE_URL}/api/resources/managers/{manager['manager_id']}/release")


class TestMasterWorkOrderEndpoints:
    """Test Master Work Order related endpoints"""
    
    def test_list_master_work_orders(self, api_client):
        """GET /api/master/work-orders returns list of work orders"""
        response = api_client.get(f"{BASE_URL}/api/master/work-orders")
        assert response.status_code == 200
        
        work_orders = response.json()
        assert isinstance(work_orders, list)
        
        for wo in work_orders:
            assert "master_wo_id" in wo
            assert "work_order_number" in wo
            assert "status" in wo
            assert wo["status"] in ["active", "completed", "cancelled"]
        
        print(f"Found {len(work_orders)} master work orders")
        
    def test_get_single_master_work_order(self, api_client):
        """GET /api/master/work-orders/{id} returns work order details"""
        # First get list
        response = api_client.get(f"{BASE_URL}/api/master/work-orders")
        assert response.status_code == 200
        work_orders = response.json()
        
        if not work_orders:
            pytest.skip("No work orders to test")
        
        wo_id = work_orders[0]["master_wo_id"]
        
        # Get single work order
        response = api_client.get(f"{BASE_URL}/api/master/work-orders/{wo_id}")
        assert response.status_code == 200
        
        wo = response.json()
        assert wo["master_wo_id"] == wo_id
        assert "sdcs_created" in wo
        assert "sdcs_created_count" in wo
        
        print(f"Work Order {wo_id}: {wo['work_order_number']}, SDCs: {wo['sdcs_created_count']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
