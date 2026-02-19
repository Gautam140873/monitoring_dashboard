# SkillFlow CRM - Product Requirements Document

## Original Problem Statement
Build a Skill Development CRM & Billing Controller Dashboard with Master Database, Commercial Control, Timeline & Financial Engine, and Role-based security.

## Architecture
```
/app/backend/
├── server.py           # Main entry (533 lines)
├── database.py         # MongoDB connection
├── config.py           # Constants, RBAC
├── models/             # Pydantic models
├── services/           # Business logic (auth, audit, ledger)
└── routers/            # API endpoints (auth, users, master_data, resources, sdcs, dashboard, ledger)

/app/frontend/src/pages/
├── Dashboard.jsx       # Main dashboard with burndown, SDC directory
├── SDCDetail.jsx       # SDC process management
├── ResourceCalendar.jsx # Resource availability view ✅ NEW
├── MasterData.jsx      # Job roles, work orders
└── ...
```

## What's Been Implemented

### Refined RBAC ✅ (Feb 19, 2026) - P2 COMPLETED
- [x] `check_sdc_access()` validates manager assignments before updates
- [x] Managers can only update SDC where `assigned_sdc_id` matches OR `manager_email` matches
- [x] HO/Admin roles have full access to all SDCs
- [x] SDC role can only access their assigned SDC
- [x] Returns 403 with clear message when access denied

### Resource Calendar View ✅ (Feb 19, 2026) - P2 COMPLETED
- [x] **Backend**: `GET /api/ledger/resource/calendar` with grouping and summary
- [x] **Frontend**: New `/resource-calendar` page with:
  - Summary cards (Trainers, Managers, Infrastructure with counts)
  - Tabs for each resource type
  - Resources grouped by status (Available vs Assigned)
  - Pulsing green dot for available, solid amber for assigned
  - Detail dialog with contact info and current assignment
  - Release Resource button for assigned resources
- [x] Dashboard menu link added

### Target Ledger & Resource Locking ✅ (Feb 19, 2026) - P0 COMPLETED
- [x] Target Ledger tracks student allocation, prevents over-allocation
- [x] Resource Locking prevents double-booking
- [x] Burn-down Dashboard with pipeline visualization

### Backend Refactoring ✅ (Feb 19, 2026)
- [x] Modular architecture (server.py 533 lines from 3,997)

### System Reliability ✅
- [x] 4-tier RBAC, Audit Logging, Soft Delete, Error Boundary

## RBAC Permission Matrix
| Role | Read All SDCs | Update Own SDC | Update Any SDC |
|------|---------------|----------------|----------------|
| Admin | ✅ | ✅ | ✅ |
| HO | ✅ | ✅ | ✅ |
| Manager | ✅ | ✅ | ❌ (403) |
| SDC | ❌ (own only) | ✅ | ❌ |

## New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ledger/resource/calendar` | GET | Resource availability with grouping |

## Process Stages
1. Mobilization → 2. Training → 3. OJT → 4. Assessment → 5. Placement

## Prioritized Backlog

### P2 (Nice to Have) - REMAINING
- [ ] Holiday Management UI
- [ ] Gmail integration verification
- [ ] PDF invoice generation
- [ ] WhatsApp/SMS notifications

## Technical Notes
- **API Version**: 3.0.0 (Modular)
- **Preview URL**: https://training-tracker-63.preview.emergentagent.com
- **Test User**: gautam.hinger@gmail.com (role: ho)

## Test Reports
- `/app/test_reports/iteration_14.json` - RBAC & Calendar (14 tests passed)
- `/app/test_reports/iteration_13.json` - Ledger (19 tests passed)

## Files of Reference
- `/app/backend/services/auth.py` - check_sdc_access() for refined RBAC
- `/app/backend/routers/ledger.py` - Resource calendar endpoint
- `/app/frontend/src/pages/ResourceCalendar.jsx` - Calendar UI
- `/app/frontend/src/pages/Dashboard.jsx` - Updated with calendar link
