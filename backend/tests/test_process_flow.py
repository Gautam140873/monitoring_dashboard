"""
Test Process Flow Feature - SDC Process Status APIs
Tests the new sequential process stages (Mobilization → Training → OJT → Assessment → Placement)
and deliverables (Dress, Study Material, ID Card, Toolkit) functionality.
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test session token - will be set by fixture
SESSION_TOKEN = None


@pytest.fixture(scope="module")
def auth_session():
    """Create authenticated session for testing"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ.get('TEST_SESSION_TOKEN', 'test_session_process_1771485525040')}"
    })
    return session


@pytest.fixture(scope="module")
def test_sdc_id():
    """Return a test SDC ID"""
    return "sdc_jaipur"


class TestProcessStatusGet:
    """Test GET /api/sdcs/{id}/process-status endpoint"""
    
    def test_get_process_status_returns_200(self, auth_session, test_sdc_id):
        """Test that process status endpoint returns 200"""
        response = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_process_status_has_required_fields(self, auth_session, test_sdc_id):
        """Test that response contains all required fields"""
        response = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        data = response.json()
        
        # Check top-level fields
        assert "sdc_id" in data
        assert "sdc_name" in data
        assert "target_students" in data
        assert "overall_progress" in data
        assert "stages" in data
        assert "deliverables" in data
        assert "process_definitions" in data
    
    def test_process_status_has_5_stages(self, auth_session, test_sdc_id):
        """Test that there are exactly 5 process stages"""
        response = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        data = response.json()
        
        assert len(data["stages"]) == 5
        stage_ids = [s["stage_id"] for s in data["stages"]]
        assert stage_ids == ["mobilization", "training", "ojt", "assessment", "placement"]
    
    def test_stages_in_sequential_order(self, auth_session, test_sdc_id):
        """Test that stages are in correct sequential order"""
        response = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        data = response.json()
        
        expected_order = [
            ("mobilization", 1),
            ("training", 2),
            ("ojt", 3),
            ("assessment", 4),
            ("placement", 5)
        ]
        
        for i, (stage_id, order) in enumerate(expected_order):
            assert data["stages"][i]["stage_id"] == stage_id
            assert data["stages"][i]["order"] == order
    
    def test_process_status_has_4_deliverables(self, auth_session, test_sdc_id):
        """Test that there are exactly 4 deliverables"""
        response = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        data = response.json()
        
        assert len(data["deliverables"]) == 4
        deliverable_ids = [d["deliverable_id"] for d in data["deliverables"]]
        assert "dress_distribution" in deliverable_ids
        assert "study_material" in deliverable_ids
        assert "id_card" in deliverable_ids
        assert "toolkit" in deliverable_ids
    
    def test_stage_has_progress_fields(self, auth_session, test_sdc_id):
        """Test that each stage has progress tracking fields"""
        response = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        data = response.json()
        
        for stage in data["stages"]:
            assert "target" in stage
            assert "completed" in stage
            assert "progress_percent" in stage
            assert "status" in stage
            assert "can_start" in stage
    
    def test_first_stage_can_always_start(self, auth_session, test_sdc_id):
        """Test that first stage (mobilization) can always start"""
        response = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        data = response.json()
        
        mobilization = data["stages"][0]
        assert mobilization["stage_id"] == "mobilization"
        assert mobilization["can_start"] == True


class TestProcessStageUpdate:
    """Test PUT /api/sdcs/{id}/process-status/stage/{stage_id} endpoint"""
    
    def test_update_stage_completed_count(self, auth_session, test_sdc_id):
        """Test updating stage completed count"""
        response = auth_session.put(
            f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status/stage/mobilization?completed=45"
        )
        assert response.status_code == 200
        assert "updated successfully" in response.json()["message"]
        
        # Verify update
        verify = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        data = verify.json()
        mobilization = next(s for s in data["stages"] if s["stage_id"] == "mobilization")
        assert mobilization["completed"] == 45
    
    def test_update_stage_auto_sets_status(self, auth_session, test_sdc_id):
        """Test that updating completed count auto-sets status"""
        # Set to partial completion
        auth_session.put(
            f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status/stage/mobilization?completed=30"
        )
        
        verify = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        data = verify.json()
        mobilization = next(s for s in data["stages"] if s["stage_id"] == "mobilization")
        assert mobilization["status"] == "in_progress"
    
    def test_mark_stage_complete_100_percent(self, auth_session, test_sdc_id):
        """Test marking stage as 100% complete"""
        # Get target
        verify = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        target = verify.json()["target_students"]
        
        # Mark complete
        response = auth_session.put(
            f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status/stage/mobilization?completed={target}"
        )
        assert response.status_code == 200
        
        # Verify status is completed
        verify = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        data = verify.json()
        mobilization = next(s for s in data["stages"] if s["stage_id"] == "mobilization")
        assert mobilization["status"] == "completed"
        assert mobilization["progress_percent"] == 100.0
    
    def test_next_stage_unlocks_when_previous_starts(self, auth_session, test_sdc_id):
        """Test that next stage unlocks when previous stage is in_progress"""
        # Set mobilization to in_progress
        auth_session.put(
            f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status/stage/mobilization?completed=30"
        )
        
        verify = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        data = verify.json()
        
        training = next(s for s in data["stages"] if s["stage_id"] == "training")
        assert training["can_start"] == True, "Training should be unlocked when mobilization is in_progress"
    
    def test_invalid_stage_id_returns_400(self, auth_session, test_sdc_id):
        """Test that invalid stage_id returns 400"""
        response = auth_session.put(
            f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status/stage/invalid_stage?completed=10"
        )
        assert response.status_code == 400
        assert "Invalid stage_id" in response.json()["detail"]


