import string
import random
import time
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from services.sheets_service import get_orders_sheet
from utils.logger import log_api_hit

orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')

def generate_order_id():
    return "DB-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@orders_bp.route('/create', methods=['POST'])
def create_order():
    log_api_hit()

    # Can handle both form-data (for screenshot) and JSON depending on frontend implementation
    data = request.form if request.form else request.json or {}

    required_fields = ['name', 'email', 'build_type', 'plan', 'total_price']
    for field in required_fields:
        if not data.get(field):
            print(f"❌ [VALIDATION] Missing: {field}")
            return jsonify({"success": False, "error": f"Missing field: {field}"}), 400

    order_id = generate_order_id()
    current_time = datetime.utcnow().isoformat() + "Z"

    total_price = str(data.get('total_price', '0')).replace(',', '')
    advance_paid = "0"
    remaining_amount = total_price

    try:
        ws = get_orders_sheet()

        # order_id, name, email, phone, build_type, plan, status, preview_link, total_price, advance_paid, remaining_amount, notes, created_at, updated_at
        order_data = [
            order_id,
            data.get('name', ''),
            data.get('email', ''),
            data.get('phone', ''),
            data.get('build_type', ''),
            data.get('plan', ''),
            "NEW",
            "",
            total_price,
            advance_paid,
            remaining_amount,
            data.get('notes', ''),
            current_time,
            current_time
        ]

        ws.append_row(order_data)
        print(f"✅ [ORDERS] Order {order_id} created successfully.")

        return jsonify({"success": True, "order_id": order_id})

    except Exception as e:
        print(f"❌ [ORDERS ERROR]: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@orders_bp.route('', methods=['GET'])
def get_orders():
    log_api_hit()

    user_email = session.get('email') or session.get('user_email')
    is_admin = session.get('is_admin')

    if not user_email and not is_admin:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        ws = get_orders_sheet()
        records = ws.get_all_records()

        orders = []
        for r in records:
            if is_admin or str(r.get('email', '')).strip().lower() == str(user_email).strip().lower():
                orders.append(r)

        return jsonify({"success": True, "orders": list(reversed(orders))})
    except Exception as e:
        print(f"❌ [ORDERS ERROR]: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@orders_bp.route('/track/<order_id>', methods=['GET'])
def track_order(order_id):
    log_api_hit()

    order_id = order_id.strip().upper()
    if not order_id:
        return jsonify({"success": False, "error": "Order ID required"}), 400

    try:
        ws = get_orders_sheet()
        col_values = ws.col_values(1)

        if order_id not in col_values:
            return jsonify({"success": False, "error": "Order not found"}), 404

        row_idx = col_values.index(order_id) + 1
        headers = ws.row_values(1)
        row_data = ws.row_values(row_idx)

        order = {}
        for i, h in enumerate(headers):
            order[h] = row_data[i] if i < len(row_data) else ""

        return jsonify({"success": True, "order": order})
    except Exception as e:
        print(f"❌ [TRACK ERROR]: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
