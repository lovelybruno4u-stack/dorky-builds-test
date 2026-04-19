import json
from datetime import datetime
from flask import request

def log_api_hit():
    print(f"🔥 API HIT: {request.path}")
    if request.is_json:
        print(f"📦 DATA: {request.json}")
    elif request.form:
        print(f"📦 DATA: {request.form}")

def write_admin_log(action, endpoint, payload, response):
    try:
        from services.sheets_service import get_logs_sheet
        ws = get_logs_sheet()
        if ws:
            timestamp = datetime.utcnow().isoformat() + "Z"
            event_details = f"Action: {action} | Endpoint: {endpoint} | Payload: {payload} | Response: {response}"
            ws.append_row([
                timestamp,
                event_details
            ])
    except Exception as e:
        print(f"❌ [LOGGER] Failed to write admin log: {e}")

def write_payment_log(order_id, amount, payment_type, user_email):
    try:
        from services.sheets_service import get_logs_sheet
        ws = get_logs_sheet()
        if ws:
            timestamp = datetime.utcnow().isoformat() + "Z"
            event_details = f"PAYMENT_RECEIVED | Order: {order_id} | Amount: {amount} | Type: {payment_type} | User: {user_email}"
            ws.append_row([
                timestamp,
                event_details
            ])
            print(f"✅ [PAYMENT] Trace recorded for {order_id}.")
    except Exception as e:
        print(f"❌ [LOGGER] CRITICAL: Failed to write payment log for {order_id}: {e}")

def write_submission_log(form_name, user_email, details):
    try:
        from services.sheets_service import get_logs_sheet
        ws = get_logs_sheet()
        if ws:
            timestamp = datetime.utcnow().isoformat() + "Z"
            event_details = f"SUBMISSION | Form: {form_name} | User: {user_email} | Details: {details}"
            ws.append_row([
                timestamp,
                event_details
            ])
            print(f"✅ [SUBMISSION] Trace recorded for {form_name}.")
    except Exception as e:
        print(f"❌ [LOGGER] Failed to write submission log: {e}")
