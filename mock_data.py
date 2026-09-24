"""
Mock data used by DeskFlow.
Contains users, software catalog, and sample IT support tickets.
"""

from datetime import datetime, timedelta


# ============================================================
# USER DATA
# ============================================================

USERS = {
    "EMP001": {
        "employee_id": "EMP001",
        "name": "Aarav Sharma",
        "email": "aarav.sharma@deskflow.in",
        "department": "Engineering",
        "role": "Software Engineer",
        "manager_id": "EMP010",
        "location": "Ahmedabad",
        "phone": "+91-9876500001",
        "entitlements": ["Microsoft 365", "Slack", "GitHub", "Jira", "Zoom"],
        "active": True,
    },
    "EMP002": {
        "employee_id": "EMP002",
        "name": "Priya Patel",
        "email": "priya.patel@deskflow.in",
        "department": "Marketing",
        "role": "Marketing Analyst",
        "manager_id": "EMP011",
        "location": "Ahmedabad",
        "phone": "+91-9876500002",
        "entitlements": ["Microsoft 365", "Slack", "Zoom", "Adobe Creative Suite"],
        "active": True,
    },
    "EMP003": {
        "employee_id": "EMP003",
        "name": "Rohan Mehta",
        "email": "rohan.mehta@deskflow.in",
        "department": "Finance",
        "role": "Financial Analyst",
        "manager_id": "EMP012",
        "location": "Mumbai",
        "phone": "+91-9876500003",
        "entitlements": ["Microsoft 365", "Slack", "Zoom", "SAP"],
        "active": True,
    },
    "EMP004": {
        "employee_id": "EMP004",
        "name": "Ananya Iyer",
        "email": "ananya.iyer@deskflow.in",
        "department": "Human Resources",
        "role": "HR Specialist",
        "manager_id": "EMP013",
        "location": "Bengaluru",
        "phone": "+91-9876500004",
        "entitlements": ["Microsoft 365", "Slack", "Zoom", "Workday"],
        "active": True,
    },
    "EMP005": {
        "employee_id": "EMP005",
        "name": "Vikram Desai",
        "email": "vikram.desai@deskflow.in",
        "department": "Engineering",
        "role": "DevOps Engineer",
        "manager_id": "EMP010",
        "location": "Pune",
        "phone": "+91-9876500005",
        "entitlements": ["Microsoft 365", "Slack", "GitHub", "Jira", "Zoom", "AWS Console"],
        "active": True,
    },
    "EMP006": {
        "employee_id": "EMP006",
        "name": "Kavya Nair",
        "email": "kavya.nair@deskflow.in",
        "department": "Engineering",
        "role": "Backend Developer",
        "manager_id": "EMP010",
        "location": "Kochi",
        "phone": "+91-9876500006",
        "entitlements": ["Microsoft 365", "Slack", "GitHub", "Jira"],
        "active": True,
    },
    "EMP007": {
        "employee_id": "EMP007",
        "name": "Aditya Verma",
        "email": "aditya.verma@deskflow.in",
        "department": "Engineering",
        "role": "Frontend Developer",
        "manager_id": "EMP010",
        "location": "Delhi",
        "phone": "+91-9876500007",
        "entitlements": ["Microsoft 365", "Slack", "GitHub", "Jira", "Figma"],
        "active": True,
    },
    "EMP008": {
        "employee_id": "EMP008",
        "name": "Neha Joshi",
        "email": "neha.joshi@deskflow.in",
        "department": "Engineering",
        "role": "QA Engineer",
        "manager_id": "EMP010",
        "location": "Jaipur",
        "phone": "+91-9876500008",
        "entitlements": ["Microsoft 365", "Slack", "Jira", "Postman"],
        "active": True,
    },
    "EMP009": {
        "employee_id": "EMP009",
        "name": "Siddharth Rao",
        "email": "siddharth.rao@deskflow.in",
        "department": "IT Operations",
        "role": "System Administrator",
        "manager_id": "EMP014",
        "location": "Hyderabad",
        "phone": "+91-9876500009",
        "entitlements": ["Microsoft 365", "Slack", "AWS Console", "Azure Portal"],
        "active": True,
    },
    "EMP010": {
        "employee_id": "EMP010",
        "name": "Rahul Kulkarni",
        "email": "rahul.kulkarni@deskflow.in",
        "department": "Engineering",
        "role": "Engineering Manager",
        "manager_id": "EMP020",
        "location": "Pune",
        "phone": "+91-9876500010",
        "entitlements": ["Microsoft 365", "Slack", "GitHub", "Jira", "Zoom", "AWS Console"],
        "active": True,
    },
    "EMP011": {
        "employee_id": "EMP011",
        "name": "Sneha Kapoor",
        "email": "sneha.kapoor@deskflow.in",
        "department": "Marketing",
        "role": "Marketing Manager",
        "manager_id": "EMP020",
        "location": "Delhi",
        "phone": "+91-9876500011",
        "entitlements": ["Microsoft 365", "Slack", "Zoom", "Adobe Creative Suite", "Canva"],
        "active": True,
    },
    "EMP012": {
        "employee_id": "EMP012",
        "name": "Manish Shah",
        "email": "manish.shah@deskflow.in",
        "department": "Finance",
        "role": "Finance Manager",
        "manager_id": "EMP020",
        "location": "Ahmedabad",
        "phone": "+91-9876500012",
        "entitlements": ["Microsoft 365", "Slack", "Zoom", "SAP", "Power BI"],
        "active": True,
    },
    "EMP013": {
        "employee_id": "EMP013",
        "name": "Pooja Menon",
        "email": "pooja.menon@deskflow.in",
        "department": "Human Resources",
        "role": "HR Manager",
        "manager_id": "EMP020",
        "location": "Bengaluru",
        "phone": "+91-9876500013",
        "entitlements": ["Microsoft 365", "Slack", "Zoom", "Workday"],
        "active": True,
    },
    "EMP014": {
        "employee_id": "EMP014",
        "name": "Arjun Malhotra",
        "email": "arjun.malhotra@deskflow.in",
        "department": "IT Operations",
        "role": "IT Operations Manager",
        "manager_id": "EMP020",
        "location": "Mumbai",
        "phone": "+91-9876500014",
        "entitlements": ["Microsoft 365", "Slack", "AWS Console", "Azure Portal", "ServiceNow"],
        "active": True,
    },
    "EMP015": {
        "employee_id": "EMP015",
        "name": "Ishita Gupta",
        "email": "ishita.gupta@deskflow.in",
        "department": "Sales",
        "role": "Sales Executive",
        "manager_id": "EMP016",
        "location": "Lucknow",
        "phone": "+91-9876500015",
        "entitlements": ["Microsoft 365", "Slack", "Zoom", "Salesforce"],
        "active": True,
    },
    "EMP016": {
        "employee_id": "EMP016",
        "name": "Nitin Bansal",
        "email": "nitin.bansal@deskflow.in",
        "department": "Sales",
        "role": "Sales Manager",
        "manager_id": "EMP020",
        "location": "Chandigarh",
        "phone": "+91-9876500016",
        "entitlements": ["Microsoft 365", "Slack", "Zoom", "Salesforce", "Power BI"],
        "active": True,
    },
    "EMP017": {
        "employee_id": "EMP017",
        "name": "Meera Krishnan",
        "email": "meera.krishnan@deskflow.in",
        "department": "Customer Support",
        "role": "Support Executive",
        "manager_id": "EMP018",
        "location": "Chennai",
        "phone": "+91-9876500017",
        "entitlements": ["Microsoft 365", "Slack", "Zoom", "Zendesk"],
        "active": True,
    },
    "EMP018": {
        "employee_id": "EMP018",
        "name": "Harsh Vora",
        "email": "harsh.vora@deskflow.in",
        "department": "Customer Support",
        "role": "Support Manager",
        "manager_id": "EMP020",
        "location": "Ahmedabad",
        "phone": "+91-9876500018",
        "entitlements": ["Microsoft 365", "Slack", "Zoom", "Zendesk", "Power BI"],
        "active": True,
    },
    "EMP019": {
        "employee_id": "EMP019",
        "name": "Tanvi Sethi",
        "email": "tanvi.sethi@deskflow.in",
        "department": "Design",
        "role": "UI/UX Designer",
        "manager_id": "EMP011",
        "location": "Gurugram",
        "phone": "+91-9876500019",
        "entitlements": ["Microsoft 365", "Slack", "Zoom", "Figma", "Adobe Creative Suite"],
        "active": True,
    },
    "EMP020": {
        "employee_id": "EMP020",
        "name": "Suresh Choudhary",
        "email": "suresh.choudhary@deskflow.in",
        "department": "Management",
        "role": "Chief Technology Officer",
        "manager_id": None,
        "location": "Mumbai",
        "phone": "+91-9876500020",
        "entitlements": ["Microsoft 365", "Slack", "Zoom", "AWS Console", "Power BI"],
        "active": True,
    },
    "EMP021": {
        "employee_id": "EMP021",
        "name": "Divya Reddy",
        "email": "divya.reddy@deskflow.in",
        "department": "Data Science",
        "role": "Data Scientist",
        "manager_id": "EMP022",
        "location": "Hyderabad",
        "phone": "+91-9876500021",
        "entitlements": ["Microsoft 365", "Slack", "GitHub", "Jira", "AWS Console", "Databricks"],
        "active": True,
    },
    "EMP022": {
        "employee_id": "EMP022",
        "name": "Karan Singh",
        "email": "karan.singh@deskflow.in",
        "department": "Data Science",
        "role": "Data Science Manager",
        "manager_id": "EMP020",
        "location": "Noida",
        "phone": "+91-9876500022",
        "entitlements": ["Microsoft 365", "Slack", "GitHub", "Jira", "AWS Console", "Databricks", "Power BI"],
        "active": True,
    },
    "EMP023": {
        "employee_id": "EMP023",
        "name": "Simran Kaur",
        "email": "simran.kaur@deskflow.in",
        "department": "Legal",
        "role": "Legal Associate",
        "manager_id": "EMP024",
        "location": "Amritsar",
        "phone": "+91-9876500023",
        "entitlements": ["Microsoft 365", "Slack", "Zoom", "DocuSign"],
        "active": True,
    },
    "EMP024": {
        "employee_id": "EMP024",
        "name": "Amit Trivedi",
        "email": "amit.trivedi@deskflow.in",
        "department": "Legal",
        "role": "Legal Manager",
        "manager_id": "EMP020",
        "location": "Ahmedabad",
        "phone": "+91-9876500024",
        "entitlements": ["Microsoft 365", "Slack", "Zoom", "DocuSign", "Adobe Acrobat"],
        "active": True,
    },
    "EMP025": {
        "employee_id": "EMP025",
        "name": "Lakshmi Narayanan",
        "email": "lakshmi.narayanan@deskflow.in",
        "department": "Procurement",
        "role": "Procurement Specialist",
        "manager_id": "EMP026",
        "location": "Chennai",
        "phone": "+91-9876500025",
        "entitlements": ["Microsoft 365", "Slack", "Zoom", "SAP"],
        "active": True,
    },
    "EMP026": {
        "employee_id": "EMP026",
        "name": "Vivek Agarwal",
        "email": "vivek.agarwal@deskflow.in",
        "department": "Procurement",
        "role": "Procurement Manager",
        "manager_id": "EMP020",
        "location": "Kolkata",
        "phone": "+91-9876500026",
        "entitlements": ["Microsoft 365", "Slack", "Zoom", "SAP", "Power BI"],
        "active": True,
    },
}