class TestDeliverableUpdate:
    """Test PUT /api/sdcs/{id}/process-status/deliverable/{deliverable_id} endpoint"""
    
    def test_update_deliverable_to_completed(self, auth_session, test_sdc_id):
        """Test updating deliverable status to completed"""
        response = auth_session.put(
            f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status/deliverable/study_material?status=completed"
        )
        assert response.status_code == 200
        assert "updated to completed" in response.json()["message"]
        
        # Verify
        verify = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        data = verify.json()
        study_material = next(d for d in data["deliverables"] if d["deliverable_id"] == "study_material")
        assert study_material["status"] == "completed"
        assert study_material["completed_date"] is not None
    
    def test_update_deliverable_to_not_required(self, auth_session, test_sdc_id):
        """Test updating deliverable status to not_required"""
        response = auth_session.put(
            f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status/deliverable/id_card?status=not_required"
        )
        assert response.status_code == 200
        
        # Verify
        verify = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        data = verify.json()
        id_card = next(d for d in data["deliverables"] if d["deliverable_id"] == "id_card")
        assert id_card["status"] == "not_required"
    
    def test_update_deliverable_to_pending(self, auth_session, test_sdc_id):
        """Test updating deliverable status back to pending"""
        response = auth_session.put(
            f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status/deliverable/id_card?status=pending"
        )
        assert response.status_code == 200
        
        # Verify
        verify = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        data = verify.json()
        id_card = next(d for d in data["deliverables"] if d["deliverable_id"] == "id_card")
        assert id_card["status"] == "pending"
    
    def test_invalid_deliverable_id_returns_400(self, auth_session, test_sdc_id):
        """Test that invalid deliverable_id returns 400"""
        response = auth_session.put(
            f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status/deliverable/invalid_deliv?status=completed"
        )
        assert response.status_code == 400
        assert "Invalid deliverable_id" in response.json()["detail"]
    
    def test_invalid_status_returns_400(self, auth_session, test_sdc_id):
        """Test that invalid status returns 400"""
        response = auth_session.put(
            f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status/deliverable/dress_distribution?status=invalid"
        )
        assert response.status_code == 400
        assert "Status must be" in response.json()["detail"]


class TestOverallProgress:
    """Test overall progress calculation"""
    
    def test_overall_progress_calculation(self, auth_session, test_sdc_id):
        """Test that overall progress is calculated correctly"""
        # Reset all stages to 0
        for stage_id in ["mobilization", "training", "ojt", "assessment", "placement"]:
            auth_session.put(
                f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status/stage/{stage_id}?completed=0"
            )
        
        # Get initial progress
        verify = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        data = verify.json()
        assert data["overall_progress"] == 0.0
        
        # Complete mobilization (1/5 stages = 20%)
        target = data["target_students"]
        auth_session.put(
            f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status/stage/mobilization?completed={target}"
        )
        
        verify = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        data = verify.json()
        assert data["overall_progress"] == 20.0, f"Expected 20.0%, got {data['overall_progress']}%"


class TestProcessFlowIntegration:
    """Integration tests for the complete process flow"""
    
    def test_complete_process_flow(self, auth_session, test_sdc_id):
        """Test completing the entire process flow"""
        # Get target
        verify = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        target = verify.json()["target_students"]
        
        # Complete all stages sequentially
        stages = ["mobilization", "training", "ojt", "assessment", "placement"]
        
        for i, stage_id in enumerate(stages):
            # Update stage
            response = auth_session.put(
                f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status/stage/{stage_id}?completed={target}"
            )
            assert response.status_code == 200
            
            # Verify stage is completed
            verify = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
            data = verify.json()
            stage = next(s for s in data["stages"] if s["stage_id"] == stage_id)
            assert stage["status"] == "completed"
            
            # Verify next stage can start (if not last)
            if i < len(stages) - 1:
                next_stage = next(s for s in data["stages"] if s["stage_id"] == stages[i + 1])
                assert next_stage["can_start"] == True
        
        # Verify 100% overall progress
        verify = auth_session.get(f"{BASE_URL}/api/sdcs/{test_sdc_id}/process-status")
        data = verify.json()
        assert data["overall_progress"] == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
