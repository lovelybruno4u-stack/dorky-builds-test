import os
import json
import random
import string
import csv
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dorky_builds_super_secret_dev_key")

# Try to set up Google Sheets using ENV VARIABLES
SHEET_CONNECTED = False
sheet = None

def init_google_sheets():
    global sheet, SHEET_CONNECTED

    creds_json_str = os.environ.get("GOOGLE_CREDS_JSON")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")

    if not creds_json_str or not sheet_id:
        print("❌ Google Sheets connection failed: GOOGLE_CREDS_JSON or GOOGLE_SHEET_ID not set. Using degraded mode (CSV).")
        return

    try:
        import json
        creds_dict = json.loads(creds_json_str)
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        try:
            sheet = client.open_by_key(sheet_id).sheet1
        except Exception as e:
            if "404" in str(e):
                print(f"❌ Google Sheets connection failed: 404 Not Found. Make sure you shared the sheet ({sheet_id}) with the service account email! Error: {e}")
            else:
                print(f"❌ Google Sheets connection failed during open_by_key: {e}")
            return

        SHEET_CONNECTED = True

        # Auto create headers including UID and displayName
        headers = [
            "booking_id", "uid", "name", "email", "phone",
            "project_type", "plan", "delivery_speed", "features",
            "budget", "timeline",
            "status", "preview_link",
            "payment_status", "approved", "created_at", "last_updated"
        ]
        try:
            existing = sheet.row_values(1)
            if existing != headers:
                sheet.insert_row(headers, 1)
        except Exception as e:
            # If sheet is totally empty, row_values might fail
            sheet.insert_row(headers, 1)

        print("✅ Successfully connected to Google Sheets and verified headers.")
    except Exception as e:
        print(f"❌ Google Sheets connection failed: {e}. Using degraded mode (CSV).")
def generate_booking_id():
    return "DB-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/workbench')
def workbench():
    return render_template('workbench.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/requirements')
def requirements():
    return render_template('requirements.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/track')
def track():
    return render_template('track.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/contact-submit', methods=['POST'])
def contact_submit():
    data = request.form
    return jsonify({"status": "success", "message": "Message received. Initiating response protocol..."})

@app.route('/apply', methods=['POST'])
def apply():
    data = request.form
    return jsonify({"status": "success", "message": "Application accepted. Evaluating credentials..."})

@app.route('/submit-requirements', methods=['POST'])
def submit_requirements():
    data = request.form

    # Input validation
    required_fields = ['name', 'email', 'projectType', 'plan']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400

    booking_id = generate_booking_id()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    uid = data.get('uid', 'anonymous')
    row_data = [
        booking_id,
        uid,
        data.get('name', ''),
        data.get('email', ''),
        data.get('phone', ''),
        data.get('projectType', ''),
        data.get('plan', ''),
        data.get('deliverySpeed', ''),
        data.get('features', ''),
        data.get('budget', ''),
        data.get('timeline', ''),
        "REQUESTED",    # status
        "",             # preview_link
        "PENDING",      # payment_status
        "NO",           # approved
        current_time,   # created_at
        current_time    # last_updated
    ]

    print(f"📦 [SUBMIT] Incoming payload for {data.get('email')}: {data}")

    if SHEET_CONNECTED:
        try:
            sheet.append_row(row_data)
            print(f"✅ [SHEETS] Successfully wrote booking {booking_id} to Google Sheets.")
        except Exception as e:
            print(f"❌ [SHEETS] Error writing booking {booking_id} to Google Sheets: {e}")
            return jsonify({"status": "error", "message": "Database error while saving request."}), 500
    else:
        print(f"⚠️ [CSV FALLBACK] SHEET_CONNECTED is False. Writing booking {booking_id} to local CSV.")

    # Save locally to CSV fallback
    csv_file = 'leads.csv'
    file_exists = os.path.isfile(csv_file)
    try:
        with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["booking_id", "uid", "name", "email", "phone", "project_type", "plan", "delivery_speed", "features", "budget", "timeline", "status", "preview_link", "payment_status", "approved", "created_at", "last_updated"])
            writer.writerow(row_data)
    except Exception as e:
        print(f"Error saving lead locally: {e}")

    return jsonify({
        "status": "success",
        "message": "Requirements submitted successfully.",
        "booking_id": booking_id
    })

