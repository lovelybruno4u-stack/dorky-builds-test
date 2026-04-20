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
    project_id = data.get('order_id') or data.get('project_id')
    amount_str = data.get('amount')
    payment_type = data.get('type', 'UPI')
    user_email = session.get('email') or session.get('user_email', 'unknown')

    if not project_id or not amount_str:
        print(f"❌ [PAYMENTS] Missing required fields for advance payment on {project_id}")
        return jsonify({"success": False, "error": "Missing project_id or amount"}), 400

    try:
        new_amount = float(str(amount_str).replace(',', ''))
    except ValueError:
        return jsonify({"success": False, "error": "Invalid amount format"}), 400

    payment_id = str(uuid.uuid4())[:8]
    timestamp = datetime.utcnow().isoformat() + "Z"

    # 1. ALWAYS write to ledger first.
    try:
        payments_ws = get_payments_sheet()
        payments_ws.append_row([
            payment_id,
            project_id,
            new_amount,
            payment_type,
            "SUCCESS",
            timestamp
        ])
        print(f"✅ [PAYMENTS] Immutable ledger entry recorded for Payment {payment_id} (Project: {project_id})")
    except Exception as e:
        print(f"❌ [PAYMENTS CRITICAL] Failed to write ledger for {payment_id}: {e}")
        return jsonify({"success": False, "error": f"Failed to record payment ledger: {e}"}), 500

    # 2. Write an immutable log trace
    try:
        from utils.logger import write_payment_log
        write_payment_log(project_id, new_amount, payment_type, user_email)
    except Exception as e:
        print(f"⚠️ [PAYMENTS] Non-fatal log write failure: {e}")

    # 3. Calculate Sum and Update the Projects sheet
    try:
        # Sum all payments
        all_payments = payments_ws.get_all_records()
        total_paid_for_project = 0.0
        for p in all_payments:
            if str(p.get('project_id', '')).strip() == str(project_id).strip() and str(p.get('status', '')) == 'SUCCESS':
                try:
                    total_paid_for_project += float(str(p.get('amount', '0')).replace(',', ''))
                except ValueError:
                    pass

        # Update Project
        projects_ws = get_orders_sheet() # Maps to projects
        col_values = projects_ws.col_values(1)

        if project_id not in col_values:
            print(f"⚠️ [PAYMENTS] Project {project_id} not found in Projects sheet. Ledger was saved.")
            return jsonify({"success": True, "payment_id": payment_id, "warning": "Project not found but payment recorded."})

        row_idx = col_values.index(project_id) + 1
        headers = projects_ws.row_values(1)
        row_data = projects_ws.row_values(row_idx)

        # Calculate Remaining
        total_col_idx = headers.index('total_amount') + 1 if 'total_amount' in headers else -1
        if total_col_idx == -1:
             total_col_idx = headers.index('Total Amount') + 1 if 'Total Amount' in headers else -1

        total_amount = 0.0
        if total_col_idx != -1:
            try:
                total_val_str = row_data[total_col_idx-1] if len(row_data) >= total_col_idx else "0"
                total_amount = float(str(total_val_str).replace(',', ''))
            except ValueError:
                total_amount = 0.0

        remaining_amount = total_amount - total_paid_for_project

        # Determine Status
        if total_paid_for_project == 0:
            payment_status = "unpaid"
        elif 0 < total_paid_for_project < total_amount:
            payment_status = "partial"
        else:
            payment_status = "paid"

        # Perform cell updates safely
        def safe_update(col_name, val):
            if col_name in headers:
                idx = headers.index(col_name) + 1
                projects_ws.update_cell(row_idx, idx, val)

        safe_update('advance_paid', total_paid_for_project)
        safe_update('remaining_amount', remaining_amount)
        safe_update('payment_status', payment_status)
        safe_update('timestamp', timestamp)

        # Append to notes for backward compatibility
        if 'notes' in headers:
            notes_idx = headers.index('notes') + 1
            existing_notes = row_data[notes_idx-1] if len(row_data) >= notes_idx else ""
            new_notes = existing_notes + f" | [PAYMENT {timestamp}] +₹{new_amount} via {payment_type}"
            projects_ws.update_cell(row_idx, notes_idx, new_notes)

        print(f"✅ [PAYMENTS] Project {project_id} updated: Paid={total_paid_for_project}, Rem={remaining_amount}, Status={payment_status}")
        return jsonify({"success": True, "payment_id": payment_id})

    except Exception as e:
        print(f"❌ [PAYMENTS ERROR]: Failed to update Project {project_id} after successful payment {payment_id}. Error: {e}")
        return jsonify({"success": True, "payment_id": payment_id, "warning": "Payment recorded, but Project update failed."})
