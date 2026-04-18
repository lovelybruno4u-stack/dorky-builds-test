import os
import json
from google.oauth2.service_account import Credentials
import gspread

SHEET_CONNECTED = False
GOOGLE_CLIENT = None
SPREADSHEET = None

# Global Worksheets
orders_sheet = None
banner_sheet = None
users_sheet = None
payments_sheet = None
admin_logs_sheet = None
coupons_sheet = None
settings_sheet = None
launch_tracker_sheet = None

def _enforce_worksheet(title, headers, default_data=None):
    global SPREADSHEET
    try:
        ws = SPREADSHEET.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        print(f"⏳ [WORKSHEET] '{title}' not found. Creating...")
        ws = SPREADSHEET.add_worksheet(title=title, rows="1000", cols="20")

    try:
        existing = ws.row_values(1)
        if existing != headers:
            print(f"⚠️ [WORKSHEET] '{title}' headers mismatched or missing. Reinitializing...")
            ws.clear()
            ws.insert_row(headers, 1)
            if default_data:
                for row in default_data:
                    ws.append_row(row)
    except Exception as e:
        print(f"⚠️ [WORKSHEET] Error checking '{title}' headers, forcing reset. {e}")
        ws.clear()
        ws.insert_row(headers, 1)
        if default_data:
            for row in default_data:
                ws.append_row(row)

    return ws

def init_google_client():
    global GOOGLE_CLIENT, SHEET_CONNECTED, SPREADSHEET
    global orders_sheet, banner_sheet, payments_sheet, admin_logs_sheet, users_sheet
    global coupons_sheet, settings_sheet, launch_tracker_sheet

    creds_json_str = os.environ.get("GOOGLE_CREDS_JSON", "") or os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

    if not creds_json_str:
        print("❌ [FATAL] Missing GOOGLE_CREDS_JSON. Sheets offline.")
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

    # Manage Workbook "DorkyBuildsDB"
    try:
        # Try to find by exact name
        spreadsheets = GOOGLE_CLIENT.openall()
        target_name = "DorkyBuildsDB"
        SPREADSHEET = None

        for sp in spreadsheets:
            if sp.title == target_name:
                SPREADSHEET = sp
                break

        if not SPREADSHEET:
            print(f"⏳ [WORKBOOK] '{target_name}' not found. Creating new spreadsheet...")
            # Requires drive API permission to create and share if necessary.
            # Assuming the service account has permission to create.
            SPREADSHEET = GOOGLE_CLIENT.create(target_name)

            # Since it's a service account, it might need to share it to an owner email if we want human access.
            owner_email = os.environ.get("ADMIN_EMAIL", "dorkybuilds@gmail.com")
            if owner_email:
                try:
                    SPREADSHEET.share(owner_email, perm_type='user', role='writer')
                    print(f"✅ [WORKBOOK] Shared '{target_name}' with {owner_email}")
                except Exception as e:
                    print(f"⚠️ [WORKBOOK] Could not share with {owner_email}: {e}")

        print(f"✅ [WORKBOOK] Using '{target_name}' (ID: {SPREADSHEET.id})")

        # Enforce exactly the required schemas


        # 1. Orders
        orders_sheet = _enforce_worksheet("Orders", [
            "Order ID", "Name", "Email", "Build Type", "Status", "Payment Status", "Preview Link", "Notes", "Timestamp"
        ])

        # Auth / Users
        users_sheet = _enforce_worksheet("Users", ["uid", "name", "email", "password_hash", "created_at"])


        # 2. Banner
        banner_sheet = _enforce_worksheet("Banner", [
            "id", "text", "active"
        ], [
            ["1", "Welcome to Dorky Builds - System Online", "TRUE"]
        ])

        # Keep other required sheets active to not break other routes we built
        payments_sheet = _enforce_worksheet("payments", [
            "payment_id", "order_id", "amount", "type", "status", "timestamp"
        ])

        admin_logs_sheet = _enforce_worksheet("admin_logs", [
            "action", "endpoint", "payload", "response", "timestamp"
        ])

        settings_sheet = _enforce_worksheet("Settings", [
            "setting_name", "value"
        ], [
            ["UPI_ID", "bina.patil@axl"],
            ["MIN_ADVANCE", "10"],
            ["MAX_ADVANCE_PERCENT", "100"],
            ["SITE_MODE", "LIVE"]
        ])

        coupons_sheet = _enforce_worksheet("Coupons", [
            "coupon_code", "discount_type", "discount_value", "min_order_value", "expiry_date", "active"
        ], [
            ["FIRST100", "flat", "100", "0", "2026-12-31", "TRUE"]
        ])

        default_launch_features = [
            ["Homepage UI Design", "CORE UI", "Pending", "", ""],
            ["Responsive Design", "CORE UI", "Pending", "", ""],
            ["Navigation Flow", "CORE UI", "Pending", "", ""],
            ["Animations", "CORE UI", "Pending", "", ""],
            ["Flask Backend", "BACKEND", "Pending", "", ""],
            ["Google Sheets Integration", "BACKEND", "Pending", "", ""],
            ["Credentials Handling", "BACKEND", "Pending", "", ""],
            ["Logging System", "BACKEND", "Pending", "", ""],
            ["Email/Password Authentication", "AUTH", "Pending", "", ""],
            ["Login/Signup Flow", "AUTH", "Pending", "", ""],
            ["Session Handling", "AUTH", "Pending", "", ""],
            ["Build Request Form", "ORDERS", "Pending", "", ""],
            ["Build Type Selection", "ORDERS", "Pending", "", ""],
            ["Data Submission to Sheets", "ORDERS", "Pending", "", ""],
            ["Error Handling", "ORDERS", "Pending", "", ""],
            ["UPI Integration", "PAYMENT", "Pending", "", ""],
            ["Screenshot Upload", "PAYMENT", "Pending", "", ""],
            ["Image Handling", "PAYMENT", "Pending", "", ""],
            ["Payment UI", "PAYMENT", "Pending", "", ""],
            ["User Dashboard", "DASHBOARD", "Pending", "", ""],
            ["Order Tracking", "DASHBOARD", "Pending", "", ""],
            ["Status Display", "DASHBOARD", "Pending", "", ""],
            ["Admin Panel", "ADMIN", "Pending", "", ""],
            ["Order Update System", "ADMIN", "Pending", "", ""],
            ["Preview Link Feature", "ADMIN", "Pending", "", ""],
            ["Portfolio Page", "PAGES", "Pending", "", ""],
            ["Contact Page", "PAGES", "Pending", "", ""],
            ["Achievements Page", "PAGES", "Pending", "", ""],
            ["Upcoming Projects Page", "PAGES", "Pending", "", ""],
            ["Render Deployment", "DEPLOYMENT", "Pending", "", ""],
            ["Domain Setup", "DEPLOYMENT", "Pending", "", ""]
        ]
        launch_tracker_sheet = _enforce_worksheet("LaunchTracker", [
            "Feature Name", "Category", "Status", "Notes", "Last Updated Timestamp"
        ], default_launch_features)

        print("✅ [WORKSHEETS] All sheets enforced and globals assigned.")
        return True

    except Exception as e:
        print(f"❌ [FATAL] Workbook Initialization Failed: {e}")
        SHEET_CONNECTED = False
        return False