# ============================================================
# SOFTWARE CATALOG
# ============================================================

SOFTWARE_CATALOG = {
    "Microsoft 365": {
        "name": "Microsoft 365",
        "category": "Productivity",
        "approval_required": False,
        "available_licenses": 100,
    },
    "Slack": {
        "name": "Slack",
        "category": "Communication",
        "approval_required": False,
        "available_licenses": 100,
    },
    "Zoom": {
        "name": "Zoom",
        "category": "Communication",
        "approval_required": False,
        "available_licenses": 100,
    },
    "Jira": {
        "name": "Jira",
        "category": "Project Management",
        "approval_required": False,
        "available_licenses": 50,
    },
    "GitHub": {
        "name": "GitHub",
        "category": "Development",
        "approval_required": True,
        "approver_role": "Engineering Manager",
        "available_licenses": 30,
    },
    "Adobe Creative Suite": {
        "name": "Adobe Creative Suite",
        "category": "Design",
        "approval_required": True,
        "approver_role": "Department Manager",
        "available_licenses": 15,
    },
    "Figma": {
        "name": "Figma",
        "category": "Design",
        "approval_required": True,
        "approver_role": "Design Lead",
        "available_licenses": 20,
    },
    "SAP": {
        "name": "SAP",
        "category": "ERP",
        "approval_required": True,
        "approver_role": "Finance Director",
        "available_licenses": 10,
    },
    "AWS Console": {
        "name": "AWS Console",
        "category": "Cloud Infrastructure",
        "approval_required": True,
        "approver_role": "CTO",
        "available_licenses": 20,
    },
    "Azure Portal": {
        "name": "Azure Portal",
        "category": "Cloud Infrastructure",
        "approval_required": True,
        "approver_role": "CTO",
        "available_licenses": 20,
    },
    "Workday": {
        "name": "Workday",
        "category": "Human Resources",
        "approval_required": True,
        "approver_role": "HR Director",
        "available_licenses": 15,
    },
    "Power BI": {
        "name": "Power BI",
        "category": "Analytics",
        "approval_required": True,
        "approver_role": "Department Manager",
        "available_licenses": 25,
    },
    "Salesforce": {
        "name": "Salesforce",
        "category": "CRM",
        "approval_required": True,
        "approver_role": "Sales Director",
        "available_licenses": 40,
    },
    "Postman": {
        "name": "Postman",
        "category": "Development",
        "approval_required": False,
        "available_licenses": 50,
    },
    "ServiceNow": {
        "name": "ServiceNow",
        "category": "IT Service Management",
        "approval_required": True,
        "approver_role": "IT Operations Manager",
        "available_licenses": 25,
    },
    "Canva": {
        "name": "Canva",
        "category": "Design",
        "approval_required": False,
        "available_licenses": 40,
    },
    "Zendesk": {
        "name": "Zendesk",
        "category": "Customer Support",
        "approval_required": True,
        "approver_role": "Support Manager",
        "available_licenses": 30,
    },
    "Databricks": {
        "name": "Databricks",
        "category": "Data Engineering",
        "approval_required": True,
        "approver_role": "Data Science Manager",
        "available_licenses": 12,
    },
    "DocuSign": {
        "name": "DocuSign",
        "category": "Document Management",
        "approval_required": True,
        "approver_role": "Legal Manager",
        "available_licenses": 20,
    },
    "Adobe Acrobat": {
        "name": "Adobe Acrobat",
        "category": "Document Management",
        "approval_required": True,
        "approver_role": "Department Manager",
        "available_licenses": 30,
    },
}


