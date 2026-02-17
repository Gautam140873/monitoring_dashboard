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

### Training Roadmap Stages
1. Mobilization (Finding students)
2. Dress Distribution
3. Study Material Distribution
4. Classroom Training
5. Assessment
6. OJT (On-the-Job Training)
7. Placement

## Prioritized Backlog

### P0 (Critical - Next Sprint)
- [ ] Gmail API integration for HO Risk Summary emails
- [ ] CSV/Excel export for reports
- [ ] Batch progress update UI

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

## Technical Notes
- Backend API version: 2.0.0
- MongoDB collections: users, user_sessions, sdcs, work_orders, training_roadmaps, invoices, holidays, alerts
- All backend routes prefixed with /api
- Session token stored in httpOnly cookie

## Next Action Items
1. Implement Gmail API for automated Risk Summary emails to HO
2. Add batch progress update UI in SDC Detail page
3. Export functionality for financial reports