# Initialize eagerly on module load
init_google_client()

# Re-export getters for backward compatibility with the routes we already patched

def get_users_sheet():
    global users_sheet
    if SHEET_CONNECTED and users_sheet is not None:
        return users_sheet
    raise Exception("Database disconnected or Users sheet missing")

def get_orders_sheet():

    global orders_sheet
    if SHEET_CONNECTED and orders_sheet is not None:
        return orders_sheet
    raise Exception("Database disconnected or Orders sheet missing")

def get_banner_sheet():
    global banner_sheet
    if SHEET_CONNECTED and banner_sheet is not None:
        return banner_sheet
    raise Exception("Database disconnected or Banner sheet missing")

def get_payments_sheet():
    global payments_sheet
    if SHEET_CONNECTED and payments_sheet is not None:
        return payments_sheet
    raise Exception("Database disconnected or Payments sheet missing")

def get_admin_logs_sheet():
    global admin_logs_sheet
    if SHEET_CONNECTED and admin_logs_sheet is not None:
        return admin_logs_sheet
    raise Exception("Database disconnected or Admin Logs sheet missing")

def get_settings_sheet():
    global settings_sheet
    if SHEET_CONNECTED and settings_sheet is not None:
        return settings_sheet
    raise Exception("Database disconnected or Settings sheet missing")

def get_coupons_sheet():
    global coupons_sheet
    if SHEET_CONNECTED and coupons_sheet is not None:
        return coupons_sheet
    raise Exception("Database disconnected or Coupons sheet missing")

def get_launch_tracker_sheet():
    global launch_tracker_sheet
    if SHEET_CONNECTED and launch_tracker_sheet is not None:
        return launch_tracker_sheet
    raise Exception("Database disconnected or LaunchTracker sheet missing")