# ============================================================
# TICKET DATA
# ============================================================

_ticket_counter = [1030]


def _next_ticket_id() -> str:
    _ticket_counter[0] += 1
    return f"TKT-{_ticket_counter[0]}"


def _ticket(
    ticket_id,
    employee_id,
    title,
    description,
    priority,
    status,
    category,
    days_ago,
    assigned_to,
    resolution=None,
    hours_open=0,
):
    created_at = datetime.now() - timedelta(days=days_ago, hours=hours_open)
    updated_at = created_at + timedelta(hours=2)

    if status in {"in_progress", "open", "pending"}:
        updated_at = datetime.now() - timedelta(hours=hours_open)

    return {
        "ticket_id": ticket_id,
        "employee_id": employee_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": status,
        "category": category,
        "created_at": created_at.isoformat(),
        "updated_at": updated_at.isoformat(),
        "assigned_to": assigned_to,
        "resolution": resolution,
    }


TICKETS = {
    "TKT-1001": _ticket(
        "TKT-1001", "EMP001", "VPN not connecting from home",
        "VPN stopped working after an internet connection change.",
        "high", "resolved", "Network", 15, "L2-Network",
        "Updated VPN configuration and verified successful connection."
    ),
    "TKT-1002": _ticket(
        "TKT-1002", "EMP003", "SAP access request for month-end closing",
        "Requires SAP FI module access for month-end closing activities.",
        "medium", "in_progress", "Software Access", 2, "L1-Software"
    ),
    "TKT-1003": _ticket(
        "TKT-1003", "EMP005", "Laptop battery draining quickly",
        "Laptop battery drops from 100% to 20% within two hours.",
        "medium", "open", "Hardware", 1, "L1-HelpDesk"
    ),
    "TKT-1004": _ticket(
        "TKT-1004", "EMP007", "Figma license request",
        "Needs Figma professional access for the new dashboard design.",
        "low", "pending", "Software Access", 3, "L1-Software"
    ),
    "TKT-1005": _ticket(
        "TKT-1005", "EMP006", "Git repository permission denied",
        "Unable to push code to the backend repository.",
        "high", "resolved", "Software Access", 8, "L2-Engineering",
        "Repository permissions were updated and access was tested."
    ),
    "TKT-1006": _ticket(
        "TKT-1006", "EMP002", "Microsoft Teams audio not working",
        "Microphone is not detected during internal meetings.",
        "medium", "resolved", "Software", 7, "L1-HelpDesk",
        "Reinstalled audio drivers and corrected application permissions."
    ),
    "TKT-1007": _ticket(
        "TKT-1007", "EMP004", "Workday login failure",
        "User receives an invalid session error during login.",
        "high", "in_progress", "Software", 1, "L2-Software"
    ),
    "TKT-1008": _ticket(
        "TKT-1008", "EMP009", "AWS console access request",
        "Requires read-only AWS access for infrastructure monitoring.",
        "high", "pending", "Software Access", 4, "L2-Cloud"
    ),
    "TKT-1009": _ticket(
        "TKT-1009", "EMP010", "Jira board loading slowly",
        "Engineering sprint board takes more than one minute to load.",
        "medium", "resolved", "Performance", 10, "L2-Software",
        "Cleared browser cache and escalated a service-side performance issue."
    ),
    "TKT-1010": _ticket(
        "TKT-1010", "EMP011", "Adobe Creative Suite activation issue",
        "Adobe license is assigned but the application remains inactive.",
        "medium", "open", "Software", 1, "L1-Software"
    ),
    "TKT-1011": _ticket(
        "TKT-1011", "EMP012", "Power BI report not refreshing",
        "Scheduled refresh fails with a data source authentication error.",
        "high", "in_progress", "Application", 2, "L2-Analytics"
    ),
    "TKT-1012": _ticket(
        "TKT-1012", "EMP013", "Employee onboarding account setup",
        "New employee requires email, Slack, and HR application access.",
        "medium", "resolved", "Account Management", 12, "L1-HelpDesk",
        "Created required accounts and confirmed access with HR."
    ),
    "TKT-1013": _ticket(
        "TKT-1013", "EMP015", "Salesforce password reset",
        "User is locked out after multiple unsuccessful login attempts.",
        "high", "resolved", "Account Management", 5, "L1-Software",
        "Reset the password and enabled account recovery options."
    ),
    "TKT-1014": _ticket(
        "TKT-1014", "EMP017", "Zendesk notification delay",
        "Ticket notifications are arriving several minutes late.",
        "medium", "open", "Application", 1, "L2-Software"
    ),
    "TKT-1015": _ticket(
        "TKT-1015", "EMP019", "Design workstation display flickering",
        "External monitor flickers when connected through the docking station.",
        "high", "in_progress", "Hardware", 2, "L1-Hardware"
    ),
    "TKT-1016": _ticket(
        "TKT-1016", "EMP021", "Databricks workspace access",
        "Data science team member needs access to the analytics workspace.",
        "medium", "pending", "Software Access", 4, "L2-Cloud"
    ),
    "TKT-1017": _ticket(
        "TKT-1017", "EMP022", "Cloud storage quota exceeded",
        "Data pipeline failed because the assigned storage quota was reached.",
        "critical", "in_progress", "Cloud Infrastructure", 1, "L3-Cloud"
    ),
    "TKT-1018": _ticket(
        "TKT-1018", "EMP023", "DocuSign invitation not received",
        "Legal team member has not received the signing invitation.",
        "medium", "resolved", "Application", 6, "L1-Software",
        "Resent the invitation and confirmed delivery."
    ),
    "TKT-1019": _ticket(
        "TKT-1019", "EMP025", "SAP purchase order error",
        "Purchase order cannot be submitted due to a validation error.",
        "high", "open", "Application", 1, "L2-Software"
    ),
    "TKT-1020": _ticket(
        "TKT-1020", "EMP001", "Slow internet connection",
        "Internet speed drops significantly during afternoon work hours.",
        "medium", "resolved", "Network", 14, "L2-Network",
        "Updated network adapter settings and confirmed stable connectivity."
    ),
    "TKT-1021": _ticket(
        "TKT-1021", "EMP008", "Automated test pipeline failing",
        "CI pipeline fails during dependency installation.",
        "high", "in_progress", "Development", 2, "L2-Engineering"
    ),
    "TKT-1022": _ticket(
        "TKT-1022", "EMP014", "Azure Portal MFA issue",
        "MFA prompt loops repeatedly during portal login.",
        "critical", "resolved", "Security", 9, "L3-Security",
        "Reset MFA registration and verified successful authentication."
    ),
    "TKT-1023": _ticket(
        "TKT-1023", "EMP016", "Power BI dashboard permission request",
        "Sales manager requires access to the monthly sales dashboard.",
        "medium", "pending", "Software Access", 3, "L2-Analytics"
    ),
    "TKT-1024": _ticket(
        "TKT-1024", "EMP018", "Headset not detected",
        "USB headset is not recognized by the employee workstation.",
        "low", "resolved", "Hardware", 11, "L1-Hardware",
        "Updated USB drivers and replaced the faulty connection cable."
    ),
    "TKT-1025": _ticket(
        "TKT-1025", "EMP024", "Adobe Acrobat installation request",
        "Needs Adobe Acrobat for reviewing and signing legal documents.",
        "low", "pending", "Software Access", 2, "L1-Software"
    ),
    "TKT-1026": _ticket(
        "TKT-1026", "EMP002", "Email mailbox almost full",
        "Mailbox storage is above 95 percent of the allocated quota.",
        "medium", "open", "Email", 1, "L1-HelpDesk"
    ),
    "TKT-1027": _ticket(
        "TKT-1027", "EMP004", "Employee portal page unavailable",
        "HR portal returns a 503 error during login.",
        "high", "in_progress", "Application", 1, "L2-Software"
    ),
    "TKT-1028": _ticket(
        "TKT-1028", "EMP005", "Docker build failing",
        "Docker image build fails because a package cannot be downloaded.",
        "high", "resolved", "Development", 13, "L2-Engineering",
        "Updated dependency versions and corrected the Docker build configuration."
    ),
    "TKT-1029": _ticket(
        "TKT-1029", "EMP020", "Executive laptop replacement request",
        "Current laptop is outdated and unable to support required workloads.",
        "medium", "open", "Hardware", 3, "L1-Hardware"
    ),
    "TKT-1030": _ticket(
        "TKT-1030", "EMP021", "Python environment dependency conflict",
        "Machine learning project fails due to incompatible package versions.",
        "medium", "resolved", "Development", 7, "L2-Engineering",
        "Created a clean virtual environment and pinned compatible dependencies."
    ),
}


