import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from services.sheets_service import get_orders_sheet
from utils.logger import log_api_hit, write_admin_log

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/update', methods=['POST'])
def admin_update():
    log_api_hit()

    if not session.get('is_admin'):
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    data = request.json or {}
    order_id = data.get('order_id')

    if not order_id:
        return jsonify({"success": False, "error": "Missing order_id"}), 400

    try:
        ws = get_orders_sheet()
        col_values = ws.col_values(1)

        if order_id not in col_values:
            return jsonify({"success": False, "error": "Order not found"}), 404

        row_idx = col_values.index(order_id) + 1
        headers = ws.row_values(1)

        updates = []
        # Strictly available fields in the new 7-column schema: Status, Payment Status
        # We'll map the frontend payload keys to exact header keys
        field_map = {
            'status': 'Status',
            'payment_status': 'Payment Status',
            'preview_link': 'Preview Link',
            'notes': 'Notes'
        }

        for req_field, sheet_header in field_map.items():
            if req_field in data:
                val = data[req_field]
                try:
                    col_idx = headers.index(sheet_header) + 1
                    ws.update_cell(row_idx, col_idx, val)
                    updates.append(req_field)
                except ValueError:
                    print(f"⚠️ [ADMIN] Column {sheet_header} not found")

        if updates:
            # Update Timestamp
            current_time = datetime.utcnow().isoformat() + "Z"
            try:
                ts_col_idx = headers.index('Timestamp') + 1
                ws.update_cell(row_idx, ts_col_idx, current_time)
            except ValueError:
                pass

            write_admin_log("UPDATE_ORDER", request.path, data, {"success": True, "updated": updates})
            print(f"✅ [ADMIN] Updated {order_id}: {updates}")
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "No valid fields to update based on strict schema"}), 400

    except Exception as e:
        print(f"❌ [ADMIN ERROR]: {e}")
        write_admin_log("UPDATE_ORDER_ERROR", request.path, data, {"error": str(e)})
        return jsonify({"success": False, "error": str(e)}), 500
