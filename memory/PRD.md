# SkillFlow CRM - Product Requirements Document

## Original Problem Statement
Build a Skill Development CRM & Billing Controller Dashboard to manage and monitor skill development projects with:
- Google Sheets-like data management for Master Database and Commercial Control
- Timeline & Financial Engine with holiday-aware date calculations
- Web Dashboard with Commercial Health view and SDC Progress tracking
- HO Notification System for Risk Alerts
- Role-based security (SDC vs HO access)

## User Personas
1. **Admin** - Full system access, can manage all settings, users, and recover deleted items
2. **Head Office (HO)** - Full operational access to all SDCs, work orders, resources, and reports
3. **Manager** - Team lead access, can view and update team data
4. **SDC User** - Limited access to assigned center only

## Architecture

### Backend (FastAPI + MongoDB) - MODULAR STRUCTURE
```
/app/backend/
├── server.py           # Main entry point (533 lines)
├── database.py         # MongoDB connection
├── config.py           # Constants, RBAC, stage definitions
├── models/             # Pydantic data models
├── services/           # Business logic
│   ├── auth.py         # Authentication & RBAC
│   ├── audit.py        # Audit logging
│   ├── soft_delete.py  # Soft delete & recovery
│   ├── utils.py        # Date calculations, helpers
│   └── ledger.py       # Target Ledger, Resource Locking, Burndown ✅ NEW
└── routers/            # API endpoints
    ├── auth.py         # /api/auth/*
    ├── users.py        # /api/users/*
    ├── master_data.py  # /api/master/*
    ├── resources.py    # /api/resources/*
    ├── sdcs.py         # /api/sdcs/*
    ├── dashboard.py    # /api/dashboard/*
    └── ledger.py       # /api/ledger/* ✅ NEW
```

### Frontend (React + TailwindCSS + Shadcn/UI)
- **Pages**: Landing, Dashboard, SDC Detail, Financial Control, Settings, Master Data
- **Design**: Swiss/High-Contrast style with Chivo + Inter fonts

## What's Been Implemented

### Target Ledger & Resource Locking ✅ (Feb 19, 2026) - P0 COMPLETED
- [x] **Target Ledger System**: Tracks student allocation from Work Orders to SDCs
  - `GET /api/ledger/target/{master_wo_id}` - Get allocation by job role
  - `POST /api/ledger/validate-allocation` - Validate before creating SDC
  - Over-allocation prevention with detailed error messages
- [x] **Resource Locking**: Prevents double-booking of Trainers/Managers/Infrastructure
  - `GET /api/ledger/resource/check/{type}/{id}` - Check availability
  - `POST /api/ledger/resource/lock` - Lock resource (returns 409 if conflict)
  - `POST /api/ledger/resource/release/{type}/{id}` - Release locked resource
  - `GET /api/ledger/resource/summary` - Resource counts
- [x] **SDC Creation Integration**: Validation + locking applied automatically

### Burn-down Dashboard ✅ (Feb 19, 2026) - P1 COMPLETED
- [x] **Backend API**: `GET /api/ledger/burndown` with pipeline data
- [x] **Frontend Component**: BurndownDashboard with:
  - Pipeline bar visualization (Unallocated → Allocated → Mobilized → In Training → Placed)
  - Work Order selector dropdown
  - Summary stats cards
  - Progress indicator

### Dashboard Redesign ✅ (Feb 19, 2026)
- [x] **SDC Status Metrics**: Total Registered, Active/Available, Engaged/Busy, Inactive
- [x] **Collapsible SDC Directory**: Accordion-style grouped by status
  - Search and filter functionality
  - Status dots (pulsing green for available, amber for engaged)
  - Expand to see details, progress, financial summary
  - Assign button disabled for non-available SDCs
- [x] **Process Stages & Deliverables**: Separated into side-by-side cards

### Backend Refactoring ✅ (Feb 19, 2026)
- [x] **Modular Architecture**: server.py reduced from 3,997 to 533 lines
- [x] **Separated Models**: 6 model files with Pydantic schemas
- [x] **Service Layer**: Auth, audit, soft delete, utility, ledger services
- [x] **Route Modules**: 7 router files for clean API organization

### System Reliability Upgrades ✅ (Feb 18, 2026)
- [x] **Enhanced RBAC**: 4-tier role system (Admin → HO → Manager → SDC)
- [x] **Audit Logging**: Complete audit trail for all CRUD operations
- [x] **Soft Delete System**: 30-day recovery window
- [x] **Database Indexes**: Auto-created on startup
- [x] **Error Boundary**: React error boundary with retry mechanism

### Core Features ✅
- [x] Google OAuth authentication with role-based access
- [x] Dashboard Overview with 5 financial metrics
- [x] 5-stage Training Roadmap Progress visualization
- [x] Work Order creation with auto SDC and training roadmap
- [x] Invoice creation with variance tracking
- [x] Payment recording with PAID trigger
- [x] User role management
- [x] Holiday management (global + local)
- [x] Alert generation

## Process Stages (5-Stage Pipeline)
1. **Mobilization** - Student registration and enrollment
2. **Training** - Classroom training phase
3. **OJT** - On-the-Job Training
4. **Assessment** - Evaluation and certification
5. **Placement** - Job placement

## Prioritized Backlog

### P2 (Nice to Have) - UPCOMING
- [ ] Refined RBAC: Center Managers can only edit their assigned SDC
- [ ] Holiday Management UI in Settings
- [ ] End-to-end Gmail verification
- [ ] WhatsApp/SMS notifications
- [ ] PDF invoice generation

## New API Endpoints (Ledger)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ledger/target/{mwo_id}` | GET | Get target allocation ledger |
| `/api/ledger/validate-allocation` | POST | Validate allocation request |
| `/api/ledger/all-ledgers` | GET | Get all active ledgers |
| `/api/ledger/resource/check/{type}/{id}` | GET | Check resource availability |
| `/api/ledger/resource/lock` | POST | Lock a resource |
| `/api/ledger/resource/release/{type}/{id}` | POST | Release a resource |
| `/api/ledger/resource/summary` | GET | Get resource counts |
| `/api/ledger/resource/history/{type}/{id}` | GET | Get booking history |
| `/api/ledger/burndown` | GET | Get burn-down dashboard data |
| `/api/ledger/burndown/{mwo_id}` | GET | Get burn-down for specific WO |

## Technical Notes
- **Backend API Version**: 3.0.0 (Modular)
- **MongoDB Collections**: users, user_sessions, sdcs, work_orders, training_roadmaps, invoices, holidays, alerts, job_role_master, master_work_orders, trainers, center_managers, sdc_infrastructure, audit_logs, sdc_processes, target_ledger, resource_bookings
- **Preview URL**: https://training-tracker-63.preview.emergentagent.com
- **Test User**: gautam.hinger@gmail.com (role: ho)

## Files of Reference
- `/app/backend/services/ledger.py` - Target Ledger, Resource Locking, Burndown logic
- `/app/backend/routers/ledger.py` - Ledger API endpoints
- `/app/backend/routers/master_data.py` - Updated with allocation validation
- `/app/frontend/src/pages/Dashboard.jsx` - Updated with BurndownDashboard, SDCDirectory

## Test Reports
- `/app/test_reports/iteration_13.json` - All 19 ledger tests passed
- `/app/backend/tests/test_ledger_features.py` - Ledger test suite

## Next Action Items
1. 🟢 **P2**: Refined RBAC for Center Managers
2. 🟢 **P2**: Holiday Management UI
3. 🟢 **P2**: Gmail integration verification
4. 🟢 **P2**: PDF invoice generation
