import os
import json
from google.oauth2.service_account import Credentials
import gspread

SHEET_CONNECTED = False
GOOGLE_CLIENT = None
SPREADSHEET = None

# Global Worksheets
users_sheet = None
admin_sheet = None
logs_sheet = None
contacts_sheet = None
projects_sheet = None
orders_sheet = None
banner_sheet = None

def _enforce_worksheet(title, headers, default_data=None):
    global SPREADSHEET
    try:
        ws = SPREADSHEET.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        print(f"⏳ [WORKSHEET] '{title}' not found. Creating...")
        ws = SPREADSHEET.add_worksheet(title=title, rows="1000", cols="20")

    try:
        existing = ws.row_values(1)
        if not existing:
            ws.insert_row(headers, 1)
            if default_data:
                for row in default_data:
                    ws.append_row(row)
    except Exception as e:
        print(f"⚠️ [WORKSHEET] Sheet '{title}' is empty or unreadable. Initializing headers...")
        try:
            ws.insert_row(headers, 1)
            if default_data:
                for row in default_data:
                    ws.append_row(row)
        except Exception as e2:
            print(f"❌ [WORKSHEET] Failed to initialize headers for '{title}': {e2}")

    return ws


def init_google_client():
    global GOOGLE_CLIENT, SHEET_CONNECTED, SPREADSHEET
    global users_sheet, admin_sheet, logs_sheet, contacts_sheet, projects_sheet
    global orders_sheet, banner_sheet

    creds_json_str = os.environ.get("GOOGLE_CREDS_JSON", "") or os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "").strip()

    if not creds_json_str or not sheet_id:
        print("❌ [FATAL] Missing GOOGLE_CREDS_JSON or GOOGLE_SHEET_ID. Sheets offline.")
        SHEET_CONNECTED = False
        return False

    try:
        creds_dict = json.loads(creds_json_str)
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        GOOGLE_CLIENT = gspread.authorize(creds)
        SHEET_CONNECTED = True
        print("✅ [AUTH] Google Sheets authenticated.")
    except Exception as e:
        print(f"❌ [FATAL] Google Auth failed: {e}")
        SHEET_CONNECTED = False
        return False

    try:
        # Access strictly using provided ID, no creation, no searching
        SPREADSHEET = GOOGLE_CLIENT.open_by_key(sheet_id)
        print(f"✅ [WORKBOOK] Connected directly to GOOGLE_SHEET_ID: {sheet_id}")

# Enforce exact worksheets requested
        users_sheet = _enforce_worksheet("users", ["id", "name", "email", "password"])
        admin_sheet = _enforce_worksheet("admin", ["username", "password"], [["dorkybuildsadmin", "Poorvi@2011"]])
        logs_sheet = _enforce_worksheet("logs", ["time", "event"])
        contacts_sheet = _enforce_worksheet("contacts", ["name", "email", "message"])

        # User defined `projects` in instructions, which acts as orders.
        # "projects: title, description, status" -> Wait, they say:
        # "users.id ↔ projects.user_id" and "projects.id ↔ payments.project_id"
        # And previously they said: "total_amount, paid_amount, remaining_amount, advance_paid"
        # I must ensure the projects sheet has ALL these fields.
        projects_sheet = _enforce_worksheet("projects", [
            "id", "user_id", "title", "description", "status", "payment_status", "total_amount", "advance_paid", "remaining_amount", "preview_link", "notes", "timestamp"
        ])

        # Redefine payments sheet
        payments_sheet = _enforce_worksheet("payments", ["payment_id", "project_id", "amount", "type", "status", "timestamp"])

        # Banner for backwards compatibility
        banner_sheet = _enforce_worksheet("Banner", ["id", "text", "active"])

        # Ensure backwards compatibility for previously routed code expecting get_orders_sheet() to map to projects
        orders_sheet = projects_sheet

        print("✅ [WORKSHEETS] All sheets enforced and globals assigned.")
        return True

    except Exception as e:
        print(f"❌ [FATAL] Workbook connection/initialization failed: {e}")
        SHEET_CONNECTED = False
        return False

# Initialize eagerly on module load
init_google_client()

# Globals exposure helpers
def get_orders_sheet():
    sheet = globals().get('orders_sheet')
    if SHEET_CONNECTED and sheet is not None:
        return sheet
    raise Exception("Database disconnected or Orders sheet missing")

def get_banner_sheet():
    sheet = globals().get('banner_sheet')
    if SHEET_CONNECTED and sheet is not None:
        return sheet
    raise Exception("Database disconnected or Banner sheet missing")

def get_users_sheet():
    sheet = globals().get('users_sheet')
    if SHEET_CONNECTED and sheet is not None:
        return sheet
    raise Exception("Database disconnected or Users sheet missing")

def get_logs_sheet():
    sheet = globals().get('logs_sheet')
    if SHEET_CONNECTED and sheet is not None:
        return sheet
    raise Exception("Database disconnected or Logs sheet missing")

def get_contacts_sheet():
    sheet = globals().get('contacts_sheet')
    if SHEET_CONNECTED and sheet is not None:
        return sheet
    raise Exception("Database disconnected or Contacts sheet missing")

def get_projects_sheet():
    sheet = globals().get('projects_sheet')
    if SHEET_CONNECTED and sheet is not None:
        return sheet
    raise Exception("Database disconnected or Projects sheet missing")

def get_admin_sheet():
    sheet = globals().get('admin_sheet')
    if SHEET_CONNECTED and sheet is not None:
        return sheet
    raise Exception("Database disconnected or Admin sheet missing")
