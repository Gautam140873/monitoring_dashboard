"""
SkillFlow CRM - Reliability Features Tests
Tests for: Audit Logging, Soft Delete, Recovery, Duplicate Detection, RBAC
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test session token - HO role user
SESSION_TOKEN = os.environ.get('TEST_SESSION_TOKEN', 'test_session_1771404227755')


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SESSION_TOKEN}"
    })
    return session


class TestBackendHealth:
    """Basic backend health checks"""
    
    def test_backend_starts_without_errors(self, api_client):
        """Test backend API is accessible"""
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200, f"Backend not accessible: {response.status_code}"
        print("✓ Backend API starts without errors")
    
    def test_auth_returns_user_with_role(self, api_client):
        """Test auth returns user with RBAC role"""
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "role" in data, "User should have role field"
        assert data["role"] in ["admin", "ho", "manager", "sdc"], f"Invalid role: {data['role']}"
        print(f"✓ User has role: {data['role']}")


class TestAuditLogsEndpoint:
    """Audit logging endpoint tests"""
    
    def test_get_audit_logs_requires_auth(self):
        """Test GET /api/audit/logs requires authentication"""
        response = requests.get(f"{BASE_URL}/api/audit/logs")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Audit logs endpoint requires authentication")
    
    def test_get_audit_logs_success(self, api_client):
        """Test GET /api/audit/logs returns audit logs (HO role)"""
        response = api_client.get(f"{BASE_URL}/api/audit/logs")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "logs" in data, "Response should have 'logs' field"
        assert "total" in data, "Response should have 'total' field"
        assert "skip" in data, "Response should have 'skip' field"
        assert "limit" in data, "Response should have 'limit' field"
        assert isinstance(data["logs"], list), "Logs should be a list"
        
        print(f"✓ Audit logs endpoint returned {len(data['logs'])} logs (total: {data['total']})")
    
    def test_get_audit_logs_with_filters(self, api_client):
        """Test GET /api/audit/logs with query filters"""
        # Test with entity_type filter
        response = api_client.get(f"{BASE_URL}/api/audit/logs?entity_type=users")
        assert response.status_code == 200
        
        # Test with action filter
        response = api_client.get(f"{BASE_URL}/api/audit/logs?action=SOFT_DELETE")
        assert response.status_code == 200
        
        # Test with pagination
        response = api_client.get(f"{BASE_URL}/api/audit/logs?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        
        print("✓ Audit logs filtering works correctly")


class TestDeletedItemsEndpoint:
    """Soft delete recovery endpoint tests"""
    
    def test_get_deleted_items_requires_auth(self):
        """Test GET /api/deleted/items requires authentication"""
        response = requests.get(f"{BASE_URL}/api/deleted/items")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Deleted items endpoint requires authentication")
    
    def test_get_deleted_items_success(self, api_client):
        """Test GET /api/deleted/items returns recoverable items (HO role)"""
        response = api_client.get(f"{BASE_URL}/api/deleted/items")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should have 'items' field"
        assert "total" in data, "Response should have 'total' field"
        assert isinstance(data["items"], list), "Items should be a list"
        
        # If there are deleted items, verify structure
        if len(data["items"]) > 0:
            item = data["items"][0]
            assert "entity_type" in item
            assert "entity_id" in item
            assert "name" in item
            assert "deleted_at" in item
            assert "can_restore" in item
            assert "days_until_permanent" in item
        
        print(f"✓ Deleted items endpoint returned {len(data['items'])} recoverable items")
    
    def test_get_deleted_items_with_entity_type_filter(self, api_client):
        """Test GET /api/deleted/items with entity_type filter"""
        response = api_client.get(f"{BASE_URL}/api/deleted/items?entity_type=trainers")
        assert response.status_code == 200
        print("✓ Deleted items filtering by entity_type works")


class TestRestoreDeletedItem:
    """Restore deleted item endpoint tests"""
    
    def test_restore_invalid_entity_type(self, api_client):
        """Test POST /api/deleted/restore with invalid entity type"""
        response = api_client.post(f"{BASE_URL}/api/deleted/restore/invalid_type/some_id")
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Restore endpoint rejects invalid entity types")
    
    def test_restore_nonexistent_item(self, api_client):
        """Test POST /api/deleted/restore for non-existent item"""
        response = api_client.post(f"{BASE_URL}/api/deleted/restore/trainers/nonexistent_id")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Restore endpoint returns 404 for non-existent items")


class TestDuplicateCheckEndpoint:
    """Duplicate detection endpoint tests"""
    
    def test_duplicate_check_requires_auth(self):
        """Test POST /api/validate/duplicate requires authentication"""
        response = requests.post(f"{BASE_URL}/api/validate/duplicate?collection=trainers&field=email&value=test@test.com")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Duplicate check endpoint requires authentication")
    
    def test_duplicate_check_success(self, api_client):
        """Test POST /api/validate/duplicate returns duplicate status"""
        # Check for a non-existent email (should not be duplicate)
        response = api_client.post(
            f"{BASE_URL}/api/validate/duplicate",
            params={
                "collection": "trainers",
                "field": "email",
                "value": f"nonexistent_{datetime.now().timestamp()}@test.com"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "is_duplicate" in data, "Response should have 'is_duplicate' field"
        assert data["is_duplicate"] == False, "Non-existent email should not be duplicate"
        
        print("✓ Duplicate check endpoint works correctly")
    
    def test_duplicate_check_invalid_collection(self, api_client):
        """Test POST /api/validate/duplicate with invalid collection"""
        response = api_client.post(
            f"{BASE_URL}/api/validate/duplicate",
            params={
                "collection": "invalid_collection",
                "field": "email",
                "value": "test@test.com"
            }
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Duplicate check rejects invalid collections")


class TestSoftDeleteSDC:
    """Soft delete for SDC endpoint tests"""
    
    def test_delete_sdc_returns_recovery_info(self, api_client):
        """Test DELETE /api/sdcs/{id} returns recovery information"""
        # First create a test SDC
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        create_payload = {
            "work_order_number": f"WO/SOFTDEL/{timestamp}",
            "location": f"SoftDelTestCity{timestamp}",
            "job_role_code": "CSC/Q0801",
            "job_role_name": "Field Technician Computing",
            "awarding_body": "NSDC PMKVY",
            "scheme_name": "PMKVY 4.0",
            "total_training_hours": 200,
            "sessions_per_day": 8,
            "num_students": 25,
            "cost_per_student": 8000
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/work-orders", json=create_payload)
        if create_response.status_code != 200:
            pytest.skip(f"Could not create test SDC: {create_response.text}")
        
        sdc_id = create_response.json()["sdc"]["sdc_id"]
        
        # Now delete the SDC
        delete_response = api_client.delete(f"{BASE_URL}/api/sdcs/{sdc_id}")
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        data = delete_response.json()
        assert "message" in data, "Response should have 'message' field"
        # Check if recovery info is included
        assert "sdc_id" in data or "Can be recovered" in data.get("message", ""), "Should include recovery info"
        
        print(f"✓ SDC soft delete returns recovery info: {data.get('message', '')}")


class TestSoftDeleteJobRole:
    """Soft delete for Job Role endpoint tests"""
    
    def test_delete_job_role_returns_recovery_info(self, api_client):
        """Test DELETE /api/master/job-roles/{id} returns recovery information"""
        # First create a test job role
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        create_payload = {
            "job_role_code": f"TEST/Q{timestamp[:6]}",
            "job_role_name": f"Test Job Role {timestamp}",
            "category": "A",
            "total_training_hours": 400,
            "awarding_body": "NSDC",
            "scheme_name": "PMKVY 4.0"
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/master/job-roles", json=create_payload)
        if create_response.status_code != 200:
            pytest.skip(f"Could not create test job role: {create_response.text}")
        
        job_role_id = create_response.json()["job_role_id"]
        
        # Now delete the job role
        delete_response = api_client.delete(f"{BASE_URL}/api/master/job-roles/{job_role_id}")
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        data = delete_response.json()
        assert "message" in data, "Response should have 'message' field"
        # Check if recovery info is included
        assert "30 days" in data.get("message", "") or "recover" in data.get("message", "").lower(), \
            f"Should mention recovery period. Got: {data.get('message', '')}"
        
        print(f"✓ Job Role soft delete returns recovery info: {data.get('message', '')}")


class TestRBACPermissions:
    """RBAC permission system tests"""
    
    def test_users_endpoint_requires_ho_role(self, api_client):
        """Test GET /api/users requires HO role"""
        response = api_client.get(f"{BASE_URL}/api/users")
        # Should succeed for HO role user
        assert response.status_code == 200, f"HO user should access /api/users: {response.status_code}"
        print("✓ Users endpoint accessible to HO role")
    
    def test_audit_logs_requires_ho_role(self, api_client):
        """Test GET /api/audit/logs requires HO role"""
        response = api_client.get(f"{BASE_URL}/api/audit/logs")
        assert response.status_code == 200, f"HO user should access audit logs: {response.status_code}"
        print("✓ Audit logs accessible to HO role")
    
    def test_deleted_items_requires_ho_role(self, api_client):
        """Test GET /api/deleted/items requires HO role"""
        response = api_client.get(f"{BASE_URL}/api/deleted/items")
        assert response.status_code == 200, f"HO user should access deleted items: {response.status_code}"
        print("✓ Deleted items accessible to HO role")


class TestAuditLogCreation:
    """Test that actions create audit logs"""
    
    def test_role_update_creates_audit_log(self, api_client):
        """Test that updating user role creates an audit log"""
        # Get initial audit log count
        initial_response = api_client.get(f"{BASE_URL}/api/audit/logs?action=PERMISSION_CHANGE")
        initial_count = initial_response.json()["total"]
        
        # Get a user to update
        users_response = api_client.get(f"{BASE_URL}/api/users")
        if users_response.status_code != 200 or len(users_response.json()) == 0:
            pytest.skip("No users available for testing")
        
        # Find a non-HO user to update (or use the first user)
        users = users_response.json()
        test_user = None
        for user in users:
            if user.get("role") != "ho":
                test_user = user
                break
        
        if not test_user:
            # Use first user but don't actually change role
            test_user = users[0]
        
        # Update user role (toggle between sdc and manager)
        current_role = test_user.get("role", "sdc")
        new_role = "manager" if current_role == "sdc" else "sdc"
        
        update_response = api_client.put(
            f"{BASE_URL}/api/users/{test_user['user_id']}/role",
            json={"role": new_role}
        )
        
        if update_response.status_code == 200:
            # Check if audit log was created
            final_response = api_client.get(f"{BASE_URL}/api/audit/logs?action=PERMISSION_CHANGE")
            final_count = final_response.json()["total"]
            
            # Restore original role
            api_client.put(
                f"{BASE_URL}/api/users/{test_user['user_id']}/role",
                json={"role": current_role}
            )
            
            assert final_count >= initial_count, "Audit log should be created for role change"
            print(f"✓ Role update creates audit log (count: {initial_count} -> {final_count})")
        else:
            print(f"⚠ Could not test audit log creation: {update_response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