# ============================================================
# OPTIONAL SUPPORT GROUPS
# ============================================================

SUPPORT_GROUPS = {
    "L1-HelpDesk": {
        "name": "Level 1 Help Desk",
        "specialization": "General IT Support",
        "sla_hours": 8,
    },
    "L1-Software": {
        "name": "Level 1 Software Support",
        "specialization": "Software and Access Requests",
        "sla_hours": 12,
    },
    "L1-Hardware": {
        "name": "Level 1 Hardware Support",
        "specialization": "Laptop, Desktop, and Peripheral Issues",
        "sla_hours": 12,
    },
    "L2-Network": {
        "name": "Level 2 Network Support",
        "specialization": "VPN, Wi-Fi, and Connectivity",
        "sla_hours": 8,
    },
    "L2-Software": {
        "name": "Level 2 Software Support",
        "specialization": "Application Troubleshooting",
        "sla_hours": 16,
    },
    "L2-Engineering": {
        "name": "Level 2 Engineering Support",
        "specialization": "Development Tools and CI/CD",
        "sla_hours": 16,
    },
    "L2-Cloud": {
        "name": "Level 2 Cloud Support",
        "specialization": "Cloud Infrastructure and Access",
        "sla_hours": 8,
    },
    "L2-Analytics": {
        "name": "Level 2 Analytics Support",
        "specialization": "Power BI and Data Platforms",
        "sla_hours": 16,
    },
    "L3-Cloud": {
        "name": "Level 3 Cloud Engineering",
        "specialization": "Critical Cloud Infrastructure",
        "sla_hours": 4,
    },
    "L3-Security": {
        "name": "Level 3 Security Support",
        "specialization": "Authentication and Security Incidents",
        "sla_hours": 4,
    },
}


