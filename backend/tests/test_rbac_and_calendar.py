"""
Test suite for Refined RBAC and Resource Calendar features
Tests:
1. Refined RBAC - Manager role can only update their assigned SDC
2. Refined RBAC - HO role can update any SDC
3. Resource Calendar API - GET /api/ledger/resource/calendar
4. Resource Calendar shows trainers/managers/infrastructure grouped by status
5. Resource release functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials created in MongoDB
HO_SESSION_TOKEN = "test_session_ho_1771502416635"
MANAGER_SESSION_TOKEN = "test_session_manager_1771502416659"
MANAGER_ASSIGNED_SDC = "sdc_gurugram"
OTHER_SDC = "sdc_other_1771502416663"


class TestRefinedRBAC:
    """Test Refined RBAC - Manager can only update assigned SDC, HO can update any"""
    
    def test_ho_can_access_any_sdc(self):
        """HO role should be able to read any SDC"""
        response = requests.get(
            f"{BASE_URL}/api/sdcs",
            headers={"Authorization": f"Bearer {HO_SESSION_TOKEN}"}
        )
        assert response.status_code == 200, f"HO should access SDCs list: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return list of SDCs"
        print(f"✓ HO can access SDCs list - found {len(data)} SDCs")
    
    def test_ho_can_update_any_sdc_process_stage(self):
        """HO role should be able to update any SDC's process stage"""
        # First get an SDC
        response = requests.get(
            f"{BASE_URL}/api/sdcs",
            headers={"Authorization": f"Bearer {HO_SESSION_TOKEN}"}
        )
        assert response.status_code == 200
        sdcs = response.json()
        
        if len(sdcs) == 0:
            pytest.skip("No SDCs available for testing")
        
        sdc_id = sdcs[0]["sdc_id"]
        
        # Try to update process stage
        response = requests.put(
            f"{BASE_URL}/api/sdcs/{sdc_id}/process-status/stage/mobilization",
            params={"notes": "HO test update"},
            headers={"Authorization": f"Bearer {HO_SESSION_TOKEN}"}
        )
        assert response.status_code == 200, f"HO should update any SDC: {response.text}"
        print(f"✓ HO can update SDC {sdc_id} process stage")
    
    def test_manager_can_read_all_sdcs(self):
        """Manager role should be able to read all SDCs"""
        response = requests.get(
            f"{BASE_URL}/api/sdcs",
            headers={"Authorization": f"Bearer {MANAGER_SESSION_TOKEN}"}
        )
        # Manager may only see their assigned SDC based on implementation
        assert response.status_code == 200, f"Manager should access SDCs: {response.text}"
        print(f"✓ Manager can read SDCs")
    
    def test_manager_can_update_assigned_sdc(self):
        """Manager should be able to update their assigned SDC"""
        response = requests.put(
            f"{BASE_URL}/api/sdcs/{MANAGER_ASSIGNED_SDC}/process-status/stage/mobilization",
            params={"notes": "Manager test update on assigned SDC"},
            headers={"Authorization": f"Bearer {MANAGER_SESSION_TOKEN}"}
        )
        assert response.status_code == 200, f"Manager should update assigned SDC: {response.text}"
        print(f"✓ Manager can update their assigned SDC ({MANAGER_ASSIGNED_SDC})")
    
    def test_manager_cannot_update_unassigned_sdc(self):
        """Manager should NOT be able to update SDC they are not assigned to"""
        response = requests.put(
            f"{BASE_URL}/api/sdcs/{OTHER_SDC}/process-status/stage/mobilization",
            params={"notes": "Manager trying to update unassigned SDC"},
            headers={"Authorization": f"Bearer {MANAGER_SESSION_TOKEN}"}
        )
        # Should return 403 Forbidden
        assert response.status_code == 403, f"Manager should NOT update unassigned SDC. Got {response.status_code}: {response.text}"
        data = response.json()
        assert "permission" in data.get("detail", "").lower() or "assigned" in data.get("detail", "").lower(), \
            f"Error message should mention permission/assignment: {data}"
        print(f"✓ Manager correctly denied from updating unassigned SDC ({OTHER_SDC})")
    
    def test_manager_cannot_update_deliverable_on_unassigned_sdc(self):
        """Manager should NOT be able to update deliverables on unassigned SDC"""
        response = requests.put(
            f"{BASE_URL}/api/sdcs/{OTHER_SDC}/process-status/deliverable/dress_distribution",
            params={"status": "completed"},
            headers={"Authorization": f"Bearer {MANAGER_SESSION_TOKEN}"}
        )
        assert response.status_code == 403, f"Manager should NOT update deliverable on unassigned SDC. Got {response.status_code}"
        print(f"✓ Manager correctly denied from updating deliverable on unassigned SDC")


