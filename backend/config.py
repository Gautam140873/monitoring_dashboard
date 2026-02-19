"""
Configuration and constants for SkillFlow CRM
"""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Google OAuth config
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Category rate mapping for Job Roles
CATEGORY_RATES = {
    "A": 46.0,
    "B": 42.0
}

# RBAC Permissions System
ROLES = {
    "admin": {
        "description": "Full system access",
        "level": 100,
        "permissions": ["*"]
    },
    "ho": {
        "description": "Head Office - Full operational access",
        "level": 80,
        "permissions": [
            "sdcs:*", "work_orders:*", "resources:*", "master_data:*",
            "users:read", "users:update_role", "reports:*", "settings:*",
            "audit:read", "deleted:restore"
        ]
    },
    "manager": {
        "description": "Manager - Team lead access",
        "level": 50,
        "permissions": [
            "sdcs:read", "sdcs:update", "work_orders:read", "work_orders:update",
            "resources:read", "master_data:read", "reports:read",
            "team:read", "team:update"
        ]
    },
    "sdc": {
        "description": "SDC User - Limited to assigned center",
        "level": 20,
        "permissions": [
            "sdcs:read:own", "sdcs:update:own", "work_orders:read:own",
            "resources:read", "master_data:read"
        ]
    }
}

# Process Stages (Sequential & Target-bound)
PROCESS_STAGES = [
    {"stage_id": "mobilization", "name": "Mobilization", "order": 1, "description": "Student registration and enrollment", "icon": "Users"},
    {"stage_id": "training", "name": "Training", "order": 2, "description": "Classroom training phase", "icon": "GraduationCap", "depends_on": "mobilization"},
    {"stage_id": "ojt", "name": "OJT", "order": 3, "description": "On-the-Job Training", "icon": "Briefcase", "depends_on": "training"},
    {"stage_id": "assessment", "name": "Assessment", "order": 4, "description": "Evaluation and certification", "icon": "ClipboardCheck", "depends_on": "ojt"},
    {"stage_id": "placement", "name": "Placement", "order": 5, "description": "Job placement", "icon": "Award", "depends_on": "assessment"}
]

# Deliverables (Yes/No/Not Required)
DELIVERABLES = [
    {"deliverable_id": "dress_distribution", "name": "Dress Distribution", "description": "Uniform/dress code"},
    {"deliverable_id": "study_material", "name": "Study Material", "description": "Books and learning materials"},
    {"deliverable_id": "id_card", "name": "ID Card", "description": "Student ID cards"},
    {"deliverable_id": "toolkit", "name": "Tool Kit", "description": "Trade-specific tools"}
]

# Training Stages (for backward compatibility)
TRAINING_STAGES = [
    {"stage_id": "mobilization", "name": "Mobilization", "order": 1, "description": "Finding students"},
    {"stage_id": "dress_distribution", "name": "Dress Distribution", "order": 2, "description": "Uniform distribution"},
    {"stage_id": "study_material", "name": "Study Material Distribution", "order": 3, "description": "Books and materials"},
    {"stage_id": "classroom_training", "name": "Classroom Training", "order": 4, "description": "Main training phase"},
    {"stage_id": "assessment", "name": "Assessment", "order": 5, "description": "Evaluation and certification"},
    {"stage_id": "ojt", "name": "OJT (On-the-Job Training)", "order": 6, "description": "Practical work experience"},
    {"stage_id": "placement", "name": "Placement", "order": 7, "description": "Job placement"}
]
