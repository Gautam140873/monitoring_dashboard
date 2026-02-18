# SkillFlow CRM - Product Requirements Document

## Original Problem Statement
Build a Skill Development CRM & Billing Controller Dashboard to manage and monitor skill development projects with:
- Google Sheets-like data management for Master Database and Commercial Control
- Timeline & Financial Engine with holiday-aware date calculations
- Web Dashboard with Commercial Health view and SDC Progress tracking
- HO Notification System for Risk Alerts
- Role-based security (SDC vs HO access)

## User Personas
1. **Head Office (HO) Admin** - Full access to all SDCs, can create work orders, manage users, view financial control
2. **SDC Manager** - Limited access to assigned center only, can set start dates, update progress, view billing

## Architecture

### Backend (FastAPI + MongoDB)
- **Authentication**: Emergent Google OAuth with session-based auth
- **Data Models**: Users, SDCs, WorkOrders, TrainingRoadmaps, Invoices, Holidays, Alerts, ResourceMasters
- **Core Features**:
  - Auto-SDC creation when new location is added via Work Order
  - 7-stage Training Roadmap (Mobilization → Placement)
  - Holiday-aware end date calculation (skips Sundays + holidays)
  - Variance tracking (Order vs Billed)
  - Payment Trigger (marks stages as PAID when invoice is fully paid)
  - Resource availability tracking and auto-release

### Frontend (React + TailwindCSS + Shadcn/UI)
- **Pages**: Landing, Dashboard, SDC Detail, Financial Control, Settings, Master Data
- **Design**: Swiss/High-Contrast style with Chivo + Inter fonts

## What's Been Implemented (Feb 2026)

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

### New Features (Phase 2) ✅
- [x] Batch Progress Update UI - Update multiple roadmap stages at once
- [x] CSV Export functionality (Financial Summary, Work Orders, Training Progress, Invoices)

### New Features (Phase 3) ✅
- [x] Gmail API Integration for Risk Summary emails

### Master Data System ✅ (Feb 18, 2026)
- [x] Job Role Master with category-based rates (Cat A: ₹46/hr, Cat B: ₹42/hr)
- [x] Master Work Orders with multiple job roles and SDC districts
- [x] SDC creation from Master Work Order with auto-calculated contract values
- [x] SDC naming convention: SDC_DISTRICT or SDC_DISTRICT1, SDC_DISTRICT2

### Resource Masters ✅ (Feb 18, 2026)
- [x] **Trainers Master**: Name, Email, Qualification, Specialization, Status tracking
- [x] **Center Managers Master**: Name, Email, Phone, Status tracking
- [x] **SDC Infrastructure Master**: Center details, Address, Capacity, Facilities, Status tracking
- [x] **Resource Selection in SDC Creation**: Dropdown to select available infrastructure and managers
- [x] **Address Auto-fill**: When infrastructure is selected, address fields auto-populate
- [x] **Resource Assignment**: Resources marked as `in_use` / `assigned` when SDC is created
- [x] **Resource Release**: "Complete & Release Resources" button releases all assigned resources
- [x] **Dialog Auto-close Fix**: Dialogs no longer close when clicking outside

### New API Endpoints (Feb 18, 2026)
- `POST /api/master/work-orders/{id}/complete` - Complete work order and release all resources
- `POST /api/resources/trainers/{id}/assign` - Assign trainer to SDC
- `POST /api/resources/managers/{id}/assign` - Assign manager to SDC  
- `POST /api/resources/infrastructure/{id}/assign` - Assign center to work order
- `POST /api/resources/*/release` - Release resources (mark as available)
- `GET /api/resources/summary` - Overview with available/assigned counts

### Data Flow
```
JOB ROLE MASTER (Define rates & hours)
    ↓ Select multiple job roles
MASTER WORK ORDER (Define targets & districts)
    ↓ Create SDCs (select resources from Resource Masters)
SDC (With assigned resources)
    ↓ Training complete
WORK ORDER COMPLETION (Auto-release all resources)
```