def fetch_orders_from_csv(email=None, booking_id=None):
    orders = []
    if not os.path.isfile('leads.csv'):
        return orders
    try:
        with open('leads.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if email and row.get('email') == email:
                    orders.append(row)
                elif booking_id and row.get('booking_id') == booking_id:
                    orders.append(row)
    except Exception as e:
        print(f"Error reading CSV: {e}")
    return orders

def update_csv_order(booking_id, updates):
    if not os.path.isfile('leads.csv'):
        return False
    try:
        rows = []
        updated = False
        with open('leads.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row.get('booking_id') == booking_id:
                    for k, v in updates.items():
                        row[k] = v
                    updated = True
                rows.append(row)
        if updated:
            with open('leads.csv', mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            return True
    except Exception as e:
        print(f"Error updating CSV: {e}")
    return False

def get_google_sheet_records():
    if SHEET_CONNECTED:
        try:
            return sheet.get_all_records()
        except Exception as e:
            print(f"Google Sheets fetch error: {e}")
    return []

@app.route('/api/track/<booking_id>', methods=['GET'])
def api_track(booking_id):
    if not booking_id:
        return jsonify({"status": "error", "message": "Booking ID required"}), 400

    order = None

    if SHEET_CONNECTED:
        records = get_google_sheet_records()
        for r in records:
            if r.get('booking_id') == booking_id:
                order = r
                break

    if not order:
        orders = fetch_orders_from_csv(booking_id=booking_id)
        if orders:
            order = orders[0]

    if order:
        return jsonify({"status": "success", "order": order})
    else:
        return jsonify({"status": "error", "message": "INVALID BOOKING ID"}), 404

@app.route('/api/orders', methods=['GET'])
def api_orders():
    email = request.args.get('email')
    if not email:
        return jsonify({"status": "error", "message": "Email is required"}), 400

    orders = []

    if SHEET_CONNECTED:
        records = get_google_sheet_records()
        for r in records:
            if r.get('email') == email:
                orders.append(r)
    else:
        orders = fetch_orders_from_csv(email=email)

    return jsonify({"status": "success", "orders": orders})

@app.route('/api/approve/<booking_id>', methods=['POST'])
def api_approve(booking_id):
    # In a real app, verify the user owns this booking_id via auth token check
    data = request.json or {}
    email = data.get('email') # Basic validation

    if not booking_id or not email:
        return jsonify({"status": "error", "message": "Booking ID and email required"}), 400

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    success = False

    if SHEET_CONNECTED:
        try:
            # Find the row index
            cell = sheet.find(booking_id)
            if cell:
                row_idx = cell.row
                # Verify email matches (prevent unauthorized approval)
                row_data = sheet.row_values(row_idx)
                # assuming email is column 3 (index 2)
                headers = sheet.row_values(1)
                email_col_idx = headers.index('email') + 1
                status_col_idx = headers.index('status') + 1
                approved_col_idx = headers.index('approved') + 1
                last_updated_col_idx = headers.index('last_updated') + 1

                if row_data[email_col_idx-1] == email:
                    sheet.update_cell(row_idx, status_col_idx, 'APPROVED')
                    sheet.update_cell(row_idx, approved_col_idx, 'YES')
                    sheet.update_cell(row_idx, last_updated_col_idx, current_time)
                    success = True
                else:
                    return jsonify({"status": "error", "message": "Unauthorized"}), 403
            else:
                return jsonify({"status": "error", "message": "Order not found"}), 404
        except Exception as e:
            print(f"Google Sheets update error: {e}")

    # Always update CSV as fallback/mirror
    csv_updated = update_csv_order(booking_id, {
        'status': 'APPROVED',
        'approved': 'YES',
        'last_updated': current_time
    })

    if success or csv_updated:
        return jsonify({"status": "success", "message": "Project approved successfully."})
    else:
        return jsonify({"status": "error", "message": "Failed to approve project."}), 500


# --- ADMIN AUTHENTICATION ---
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "DorkyAdmin2024!")

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Invalid credentials")

    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))

    # Fetch all orders to display
    orders = []
    if SHEET_CONNECTED:
        records = get_google_sheet_records()
        orders = list(reversed(records)) # Show newest first
    else:
        orders = list(reversed(fetch_orders_from_csv()))

    return render_template('admin_dashboard.html', orders=orders)

@app.route('/api/admin/update_order', methods=['POST'])
def api_admin_update_order():
    if not session.get('is_admin'):
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    data = request.json or {}
    booking_id = data.get('booking_id')

    if not booking_id:
        return jsonify({"status": "error", "message": "Booking ID required"}), 400

    updates = {}
    if 'status' in data: updates['status'] = data['status']
    if 'preview_link' in data: updates['preview_link'] = data['preview_link']
    if 'payment_status' in data: updates['payment_status'] = data['payment_status']

    if not updates:
        return jsonify({"status": "error", "message": "No updates provided"}), 400

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updates['last_updated'] = current_time

    success = False

    if SHEET_CONNECTED:
        try:
            cell = sheet.find(booking_id)
            if cell:
                row_idx = cell.row
                headers = sheet.row_values(1)

                for key, value in updates.items():
                    col_idx = headers.index(key) + 1
                    sheet.update_cell(row_idx, col_idx, value)

                success = True
            else:
                return jsonify({"status": "error", "message": "Order not found"}), 404
        except Exception as e:
            print(f"Google Sheets update error: {e}")

    # Fallback/Mirror
    csv_updated = update_csv_order(booking_id, updates)

    if success or csv_updated:
        return jsonify({"status": "success", "message": "Order updated successfully."})
    else:
        return jsonify({"status": "error", "message": "Failed to update order."}), 500

# --- END ADMIN ---

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
