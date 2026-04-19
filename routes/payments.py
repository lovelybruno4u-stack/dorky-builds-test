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
    user_email = session.get('email') or session.get('user_email', 'unknown')

    if not order_id or not amount:
        print(f"❌ [PAYMENTS] Missing required fields for advance payment on {order_id}")
        return jsonify({"success": False, "error": "Missing order_id or amount"}), 400

    payment_id = str(uuid.uuid4())[:8]
    timestamp = datetime.utcnow().isoformat() + "Z"

    # 1. ALWAYS write to ledger first. This guarantees data is not lost even if Orders update fails.
    try:
        payments_ws = get_payments_sheet()
        payments_ws.append_row([
            payment_id,
            order_id,
            amount,
            payment_type,
            "SUCCESS",
            timestamp
        ])
        print(f"✅ [PAYMENTS] Immutable ledger entry recorded for Payment {payment_id} (Order: {order_id})")
    except Exception as e:
        print(f"❌ [PAYMENTS CRITICAL] Failed to write ledger for {payment_id}: {e}")
        return jsonify({"success": False, "error": f"Failed to record payment ledger: {e}"}), 500

    # 2. Write an immutable log trace
    try:
        from utils.logger import write_payment_log
        write_payment_log(order_id, amount, payment_type, user_email)
    except Exception as e:
        print(f"⚠️ [PAYMENTS] Non-fatal log write failure: {e}")

    # 3. Update the Orders sheet
    try:
        orders_ws = get_orders_sheet()
        col_values = orders_ws.col_values(1)

        if order_id not in col_values:
            print(f"⚠️ [PAYMENTS] Order {order_id} not found in Orders sheet. Ledger was saved.")
            return jsonify({"success": True, "payment_id": payment_id, "warning": "Order not found but payment recorded."})

        row_idx = col_values.index(order_id) + 1
        headers = orders_ws.row_values(1)
        row_data = orders_ws.row_values(row_idx)

        # Append payment proof to Notes
        if 'Notes' in headers:
            notes_idx = headers.index('Notes') + 1
            existing_notes = row_data[notes_idx-1] if len(row_data) >= notes_idx else ""
            new_notes = existing_notes + f" | [PAYMENT {timestamp}] +₹{amount} via {payment_type}"
            orders_ws.update_cell(row_idx, notes_idx, new_notes)

        if 'Payment Status' in headers:
            status_idx = headers.index('Payment Status') + 1
            orders_ws.update_cell(row_idx, status_idx, "Payment Received")

        if 'Timestamp' in headers:
            ts_idx = headers.index('Timestamp') + 1
            orders_ws.update_cell(row_idx, ts_idx, timestamp)

        print(f"✅ [PAYMENTS] Order {order_id} updated with payment {payment_id}")
        return jsonify({"success": True, "payment_id": payment_id})

    except Exception as e:
        print(f"❌ [PAYMENTS ERROR]: Failed to update Order {order_id} after successful payment {payment_id}. Error: {e}")
        # Return success because the payment WAS recorded in the ledger.
        # The user said "If even one advance payment is missed, the system has failed."
        # The ledger is the source of truth.
        return jsonify({"success": True, "payment_id": payment_id, "warning": "Payment recorded, but Order update failed."})
