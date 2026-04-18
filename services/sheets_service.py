import os
import json
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread

SHEET_CONNECTED = False
GOOGLE_CLIENT = None
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "").strip()

def init_google_client():
    global GOOGLE_CLIENT, SHEET_CONNECTED, SHEET_ID

    creds_json_str = os.environ.get("GOOGLE_CREDS_JSON", "") or os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "").strip()

    if not creds_json_str or not sheet_id:
        print("❌ [FATAL] Missing GOOGLE_CREDS_JSON or GOOGLE_SHEET_ID.")
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
        SHEET_ID = sheet_id
        SHEET_CONNECTED = True
        print("✅ [AUTH] Google Sheets initialized.")
        return True
    except Exception as e:
        print(f"❌ [FATAL] Google Auth failed: {e}")
        SHEET_CONNECTED = False
        return False

def get_worksheet(title, auto_create=False, ensure_headers_list=None):
    if not GOOGLE_CLIENT:
        if not init_google_client():
            raise Exception("Google Client not initialized")

    try:
        spreadsheet = GOOGLE_CLIENT.open_by_key(SHEET_ID)
        try:
            ws = spreadsheet.worksheet(title)
        except Exception:
            if auto_create:
                print(f"⏳ [WORKSHEET] '{title}' not found. Creating...")
                ws = spreadsheet.add_worksheet(title=title, rows="1000", cols="20")
            else:
                raise Exception(f"Worksheet {title} not found")

        if ensure_headers_list:
            try:
                existing = ws.row_values(1)
                if existing != ensure_headers_list:
                    ws.insert_row(ensure_headers_list, 1)
            except Exception:
                ws.insert_row(ensure_headers_list, 1)

        return ws
    except Exception as e:
        print(f"❌ [WORKSHEET_ERROR] Failed to access sheet '{title}': {e}")
        raise

def get_orders_sheet():
    return get_worksheet("orders", True, [
        "order_id", "name", "email", "phone", "build_type", "plan",
        "status", "preview_link", "total_price", "advance_paid",
        "remaining_amount", "notes", "created_at", "updated_at"
    ])

def get_payments_sheet():
    return get_worksheet("payments", True, [
        "payment_id", "order_id", "amount", "type", "status", "timestamp"
    ])

def get_admin_logs_sheet():
    return get_worksheet("admin_logs", True, [
        "action", "endpoint", "payload", "response", "timestamp"
    ])

# Helper Functions specific to the user's setup requirements
def get_banner_sheet():
    return get_worksheet("Banner_Control", True, ["banner_text", "active", "duration_seconds", "background_color", "text_color"])

def get_settings_sheet():
    return get_worksheet("Settings", True, ["setting_name", "value"])

def get_coupons_sheet():
    return get_worksheet("Coupons", True, ["coupon_code", "discount_type", "discount_value", "min_order_value", "expiry_date", "active"])

def get_launch_tracker_sheet():
    return get_worksheet("LaunchTracker", True, ["Feature Name", "Category", "Status", "Notes", "Last Updated Timestamp"])

init_google_client()
