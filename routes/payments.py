import uuid
import os
import time
from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from services.sheets_service import get_orders_sheet, get_payments_sheet
from utils.logger import log_api_hit, write_admin_log

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@payments_bp.route('/add', methods=['POST'])
def add_payment():
    log_api_hit()

    data = request.form if request.form else request.json or {}
    order_id = data.get('order_id')
    amount = data.get('amount')
    payment_type = data.get('type', 'UPI')

    if not order_id or not amount:
        return jsonify({"success": False, "error": "Missing order_id or amount"}), 400

    try:
        orders_ws = get_orders_sheet()
        col_values = orders_ws.col_values(1)

        if order_id not in col_values:
            return jsonify({"success": False, "error": "Order not found"}), 404

        row_idx = col_values.index(order_id) + 1
        headers = orders_ws.row_values(1)

        # Get current advance_paid
        advance_col_idx = headers.index('advance_paid') + 1
        total_col_idx = headers.index('total_price') + 1
        rem_col_idx = headers.index('remaining_amount') + 1

        row_data = orders_ws.row_values(row_idx)
        current_advance = float(str(row_data[advance_col_idx-1] if len(row_data) >= advance_col_idx else '0').replace(',', ''))
        total_price = float(str(row_data[total_col_idx-1] if len(row_data) >= total_col_idx else '0').replace(',', ''))

        new_advance = current_advance + float(amount)
        remaining = total_price - new_advance

        # Insert payment record
        payments_ws = get_payments_sheet()
        payment_id = str(uuid.uuid4())[:8]
        timestamp = datetime.utcnow().isoformat() + "Z"

        payments_ws.append_row([
            payment_id,
            order_id,
            amount,
            payment_type,
            "SUCCESS",
            timestamp
        ])

        # Update order record
        orders_ws.update_cell(row_idx, advance_col_idx, new_advance)
        orders_ws.update_cell(row_idx, rem_col_idx, remaining)

        # Update timestamp
        ts_col_idx = headers.index('updated_at') + 1
        orders_ws.update_cell(row_idx, ts_col_idx, timestamp)

        print(f"✅ [PAYMENTS] Payment {payment_id} recorded for Order {order_id}.")
        return jsonify({"success": True, "payment_id": payment_id})

    except Exception as e:
        print(f"❌ [PAYMENTS ERROR]: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