# ============================================================
# DEVICE INVENTORY (endpoint management)
# ============================================================

def _build_devices() -> dict:
    """Deterministic device inventory: one laptop per employee, a desktop for some."""
    now = datetime.now()
    inventory: dict = {}
    for i, uid in enumerate(USERS):
        first = USERS[uid]["name"].split()[0].lower()
        is_mac = i % 3 == 0
        laptop = {
            "device_id": f"LAP-{1001 + i}",
            "name": f"{first}-laptop",
            "type": "laptop",
            "model": 'MacBook Pro 14" (M3)' if is_mac else "ThinkPad T14 Gen 4",
            "os": "macOS 15.1" if is_mac else "Windows 11 Pro",
            "os_build": "24B83" if is_mac else f"22631.{4100 + i * 17}",
            "os_patch_days": (i * 7) % 60,
            "disk_encrypted": i % 6 != 0,
            "av_signature_days": (i * 3) % 10,
            "managed_by": "Jamf" if is_mac else "Microsoft Intune",
            "last_check_in": (now - timedelta(hours=(i * 11) % 100)).isoformat(),
            "serial": f"PF{3400 + i}A9C",
        }
        inventory[uid] = [laptop]
        if i % 4 == 0:
            inventory[uid].append({
                "device_id": f"DSK-{2001 + i}",
                "name": f"{first}-desktop",
                "type": "desktop",
                "model": "ThinkCentre M70q",
                "os": "Windows 11 Pro",
                "os_build": f"22631.{4200 + i * 13}",
                "os_patch_days": (i * 5 + 12) % 60,
                "disk_encrypted": i % 8 != 0,
                "av_signature_days": (i * 5 + 2) % 10,
                "managed_by": "Microsoft Intune",
                "last_check_in": (now - timedelta(hours=(i * 5 + 3) % 90)).isoformat(),
                "serial": f"PC{7100 + i}K2D",
            })
    return inventory


DEVICES: dict = _build_devices()


# ============================================================
# VPN GATEWAY + SESSIONS (network diagnostics)
# ============================================================

def _build_vpn_sessions() -> dict:
    now = datetime.now()
    sessions: dict = {}
    for i, uid in enumerate(USERS):
        sessions[uid] = {
            "connected": i % 3 != 0,
            "protocol": "WireGuard",
            "client_version": "1.0.2026.42" if i % 4 else "1.0.2024.11",
            "assigned_ip": f"10.8.0.{20 + i}",
            "last_handshake": (now - timedelta(minutes=(i * 7) % 45 or 1)).isoformat(),
            "split_tunnel": True,
        }
    return sessions


VPN_SESSIONS: dict = _build_vpn_sessions()

VPN_GATEWAY: dict = {
    "gateway_id": "gw-ap-mum-01",
    "region": "Mumbai (ap-south-1)",
    "status": "operational",
    "protocol": "WireGuard",
    "server_version": "1.0.2026.42",
    "public_ip": "203.0.113.10",
    "portal": "vpn.deskflow.in",
    "connected_clients": sum(1 for s in VPN_SESSIONS.values() if s["connected"]),
}
