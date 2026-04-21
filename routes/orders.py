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

    data = request.form if request.form else request.json or {}

    # Map frontend payload
    build_type = data.get('build_type') or data.get('projectType')

    if not data.get('name') or not data.get('email') or not build_type or not data.get('plan') or not data.get('total_price'):
        print(f"❌ [VALIDATION] Missing fields in payload")
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    # Handle Screenshot Upload if provided
    screenshot_url = ""
    try:
        if 'screenshot' in request.files:
            file = request.files['screenshot']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                unique_name = f"{int(time.time())}_{filename}"
                # Must reference the app config upload folder
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                file_path = os.path.join(upload_folder, unique_name)
                file.save(file_path)
                screenshot_url = f"/static/uploads/{unique_name}"
                print(f"✅ [UPLOAD] Saved: {screenshot_url}")
    except Exception as e:
        print(f"❌ [UPLOAD] Exception during file processing: {e}")
        return jsonify({"success": False, "error": "File processing failed"}), 500

    order_id = generate_order_id()
    current_time = datetime.utcnow().isoformat() + "Z"

    total_price = str(data.get('total_price', '0')).replace(',', '')
    advance_paid = str(data.get('advance_paid', '0')).replace(',', '')
    try:
        remaining_amount = str(float(total_price) - float(advance_paid))
    except ValueError:
        remaining_amount = total_price

    user_id = session.get('user_id', 'anonymous')
    notes = f"Name: {data.get('name', '')} | Email: {data.get('email', '')} | Phone: {data.get('phone', '')} | Plan: {data.get('plan', '')} | Features: {data.get('features', '')} | UPI: {data.get('upi_ref_id', '')} | Screenshot: {screenshot_url}"

    try:
        ws = get_orders_sheet() # Maps to projects

        order_data = [
            order_id,
            user_id,
            build_type,
            "New project submission via form",
            "Order Created",
            "unpaid",
            total_price,
            advance_paid,
            remaining_amount,
            "",
            notes,
            current_time
        ]

        ws.append_row(order_data)
        print(f"✅ [ORDERS] Order {order_id} created successfully for user {user_id}.")

        return jsonify({"success": True, "order_id": order_id})

    except Exception as e:
        print(f"❌ [ORDERS ERROR]: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@orders_bp.route('', methods=['GET'])
def get_orders():
    log_api_hit()

    user_id = session.get('user_id')
    is_admin = session.get('is_admin')

    if not user_id and not is_admin:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        ws = get_orders_sheet()
        records = ws.get_all_records()

        orders = []
        for r in records:
            if is_admin or str(r.get('user_id', '')).strip() == str(user_id).strip():
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

        # Safe match
        found_idx = -1
        for idx, val in enumerate(col_values):
            if str(val).strip().upper() == order_id:
                found_idx = idx
                break

        if found_idx == -1:
            return jsonify({"success": False, "error": "Order not found"}), 404

        row_idx = found_idx + 1
        headers = ws.row_values(1)
        row_data = ws.row_values(row_idx)

        order = {}
        for i, h in enumerate(headers):
            order[h] = row_data[i] if i < len(row_data) else ""

        return jsonify({"success": True, "order": order})
    except Exception as e:
        print(f"❌ [TRACK ERROR]: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
