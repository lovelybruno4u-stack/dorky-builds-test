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
