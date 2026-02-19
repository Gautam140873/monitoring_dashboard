"""
Test suite for SkillFlow CRM Ledger Features
Tests: Target Ledger, Resource Locking, Burn-down Dashboard
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test session token - will be set in conftest or fixture
SESSION_TOKEN = None


@pytest.fixture(scope="module")
def auth_session():
    """Create authenticated session for testing"""
    global SESSION_TOKEN
    
    # Create test user and session via mongosh
    import subprocess
    result = subprocess.run([
        'mongosh', '--quiet', '--eval', '''
        use('test_database');
        var userId = 'test-ledger-' + Date.now();
        var sessionToken = 'test_session_ledger_pytest_' + Date.now();
        db.users.insertOne({
          user_id: userId,
          email: 'test.ledger.pytest.' + Date.now() + '@example.com',
          name: 'Test Ledger Pytest User',
          picture: 'https://via.placeholder.com/150',
          role: 'ho',
          assigned_sdc_id: null,
          created_at: new Date()
        });
        db.user_sessions.insertOne({
          user_id: userId,
          session_token: sessionToken,
          expires_at: new Date(Date.now() + 7*24*60*60*1000),
          created_at: new Date()
        });
        print(sessionToken);
        '''
    ], capture_output=True, text=True)
    
    SESSION_TOKEN = result.stdout.strip().split('\n')[-1]
    
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SESSION_TOKEN}"
    })
    
    yield session
    
    # Cleanup test data
    subprocess.run([
        'mongosh', '--quiet', '--eval', f'''
        use('test_database');
        db.users.deleteMany({{email: /test\\.ledger\\.pytest\\./}});
        db.user_sessions.deleteMany({{session_token: /test_session_ledger_pytest_/}});
        '''
    ], capture_output=True, text=True)


class TestBurndownDashboard:
    """Tests for Burn-down Dashboard endpoints"""
    
    def test_burndown_returns_data(self, auth_session):
        """GET /api/ledger/burndown returns burndown data"""
        response = auth_session.get(f"{BASE_URL}/api/ledger/burndown")
        assert response.status_code == 200
        
        data = response.json()
        assert "work_orders" in data
        assert "overall" in data
        assert "generated_at" in data
        
        # Verify overall structure
        overall = data["overall"]
        assert "total_work_orders" in overall
        assert "total_target" in overall
        assert "total_allocated" in overall
        assert "total_mobilized" in overall
        assert "total_placed" in overall
        assert "total_unallocated" in overall
        assert "overall_completion" in overall
        
        print(f"✓ Burndown: {overall['total_work_orders']} work orders, {overall['total_target']} total target")
    
    def test_burndown_work_order_structure(self, auth_session):
        """Verify work order structure in burndown data"""
        response = auth_session.get(f"{BASE_URL}/api/ledger/burndown")
        assert response.status_code == 200
        
        data = response.json()
        if data["work_orders"]:
            wo = data["work_orders"][0]
            assert "master_wo_id" in wo
            assert "work_order_number" in wo
            assert "total_target" in wo
            assert "pipeline" in wo
            assert "summary" in wo
            
            # Verify pipeline structure
            pipeline = wo["pipeline"]
            assert "unallocated" in pipeline
            assert "allocated_not_started" in pipeline
            assert "mobilized" in pipeline
            assert "in_training" in pipeline
            assert "placed" in pipeline
            
            print(f"✓ Work order {wo['work_order_number']} pipeline verified")
    
    def test_burndown_specific_work_order(self, auth_session):
        """GET /api/ledger/burndown/{master_wo_id} returns specific WO data"""
        # First get list of work orders
        response = auth_session.get(f"{BASE_URL}/api/ledger/burndown")
        assert response.status_code == 200
        
        data = response.json()
        if data["work_orders"]:
            master_wo_id = data["work_orders"][0]["master_wo_id"]
            
            # Get specific work order burndown
            response = auth_session.get(f"{BASE_URL}/api/ledger/burndown/{master_wo_id}")
            assert response.status_code == 200
            
            wo_data = response.json()
            assert wo_data["master_wo_id"] == master_wo_id
            assert "pipeline" in wo_data
            assert "summary" in wo_data
            
            print(f"✓ Specific burndown for {master_wo_id} verified")


class TestTargetLedger:
    """Tests for Target Ledger endpoints"""
    
    def test_target_ledger_returns_data(self, auth_session):
        """GET /api/ledger/target/{master_wo_id} returns ledger data"""
        # Get a master work order with allocations
        response = auth_session.get(f"{BASE_URL}/api/master/work-orders")
        assert response.status_code == 200
        
        work_orders = response.json()
        # Find one with job_roles
        master_wo_id = None
        for wo in work_orders:
            if wo.get("job_roles"):
                master_wo_id = wo["master_wo_id"]
                break
        
        if master_wo_id:
            response = auth_session.get(f"{BASE_URL}/api/ledger/target/{master_wo_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["master_wo_id"] == master_wo_id
            assert "work_order_number" in data
            assert "total_training_target" in data
            assert "total_allocated" in data
            assert "total_remaining" in data
            assert "job_roles" in data
            assert "is_fully_allocated" in data
            
            print(f"✓ Target ledger for {master_wo_id}: {data['total_allocated']}/{data['total_training_target']} allocated")
    
    def test_target_ledger_job_role_structure(self, auth_session):
        """Verify job role structure in target ledger"""
        response = auth_session.get(f"{BASE_URL}/api/master/work-orders")
        work_orders = response.json()
        
        master_wo_id = None
        for wo in work_orders:
            if wo.get("job_roles"):
                master_wo_id = wo["master_wo_id"]
                break
        
        if master_wo_id:
            response = auth_session.get(f"{BASE_URL}/api/ledger/target/{master_wo_id}")
            data = response.json()
            
            if data["job_roles"]:
                jr = data["job_roles"][0]
                assert "job_role_id" in jr
                assert "job_role_code" in jr
                assert "job_role_name" in jr
                assert "total_target" in jr
                assert "allocated" in jr
                assert "remaining" in jr
                assert "utilization_percent" in jr
                assert "is_fully_allocated" in jr
                assert "sdc_allocations" in jr
                
                print(f"✓ Job role {jr['job_role_code']}: {jr['allocated']}/{jr['total_target']} ({jr['utilization_percent']}%)")
    
    def test_target_ledger_not_found(self, auth_session):
        """GET /api/ledger/target/{invalid_id} returns 404"""
        response = auth_session.get(f"{BASE_URL}/api/ledger/target/invalid_mwo_id")
        assert response.status_code == 404
        print("✓ Invalid master_wo_id returns 404")
    
    def test_all_ledgers_endpoint(self, auth_session):
        """GET /api/ledger/all-ledgers returns all active ledgers"""
        response = auth_session.get(f"{BASE_URL}/api/ledger/all-ledgers")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if data:
            ledger = data[0]
            assert "master_wo_id" in ledger
            assert "work_order_number" in ledger
            assert "total_allocated" in ledger
            
        print(f"✓ All ledgers: {len(data)} active work orders")


class TestAllocationValidation:
    """Tests for Allocation Validation endpoint"""
    
    def test_validate_allocation_valid(self, auth_session):
        """POST /api/ledger/validate-allocation with valid allocation"""
        # Find a work order with remaining capacity
        response = auth_session.get(f"{BASE_URL}/api/ledger/all-ledgers")
        ledgers = response.json()
        
        target_wo = None
        target_jr = None
        for ledger in ledgers:
            for jr in ledger.get("job_roles", []):
                if jr["remaining"] > 0:
                    target_wo = ledger["master_wo_id"]
                    target_jr = jr["job_role_id"]
                    remaining = jr["remaining"]
                    break
            if target_wo:
                break
        
        if target_wo and target_jr:
            # Request less than remaining
            request_students = min(10, remaining)
            response = auth_session.post(
                f"{BASE_URL}/api/ledger/validate-allocation",
                json={
                    "master_wo_id": target_wo,
                    "job_role_id": target_jr,
                    "requested_students": request_students
                }
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["is_valid"] == True
            assert data["remaining"] >= request_students
            assert "remaining_after" in data
            
            print(f"✓ Valid allocation: {request_students} students, {data['remaining_after']} remaining after")
    
    def test_validate_allocation_over_allocation(self, auth_session):
        """POST /api/ledger/validate-allocation with over-allocation returns 400"""
        # Find a work order with job roles
        response = auth_session.get(f"{BASE_URL}/api/ledger/all-ledgers")
        ledgers = response.json()
        
        target_wo = None
        target_jr = None
        for ledger in ledgers:
            for jr in ledger.get("job_roles", []):
                target_wo = ledger["master_wo_id"]
                target_jr = jr["job_role_id"]
                remaining = jr["remaining"]
                break
            if target_wo:
                break
        
        if target_wo and target_jr:
            # Request more than remaining
            response = auth_session.post(
                f"{BASE_URL}/api/ledger/validate-allocation",
                json={
                    "master_wo_id": target_wo,
                    "job_role_id": target_jr,
                    "requested_students": 99999  # Way more than any target
                }
            )
            assert response.status_code == 400
            
            data = response.json()
            assert "detail" in data
            assert data["detail"]["is_valid"] == False
            assert "Over-allocation" in data["detail"]["error"]
            
            print(f"✓ Over-allocation prevented: {data['detail']['error']}")
    
    def test_validate_allocation_invalid_work_order(self, auth_session):
        """POST /api/ledger/validate-allocation with invalid WO returns error"""
        response = auth_session.post(
            f"{BASE_URL}/api/ledger/validate-allocation",
            json={
                "master_wo_id": "invalid_mwo",
                "job_role_id": "invalid_jr",
                "requested_students": 10
            }
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert data["detail"]["is_valid"] == False
        
        print("✓ Invalid work order returns validation error")


class TestResourceAvailability:
    """Tests for Resource Availability Check endpoints"""
    
    def test_check_trainer_availability(self, auth_session):
        """GET /api/ledger/resource/check/trainer/{id} returns availability"""
        # Get available trainers
        response = auth_session.get(f"{BASE_URL}/api/resources/trainers/available")
        trainers = response.json()
        
        if trainers:
            trainer_id = trainers[0]["trainer_id"]
            
            response = auth_session.get(f"{BASE_URL}/api/ledger/resource/check/trainer/{trainer_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert "is_available" in data
            assert "resource" in data
            assert data["resource"]["id"] == trainer_id
            
            print(f"✓ Trainer {trainer_id} availability: {data['is_available']}")
    
    def test_check_manager_availability(self, auth_session):
        """GET /api/ledger/resource/check/manager/{id} returns availability"""
        response = auth_session.get(f"{BASE_URL}/api/resources/managers/available")
        managers = response.json()
        
        if managers:
            manager_id = managers[0]["manager_id"]
            
            response = auth_session.get(f"{BASE_URL}/api/ledger/resource/check/manager/{manager_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert "is_available" in data
            assert "resource" in data
            
            print(f"✓ Manager {manager_id} availability: {data['is_available']}")
    
    def test_check_invalid_resource_type(self, auth_session):
        """GET /api/ledger/resource/check/{invalid_type}/{id} returns error"""
        response = auth_session.get(f"{BASE_URL}/api/ledger/resource/check/invalid_type/some_id")
        assert response.status_code == 200  # Returns error in body
        
        data = response.json()
        assert data["is_available"] == False
        assert "Unknown resource type" in data["error"]
        
        print("✓ Invalid resource type returns error")
    
    def test_check_nonexistent_resource(self, auth_session):
        """GET /api/ledger/resource/check/trainer/{invalid_id} returns not found"""
        response = auth_session.get(f"{BASE_URL}/api/ledger/resource/check/trainer/invalid_trainer_id")
        assert response.status_code == 200  # Returns error in body
        
        data = response.json()
        assert data["is_available"] == False
        assert "not found" in data["error"]
        
        print("✓ Nonexistent resource returns not found error")


class TestResourceLocking:
    """Tests for Resource Locking endpoints"""
    
    def test_lock_and_release_trainer(self, auth_session):
        """POST /api/ledger/resource/lock and release flow"""
        # Get available trainer
        response = auth_session.get(f"{BASE_URL}/api/resources/trainers/available")
        trainers = response.json()
        
        if not trainers:
            pytest.skip("No available trainers for testing")
        
        trainer_id = trainers[0]["trainer_id"]
        
        # Lock the trainer
        response = auth_session.post(
            f"{BASE_URL}/api/ledger/resource/lock",
            json={
                "resource_type": "trainer",
                "resource_id": trainer_id,
                "sdc_id": "sdc_pytest_test",
                "work_order_id": "wo_pytest_test"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "booking_id" in data
        
        print(f"✓ Trainer {trainer_id} locked, booking_id: {data['booking_id']}")
        
        # Verify trainer is now unavailable
        response = auth_session.get(f"{BASE_URL}/api/ledger/resource/check/trainer/{trainer_id}")
        data = response.json()
        assert data["is_available"] == False
        
        print(f"✓ Trainer {trainer_id} confirmed unavailable after lock")
        
        # Release the trainer
        response = auth_session.post(f"{BASE_URL}/api/ledger/resource/release/trainer/{trainer_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        
        print(f"✓ Trainer {trainer_id} released")
        
        # Verify trainer is available again
        response = auth_session.get(f"{BASE_URL}/api/ledger/resource/check/trainer/{trainer_id}")
        data = response.json()
        assert data["is_available"] == True
        
        print(f"✓ Trainer {trainer_id} confirmed available after release")
    
    def test_double_booking_prevention(self, auth_session):
        """POST /api/ledger/resource/lock prevents double-booking"""
        # Get available trainer
        response = auth_session.get(f"{BASE_URL}/api/resources/trainers/available")
        trainers = response.json()
        
        if not trainers:
            pytest.skip("No available trainers for testing")
        
        trainer_id = trainers[0]["trainer_id"]
        
        # Lock the trainer
        response = auth_session.post(
            f"{BASE_URL}/api/ledger/resource/lock",
            json={
                "resource_type": "trainer",
                "resource_id": trainer_id,
                "sdc_id": "sdc_pytest_first",
                "work_order_id": "wo_pytest_first"
            }
        )
        assert response.status_code == 200
        
        # Try to lock again - should fail
        response = auth_session.post(
            f"{BASE_URL}/api/ledger/resource/lock",
            json={
                "resource_type": "trainer",
                "resource_id": trainer_id,
                "sdc_id": "sdc_pytest_second",
                "work_order_id": "wo_pytest_second"
            }
        )
        assert response.status_code == 409  # Conflict
        
        data = response.json()
        assert "detail" in data
        assert data["detail"]["success"] == False
        assert "already assigned" in data["detail"]["error"]
        
        print(f"✓ Double-booking prevented for trainer {trainer_id}")
        
        # Cleanup - release the trainer
        auth_session.post(f"{BASE_URL}/api/ledger/resource/release/trainer/{trainer_id}")


class TestResourceSummary:
    """Tests for Resource Summary endpoint"""
    
    def test_resource_summary_structure(self, auth_session):
        """GET /api/ledger/resource/summary returns correct structure"""
        response = auth_session.get(f"{BASE_URL}/api/ledger/resource/summary")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify trainers summary
        assert "trainers" in data
        assert "total" in data["trainers"]
        assert "available" in data["trainers"]
        assert "assigned" in data["trainers"]
        assert "on_leave" in data["trainers"]
        
        # Verify managers summary
        assert "managers" in data
        assert "total" in data["managers"]
        assert "available" in data["managers"]
        assert "assigned" in data["managers"]
        
        # Verify infrastructure summary
        assert "infrastructure" in data
        assert "total" in data["infrastructure"]
        assert "available" in data["infrastructure"]
        assert "in_use" in data["infrastructure"]
        assert "maintenance" in data["infrastructure"]
        
        print(f"✓ Resource summary: {data['trainers']['total']} trainers, {data['managers']['total']} managers, {data['infrastructure']['total']} infrastructure")
    
    def test_resource_summary_counts_match(self, auth_session):
        """Verify resource summary counts are consistent"""
        response = auth_session.get(f"{BASE_URL}/api/ledger/resource/summary")
        data = response.json()
        
        # Trainers: total should equal sum of statuses
        trainers = data["trainers"]
        assert trainers["total"] >= trainers["available"] + trainers["assigned"] + trainers["on_leave"]
        
        # Managers: total should equal sum of statuses
        managers = data["managers"]
        assert managers["total"] >= managers["available"] + managers["assigned"]
        
        print("✓ Resource summary counts are consistent")


class TestResourceHistory:
    """Tests for Resource Booking History endpoint"""
    
    def test_resource_history_endpoint(self, auth_session):
        """GET /api/ledger/resource/history/{type}/{id} returns history"""
        # Get a trainer
        response = auth_session.get(f"{BASE_URL}/api/resources/trainers")
        trainers = response.json()
        
        if trainers:
            trainer_id = trainers[0]["trainer_id"]
            
            response = auth_session.get(f"{BASE_URL}/api/ledger/resource/history/trainer/{trainer_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            
            print(f"✓ Trainer {trainer_id} has {len(data)} booking history records")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
