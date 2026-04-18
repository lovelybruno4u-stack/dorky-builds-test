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

        # Get current row to recalculate values
        row_data = ws.row_values(row_idx)
        order_dict = {}
        for i, h in enumerate(headers):
            order_dict[h] = row_data[i] if i < len(row_data) else ""

        updates = []
        for field in ['status', 'preview_link', 'notes', 'advance_paid']:
            if field in data:
                val = data[field]
                try:
                    col_idx = headers.index(field) + 1
                    ws.update_cell(row_idx, col_idx, val)
                    order_dict[field] = val
                    updates.append(field)
                except ValueError:
                    print(f"⚠️ [ADMIN] Column {field} not found")

        # Recalculate remaining amount
        try:
            total_price = float(str(order_dict.get('total_price', '0')).replace(',', ''))
            advance_paid = float(str(order_dict.get('advance_paid', '0')).replace(',', ''))
            remaining_amount = total_price - advance_paid

            rem_col_idx = headers.index('remaining_amount') + 1
            ws.update_cell(row_idx, rem_col_idx, remaining_amount)
            updates.append('remaining_amount')
        except ValueError:
            print("⚠️ [ADMIN] Could not recalculate remaining amount")

        if updates:
            # Update updated_at timestamp
            current_time = datetime.utcnow().isoformat() + "Z"
            ts_col_idx = headers.index('updated_at') + 1
            ws.update_cell(row_idx, ts_col_idx, current_time)

            write_admin_log("UPDATE_ORDER", request.path, data, {"success": True, "updated": updates})
            print(f"✅ [ADMIN] Updated {order_id}: {updates}")
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "No valid fields to update"}), 400

    except Exception as e:
        print(f"❌ [ADMIN ERROR]: {e}")
        write_admin_log("UPDATE_ORDER_ERROR", request.path, data, {"error": str(e)})
        return jsonify({"success": False, "error": str(e)}), 500
