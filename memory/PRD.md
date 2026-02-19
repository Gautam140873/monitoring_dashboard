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

### Backend (FastAPI + MongoDB) - MODULAR STRUCTURE (Feb 19, 2026)
```
/app/backend/
├── server.py           # Main entry point (533 lines - reduced from 3,997)
├── database.py         # MongoDB connection
├── config.py           # Constants, RBAC, stage definitions
├── models/             # Pydantic data models
│   ├── user.py
│   ├── sdc.py
│   ├── work_order.py
│   ├── master_data.py
│   ├── resources.py
│   └── schemas.py      # Request/Response schemas
├── services/           # Business logic
│   ├── auth.py         # Authentication & RBAC
│   ├── audit.py        # Audit logging
│   ├── soft_delete.py  # Soft delete & recovery
│   └── utils.py        # Date calculations, helpers
└── routers/            # API endpoints
    ├── auth.py         # /api/auth/*
    ├── users.py        # /api/users/*
    ├── master_data.py  # /api/master/*
    ├── resources.py    # /api/resources/*
    ├── sdcs.py         # /api/sdcs/*
    └── dashboard.py    # /api/dashboard/*
```

### Frontend (React + TailwindCSS + Shadcn/UI)
- **Pages**: Landing, Dashboard, SDC Detail, Financial Control, Settings, Master Data
- **Design**: Swiss/High-Contrast style with Chivo + Inter fonts

## What's Been Implemented

### Backend Refactoring ✅ (Feb 19, 2026) - P0 COMPLETED
- [x] **Modular Architecture**: server.py reduced from 3,997 to 533 lines (86% reduction)
- [x] **Separated Models**: 6 model files with Pydantic schemas
- [x] **Service Layer**: Auth, audit, soft delete, and utility services
- [x] **Route Modules**: 6 router files for clean API organization
- [x] **All Tests Passing**: 34 API endpoint tests verified
- [x] **API Version**: 3.0.0 (Modular)

### System Reliability Upgrades ✅ (Feb 18, 2026)
- [x] **Enhanced RBAC**: 4-tier role system (Admin → HO → Manager → SDC) with permission matrix
- [x] **Audit Logging**: Complete audit trail for all CRUD operations with old/new value tracking
- [x] **Soft Delete System**: 30-day recovery window for accidentally deleted records
- [x] **Database Indexes**: Auto-created on startup for optimized query performance
- [x] **Error Boundary**: React error boundary with retry mechanism for graceful error handling

### Core Features ✅
- [x] Google OAuth authentication with role-based access
- [x] Dashboard Overview with 5 financial metrics (Portfolio, Billed, Collected, Outstanding, Variance)
- [x] 7-stage Training Roadmap Progress visualization
- [x] SDC cards with progress, blockers, and overdue indicators
- [x] Work Order creation (auto-creates SDC and training roadmap)
- [x] Start Date setting with auto End Date calculation
- [x] Invoice creation with variance tracking (alerts if >10%)
- [x] Payment recording with PAID trigger for completed stages
- [x] User role management (HO/SDC assignment)
- [x] Holiday management (global + local holidays)
- [x] Alert generation for overdue work orders and high variance

### Master Data System ✅ (Feb 18, 2026)
- [x] Job Role Master with category-based rates (Cat A: ₹46/hr, Cat B: ₹42/hr)
- [x] Master Work Orders with multiple job roles and SDC districts
- [x] SDC creation from Master Work Order with auto-calculated contract values
- [x] Resource Masters (Trainers, Managers, Infrastructure)
- [x] Resource Assignment and Release on Work Order completion

## RBAC Permission System
| Role | Level | Permissions |
|------|-------|-------------|
| Admin | 100 | Full system access, all permissions |
| HO | 80 | SDCs, Work Orders, Resources, Master Data, Reports, Settings, Audit Read, Restore Deleted |
| Manager | 50 | Read/Update SDCs, Work Orders, Resources, Reports (team level) |
| SDC | 20 | Read/Update own SDC only, Read-only for resources and master data |

## Process Stages (5-Stage Pipeline)
1. **Mobilization** - Student registration and enrollment
2. **Training** - Classroom training phase (depends on Mobilization)
3. **OJT** - On-the-Job Training (depends on Training)
4. **Assessment** - Evaluation and certification (depends on OJT)
5. **Placement** - Job placement (depends on Assessment)

## Prioritized Backlog

### P0 (Critical) - IN PROGRESS
- [ ] **Target Ledger System**: Track student allocation from Work Orders to SDCs, prevent over-allocation
- [ ] **Resource Locking**: Check availability to prevent double-booking of Trainers/Managers

### P1 (High Priority) - UPCOMING
- [ ] **Sequential Workflow Engine**: Enforce strict stage completion (Training ≤ Mobilization)
- [ ] **Burn-down Dashboard**: Visualize Work Order progress (Unallocated → In-Training → Placed)
- [ ] **Refined RBAC**: Center Managers can only edit their assigned SDC

### P2 (Nice to Have)
- [ ] Holiday Management UI in Settings
- [ ] End-to-end Gmail verification
- [ ] WhatsApp/SMS notifications
- [ ] PDF invoice generation

## Technical Notes
- **Backend API Version**: 3.0.0 (Modular)
- **MongoDB Collections**: users, user_sessions, sdcs, work_orders, training_roadmaps, invoices, holidays, alerts, job_role_master, master_work_orders, trainers, center_managers, sdc_infrastructure, audit_logs, sdc_processes
- **Preview URL**: https://training-tracker-63.preview.emergentagent.com
- **Test User**: gautam.hinger@gmail.com (role: ho)

## Files of Reference
- `/app/backend/server.py` - Main entry point (modular)
- `/app/backend/routers/*.py` - API route handlers
- `/app/backend/models/*.py` - Pydantic models
- `/app/backend/services/*.py` - Business logic
- `/app/frontend/src/pages/MasterData.jsx` - Master Data UI
- `/app/frontend/src/pages/SDCDetail.jsx` - SDC process view

## Next Action Items
1. 🔴 **P0**: Implement Target Ledger for allocation tracking
2. 🔴 **P0**: Add Resource Locking to prevent double-booking
3. 🟡 **P1**: Build Burn-down Dashboard visualization
4. 🟡 **P1**: Enforce sequential stage validation in backend
5. 🟡 **P1**: Tighten RBAC for Center Managers
