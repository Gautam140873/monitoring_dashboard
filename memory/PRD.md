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
- **Data Models**: Users, SDCs, WorkOrders, TrainingRoadmaps, Invoices, Holidays, Alerts
- **Core Features**:
  - Auto-SDC creation when new location is added via Work Order
  - 7-stage Training Roadmap (Mobilization → Placement)
  - Holiday-aware end date calculation (skips Sundays + holidays)
  - Variance tracking (Order vs Billed)
  - Payment Trigger (marks stages as PAID when invoice is fully paid)

### Frontend (React + TailwindCSS + Shadcn/UI)
- **Pages**: Landing, Dashboard, SDC Detail, Financial Control, Settings, User Management
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
- [x] CSV Export functionality:
  - Financial Summary export
  - Work Orders export  
  - Training Progress export
  - Invoices export

### New Features (Phase 3) ✅
- [x] Gmail API Integration for Risk Summary emails
  - OAuth2 flow for Gmail authorization
  - HTML formatted Risk Summary emails
  - Commercial Health metrics in email
  - All active alerts included
  - Email sending history log

### Training Roadmap Stages
1. Mobilization (Finding students)
2. Dress Distribution
3. Study Material Distribution
4. Classroom Training
5. Assessment
6. OJT (On-the-Job Training)
7. Placement

## Prioritized Backlog

### P0 (Critical) - COMPLETED ✅
- [x] Gmail API integration for HO Risk Summary emails

### P1 (High Priority)
- [ ] Google Sheets bi-directional sync (if needed)
- [ ] Real-time dashboard updates (WebSocket)
- [ ] PDF invoice generation
- [ ] Audit log for all changes

### P2 (Nice to Have)
- [ ] Mobile-responsive improvements
- [ ] Dark mode toggle
- [ ] Advanced filtering and search
- [ ] Historical trend charts
- [ ] Multi-language support
- [ ] WhatsApp/SMS notifications for local managers

## Technical Notes
- Backend API version: 2.0.0
- MongoDB collections: users, user_sessions, sdcs, work_orders, training_roadmaps, invoices, holidays, alerts
- All backend routes prefixed with /api
- Session token stored in httpOnly cookie

## Recent Changes (Feb 17, 2026)

### Bug Fixes ✅
- [x] Fixed SDC detail page 403 error - User `gautam.hinger@gmail.com` was changed from 'sdc' role to 'ho' role
- [x] Added "New Work Order" form dialog to Dashboard page

### New Features ✅
- [x] New Work Order form on Dashboard with auto-SDC creation
- [x] Form includes: Work Order Number, Location, Job Role, Scheme, Training Hours, Students, Cost per Student
- [x] Auto-calculated contract value display
- [x] Success toast and dashboard refresh after creation

---

## 🚧 PLANNED: Master Data Enhancement (Pending - To Resume)

### New Tiered Structure
```
WORK ORDER (Umbrella)
├── Job Role Category: Cat A (₹46/hr) | Cat B (₹42/hr) | Custom
├── Rate Per Hour: Auto-populated or manual override
├── Total Course Duration: e.g., 400 hours
│
├── SDC 1 (Linked to Work Order)
│   ├── Target Allocation: Total candidates for center
│   ├── Batch 1: 30 students, 8hr/day → End Date, Batch Value
│   ├── Batch 2: 30 students, 6hr/day → End Date, Batch Value
│   └── SDC Total = Sum of Batch Values
│
└── WORK ORDER TOTAL = Sum of all SDC Values
```

### Financial Calculation Logic
- **Batch Value** = Candidates × Course Duration × Rate Per Hour
- **SDC Total** = Sum of all Batch Values within SDC
- **Work Order Total** = Sum of all SDC Values

### Job Role Category Rates
| Category | Rate Per Hour |
|----------|---------------|
| Cat A / Cat 1 | ₹46/hr |
| Cat B / Cat 2 | ₹42/hr |
| Custom | Manual entry |

### New Data Fields Required
| Feature | Controlled At | Input Type | Impact |
|---------|--------------|------------|--------|
| Rate Per Hour | Work Order | Dropdown (Cat A/B) | Financial multiplier |
| Total Duration | Work Order | Manual | Timeline baseline |
| Target Allocation | SDC Level | Manual | Center student count |
| Daily Hours | Batch Level | Dropdown (4,6,8) | End Date calculation |
| Student Count | Batch Level | Manual (25-30) | Batch Value calculation |

### Implementation Phases (To Do)
- **Phase 1**: Backend schema updates (new Batch model, Work Order fields)
- **Phase 2**: API endpoints for SDC/Batch management under Work Orders
- **Phase 3**: Frontend forms and financial summary dashboard

### Open Questions for Next Session
1. Migration strategy for existing 7 work orders?
2. Should 7-stage roadmap be tracked at Batch level?

---

## Next Action Items
1. 🔴 **P0**: Implement Master Data Enhancement (structure above)
2. 🟡 **P1**: Verify Gmail API end-to-end flow
3. 🟢 **P2**: Holiday Management CRUD UI in Settings