## Training Roadmap Stages
1. Mobilization (Finding students)
2. Dress Distribution
3. Study Material Distribution
4. Classroom Training
5. Assessment
6. OJT (On-the-Job Training)
7. Placement

## Prioritized Backlog

### P0 (Critical) - COMPLETED ✅
- [x] SDC Form Integration with Resource Masters
- [x] Resource Availability and Locking Logic
- [x] Dialog auto-close fix

### P1 (High Priority)
- [ ] Trainer dropdown in SDC form (same pattern as Manager)
- [ ] Holiday Management CRUD UI in Settings
- [ ] Gmail API end-to-end verification
- [ ] PDF invoice generation

### P2 (Nice to Have)
- [ ] WhatsApp/SMS notifications for SDC managers
- [ ] Audit log for all changes
- [ ] Real-time dashboard updates (WebSocket)
- [ ] Mobile-responsive improvements
- [ ] Dark mode toggle

## Technical Notes
- Backend API version: 2.1.0
- MongoDB collections: users, user_sessions, sdcs, work_orders, training_roadmaps, invoices, holidays, alerts, job_role_master, master_work_orders, trainers, center_managers, sdc_infrastructure
- All backend routes prefixed with /api
- Session token stored in httpOnly cookie

## Sample Data
- **Job Roles (11 total)**:
  | Code | Name | Category | Rate | Hours |
  |------|------|----------|------|-------|
  | CSC/Q0801 | Field Technician Computing | Cat A | ₹46/hr | 400 |
  | ELE/Q4601 | Solar Panel Installation | Cat B | ₹42/hr | 300 |
  | THC/Q0301 | Front Office Executive | Cat A | ₹46/hr | 300 |
  | HWC/Q0101 | General Duty Assistant | Cat B | ₹42/hr | 400 |
  | RSC/Q0201 | Retail Sales Associate | Cat A | ₹46/hr | 280 |
  | AUT/Q0102 | Automotive Service Technician | Cat B | ₹42/hr | 500 |
  | BWS/Q0101 | Beauty Therapist | Cat A | ₹46/hr | 350 |
  | HSS/Q5801 | Wellness Therapist (Elderly) | Cat A | ₹45/hr | 700 |
  | BSC/Q0901 | BFSI Customer Care Executive | Cat B | ₹42/hr | 500 |
  | RAC/Q0101 | Field Technician AC | Cat A | ₹48/hr | 600 |
  | ELE/Q3101 | Assistant Electrician | Cat B | ₹38/hr | 520 |

- **Master Work Orders (10 total)**:
  | WO Number | Scheme | State | Target | SDCs | Value |
  |-----------|--------|-------|--------|------|-------|
  | WO-SD-001 | PM-DAKSH | Rajasthan | 300 | 3 | ₹31,50,000 |
  | WO-SD-002 | MMYKY | Rajasthan | 250 | 2 | ₹14,40,000 |
  | WO-SD-003 | PMKVY | Gujarat | 400 | 4 | ₹25,20,000 |
  | WO-SD-004 | CSR Skill Program | Maharashtra | 150 | 2 | ₹17,28,000 |
  | WO-SD-005 | Rural Skill Dev | MP | 200 | 3 | ₹13,83,200 |
  
- **Resources**: 2 Trainers, 2 Managers, 2 SDC Centers (all available)

## Files of Reference
- `/app/backend/server.py` - Main backend with all API endpoints
- `/app/frontend/src/pages/MasterData.jsx` - Master Data management UI
- `/app/frontend/src/pages/Dashboard.jsx` - Main dashboard
- `/app/frontend/src/App.js` - App routes

## Next Action Items
1. 🟡 **P1**: Add Trainer selection dropdown to SDC creation form
2. 🟡 **P1**: Holiday Management CRUD UI in Settings page
3. 🟡 **P1**: Test Gmail API end-to-end flow
4. 🟢 **P2**: Refactor large files (server.py, MasterData.jsx) into modules