class TestResourceCalendarAPI:
    """Test Resource Calendar API endpoint"""
    
    def test_resource_calendar_endpoint_exists(self):
        """Resource Calendar endpoint should exist and return data"""
        response = requests.get(
            f"{BASE_URL}/api/ledger/resource/calendar",
            headers={"Authorization": f"Bearer {HO_SESSION_TOKEN}"}
        )
        assert response.status_code == 200, f"Resource calendar should return 200: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "start_date" in data, "Should have start_date"
        assert "end_date" in data, "Should have end_date"
        assert "resources" in data, "Should have resources list"
        assert "grouped" in data, "Should have grouped resources"
        assert "summary" in data, "Should have summary"
        print(f"✓ Resource Calendar API returns correct structure")
    
    def test_resource_calendar_grouped_structure(self):
        """Resource Calendar should group resources by type"""
        response = requests.get(
            f"{BASE_URL}/api/ledger/resource/calendar",
            headers={"Authorization": f"Bearer {HO_SESSION_TOKEN}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        grouped = data.get("grouped", {})
        assert "trainers" in grouped, "Should have trainers group"
        assert "managers" in grouped, "Should have managers group"
        assert "infrastructure" in grouped, "Should have infrastructure group"
        
        # Each group should be a list
        assert isinstance(grouped["trainers"], list), "Trainers should be a list"
        assert isinstance(grouped["managers"], list), "Managers should be a list"
        assert isinstance(grouped["infrastructure"], list), "Infrastructure should be a list"
        
        print(f"✓ Resource Calendar groups: trainers={len(grouped['trainers'])}, managers={len(grouped['managers'])}, infrastructure={len(grouped['infrastructure'])}")
    
    def test_resource_calendar_summary_structure(self):
        """Resource Calendar summary should have counts by status"""
        response = requests.get(
            f"{BASE_URL}/api/ledger/resource/calendar",
            headers={"Authorization": f"Bearer {HO_SESSION_TOKEN}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        summary = data.get("summary", {})
        
        # Check trainers summary
        assert "trainers" in summary, "Summary should have trainers"
        assert "total" in summary["trainers"], "Trainers summary should have total"
        assert "available" in summary["trainers"], "Trainers summary should have available"
        assert "assigned" in summary["trainers"], "Trainers summary should have assigned"
        
        # Check managers summary
        assert "managers" in summary, "Summary should have managers"
        assert "total" in summary["managers"], "Managers summary should have total"
        
        # Check infrastructure summary
        assert "infrastructure" in summary, "Summary should have infrastructure"
        assert "total" in summary["infrastructure"], "Infrastructure summary should have total"
        
        print(f"✓ Resource Calendar summary: trainers={summary['trainers']}, managers={summary['managers']}, infrastructure={summary['infrastructure']}")
    
    def test_resource_calendar_filter_by_type(self):
        """Resource Calendar should filter by resource type"""
        # Filter by trainer
        response = requests.get(
            f"{BASE_URL}/api/ledger/resource/calendar",
            params={"resource_type": "trainer"},
            headers={"Authorization": f"Bearer {HO_SESSION_TOKEN}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # When filtered by trainer, only trainers should be in resources
        resources = data.get("resources", [])
        for r in resources:
            assert r.get("resource_type") == "trainer", f"Should only have trainers, got {r.get('resource_type')}"
        
        print(f"✓ Resource Calendar filter by type works - found {len(resources)} trainers")
    
    def test_resource_calendar_resource_structure(self):
        """Each resource should have required fields"""
        response = requests.get(
            f"{BASE_URL}/api/ledger/resource/calendar",
            headers={"Authorization": f"Bearer {HO_SESSION_TOKEN}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        resources = data.get("resources", [])
        if len(resources) > 0:
            resource = resources[0]
            assert "resource_type" in resource, "Resource should have resource_type"
            assert "resource_id" in resource, "Resource should have resource_id"
            assert "name" in resource, "Resource should have name"
            assert "status" in resource, "Resource should have status"
            print(f"✓ Resource structure verified: {resource.get('name')} ({resource.get('status')})")
        else:
            print("⚠ No resources found to verify structure")


class TestResourceRelease:
    """Test Resource Release functionality"""
    
    def test_resource_release_endpoint_exists(self):
        """Resource release endpoint should exist"""
        # Try to release a non-existent resource (should return error, not 404 for endpoint)
        response = requests.post(
            f"{BASE_URL}/api/ledger/resource/release/trainer/nonexistent_trainer",
            headers={"Authorization": f"Bearer {HO_SESSION_TOKEN}"}
        )
        # Should return 400 (resource not found/not locked) not 404 (endpoint not found)
        assert response.status_code in [200, 400], f"Release endpoint should exist. Got {response.status_code}: {response.text}"
        print(f"✓ Resource release endpoint exists")
    
    def test_resource_release_requires_ho_role(self):
        """Resource release should require HO role"""
        response = requests.post(
            f"{BASE_URL}/api/ledger/resource/release/trainer/test_trainer",
            headers={"Authorization": f"Bearer {MANAGER_SESSION_TOKEN}"}
        )
        # Manager should not be able to release resources
        assert response.status_code == 403, f"Manager should not release resources. Got {response.status_code}"
        print(f"✓ Resource release correctly requires HO role")


class TestResourceCalendarIntegration:
    """Integration tests for Resource Calendar with actual data"""
    
    def test_calendar_shows_assigned_resources_with_sdc_info(self):
        """Assigned resources should show SDC assignment info"""
        response = requests.get(
            f"{BASE_URL}/api/ledger/resource/calendar",
            headers={"Authorization": f"Bearer {HO_SESSION_TOKEN}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        resources = data.get("resources", [])
        assigned_resources = [r for r in resources if r.get("status") == "assigned"]
        
        for resource in assigned_resources:
            current_assignment = resource.get("current_assignment")
            if current_assignment:
                assert "sdc_id" in current_assignment or "sdc_name" in current_assignment, \
                    f"Assigned resource should have SDC info: {resource}"
                print(f"✓ Assigned resource {resource.get('name')} has SDC info: {current_assignment.get('sdc_name')}")
        
        if len(assigned_resources) == 0:
            print("⚠ No assigned resources found to verify SDC info")
        else:
            print(f"✓ Found {len(assigned_resources)} assigned resources with SDC info")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
