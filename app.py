import os
import json
import random
import string
import csv
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dorky_builds_super_secret_dev_key")

DEBUG_MODE = os.environ.get("DEBUG", "true").lower() == "true"

SHEET_CONNECTED = False
orders_sheet = None
users_sheet = None

def init_google_sheets():
    global orders_sheet, users_sheet, SHEET_CONNECTED

    creds_json_str = os.environ.get("GOOGLE_CREDS_JSON")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")

    if not creds_json_str or not sheet_id:
        print("❌ [FATAL] Google Sheets connection failed: GOOGLE_CREDS_JSON or GOOGLE_SHEET_ID not set. System will NOT save orders!")
        return

    try:
        creds_dict = json.loads(creds_json_str)
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        try:
            spreadsheet = client.open_by_key(sheet_id)
            orders_sheet = spreadsheet.worksheet("Orders")
        except Exception as e:
            if "WorksheetNotFound" in str(e):
                orders_sheet = spreadsheet.sheet1
                orders_sheet.update_title("Orders")
            elif "404" in str(e):
                print(f"❌ [FATAL] Google Sheets connection failed: 404 Not Found. Make sure you shared the sheet ({sheet_id}) with the service account email! Error: {e}")
                return
            else:
                print(f"❌ [FATAL] Google Sheets connection failed during open_by_key: {e}")
                return

        try:
            users_sheet = spreadsheet.worksheet("Users")
        except Exception as e:
            if "WorksheetNotFound" in str(e):
                users_sheet = spreadsheet.add_worksheet(title="Users", rows="1000", cols="10")
            else:
                print(f"❌ [FATAL] Error accessing/creating Users sheet: {e}")
                return

        SHEET_CONNECTED = True

        # Auto create headers for Orders
        order_headers = [
            "booking_id", "user_id", "name", "email", "phone",
            "project_type", "plan", "delivery_speed", "features",
            "budget", "timeline",
            "status", "preview_link",
            "payment_status", "approved", "created_at", "last_updated"
        ]
        try:
            existing_orders = orders_sheet.row_values(1)
            if existing_orders != order_headers:
                print("⚠️ [SHEETS] Orders headers do not match. Inserting correct headers...")
                orders_sheet.insert_row(order_headers, 1)
        except Exception as e:
            print("⚠️ [SHEETS] Orders sheet is empty. Initializing headers...")
            orders_sheet.insert_row(order_headers, 1)

        # Auto create headers for Users
        user_headers = ["uid", "name", "email", "password_hash", "created_at"]
        try:
            existing_users = users_sheet.row_values(1)
            if existing_users != user_headers:
                print("⚠️ [SHEETS] Users headers do not match. Inserting correct headers...")
                users_sheet.insert_row(user_headers, 1)
        except Exception as e:
            print("⚠️ [SHEETS] Users sheet is empty. Initializing headers...")
            users_sheet.insert_row(user_headers, 1)

        print("✅ [SHEETS] Successfully connected to Google Sheets and verified headers.")
    except Exception as e:
        print(f"❌ [FATAL] Google Sheets connection failed: {e}. System will NOT save data!")

# Initialize on startup
init_google_sheets()

def generate_booking_id():
    return "DB-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.before_request
def require_login():
    protected_routes = ['/dashboard', '/requirements']
    if request.path in protected_routes and 'user_id' not in session:
        return redirect(url_for('login'))

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

# --- USER AUTHENTICATION ---

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or not email or not password:
            print(f"❌ [SIGNUP] Missing required fields for {email}")
            return render_template('signup.html', error="All fields are required")

        if not SHEET_CONNECTED:
            print("❌ [SIGNUP] Database offline. Cannot register user.")
            return render_template('signup.html', error="Database is currently disconnected. Please try again later.")

        try:
            # Check if email exists
            records = users_sheet.get_all_records()
            for r in records:
                if r.get('email', '').lower() == email:
                    print(f"❌ [SIGNUP] Registration failed: Email {email} already exists.")
                    return render_template('signup.html', error="Email is already registered.")

            uid = str(uuid.uuid4())
            password_hash = generate_password_hash(password)
            current_time = datetime.utcnow().isoformat() + "Z"

            users_sheet.append_row([uid, name, email, password_hash, current_time])
            print(f"✅ [SIGNUP] User registered successfully: {email} (UID: {uid})")

            # Auto-login
            session['user_id'] = uid
            session['email'] = email
            session['name'] = name
            print(f"✅ [SESSION] Session created for {email}")

            return redirect(url_for('dashboard'))

        except Exception as e:
            print(f"❌ [SIGNUP] Error saving user to database: {e}")
            return render_template('signup.html', error="Internal server error during registration.")

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            print(f"❌ [LOGIN] Missing credentials for {email}")
            return render_template('login.html', error="Email and password required")

        if not SHEET_CONNECTED:
            print("❌ [LOGIN] Database offline. Cannot authenticate.")
            return render_template('login.html', error="Database is currently disconnected.")

        try:
            print(f"⏳ [LOGIN] Attempting login for {email}")
            records = users_sheet.get_all_records()
            user_found = False

            for r in records:
                if r.get('email', '').lower() == email:
                    user_found = True
                    stored_hash = r.get('password_hash')
                    if check_password_hash(stored_hash, password):
                        session['user_id'] = str(r.get('uid'))
                        session['email'] = email
                        session['name'] = r.get('name', '')
                        print(f"✅ [LOGIN] Success for {email} (UID: {session['user_id']})")
                        return redirect(url_for('dashboard'))
                    else:
                        print(f"❌ [LOGIN] Invalid password for {email}")
                        return render_template('login.html', error="Invalid email or password")

            if not user_found:
                print(f"❌ [LOGIN] Email not found: {email}")
                return render_template('login.html', error="Invalid email or password")

        except Exception as e:
            print(f"❌ [LOGIN] Error during authentication: {e}")
            return render_template('login.html', error="Internal server error during login.")

    return render_template('login.html')

@app.route('/logout')
def logout():
    email = session.get('email', 'Unknown')
    session.clear()
    print(f"✅ [LOGOUT] Session cleared for {email}")
    return redirect(url_for('login'))

# --- END USER AUTHENTICATION ---

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
    if 'user_id' not in session:
        print("❌ [SUBMIT] Unauthorized submission attempt (no session)")
        return jsonify({"status": "error", "message": "Unauthorized. Please log in."}), 401

    data = request.form

    # Input validation
    required_fields = ['name', 'email', 'projectType', 'plan']
    for field in required_fields:
        if not data.get(field):
            print(f"❌ [VALIDATION] Missing required field: {field}")
            return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400

    user_id = session.get('user_id')
    booking_id = generate_booking_id()
    current_time = datetime.utcnow().isoformat() + "Z"

    row_data = [
        booking_id,
        user_id,
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

    print(f"✅ [SUBMIT] Received payload from User ID: {user_id}")
    if DEBUG_MODE:
        print(f"📦 [DEBUG] Incoming request payload: {data}")

    if SHEET_CONNECTED:
        try:
            # Check for uniqueness
            existing_records = orders_sheet.col_values(1) # Column A: booking_id
            while booking_id in existing_records:
                print(f"⚠️ [COLLISION] Booking ID {booking_id} already exists. Regenerating...")
                booking_id = generate_booking_id()
                row_data[0] = booking_id

            orders_sheet.append_row(row_data)
            print(f"✅ [SHEETS] Successfully wrote booking {booking_id} to Orders sheet.")
        except Exception as e:
            print(f"❌ [SHEETS] Error writing booking {booking_id} to Google Sheets: {e}")
            if DEBUG_MODE:
                print(f"🐛 [DEBUG] Full Google Sheets exception: {repr(e)}")
            return jsonify({"status": "error", "message": "Database error while saving request."}), 500
    else:
        print(f"❌ [FATAL] SHEET_CONNECTED is False. System dropped order {booking_id}.")
        return jsonify({"status": "error", "message": "Database connection is offline. Cannot process order."}), 500

    return jsonify({
        "status": "success",
        "message": "Requirements submitted successfully.",
        "booking_id": booking_id
    })

def get_google_sheet_records():
    if SHEET_CONNECTED:
        try:
            records = orders_sheet.get_all_records()
            if DEBUG_MODE:
                print(f"📦 [DEBUG] Fetched {len(records)} records from Orders sheet.")
            return records
        except Exception as e:
            print(f"❌ [SHEETS] Google Sheets fetch error: {e}")
    else:
        print("❌ [SHEETS] Cannot fetch records: Database disconnected.")
    return []

@app.route('/api/track/<booking_id>', methods=['GET'])
def api_track(booking_id):
    if not booking_id:
        return jsonify({"status": "error", "message": "Booking ID required"}), 400

    if not SHEET_CONNECTED:
        return jsonify({"status": "error", "message": "Database is currently disconnected"}), 500

    order = None
    records = get_google_sheet_records()
    for r in records:
        if r.get('booking_id') == booking_id:
            order = r
            break

    if order:
        # Sanitize sensitive fields if necessary
        return jsonify({"status": "success", "order": order})
    else:
        return jsonify({"status": "error", "message": "INVALID BOOKING ID"}), 404

@app.route('/api/orders', methods=['GET'])
def api_orders():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    user_id = session.get('user_id')

    if not SHEET_CONNECTED:
        return jsonify({"status": "error", "message": "Database is currently disconnected"}), 500

    orders = []
    records = get_google_sheet_records()
    for r in records:
        # Filter by user_id
        if str(r.get('user_id')) == str(user_id):
            orders.append(r)

    return jsonify({"status": "success", "orders": orders})

@app.route('/api/approve/<booking_id>', methods=['POST'])
def api_approve(booking_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    user_id = session.get('user_id')

    if not booking_id:
        return jsonify({"status": "error", "message": "Booking ID required"}), 400

    current_time = datetime.utcnow().isoformat() + "Z"

    if SHEET_CONNECTED:
        try:
            cell = orders_sheet.find(booking_id)
            if cell:
                row_idx = cell.row
                row_data = orders_sheet.row_values(row_idx)
                headers = orders_sheet.row_values(1)

                user_id_col_idx = headers.index('user_id') + 1
                status_col_idx = headers.index('status') + 1
                approved_col_idx = headers.index('approved') + 1
                last_updated_col_idx = headers.index('last_updated') + 1

                if str(row_data[user_id_col_idx-1]) == str(user_id):
                    orders_sheet.update_cell(row_idx, status_col_idx, 'APPROVED')
                    orders_sheet.update_cell(row_idx, approved_col_idx, 'YES')
                    orders_sheet.update_cell(row_idx, last_updated_col_idx, current_time)
                    print(f"✅ [SHEETS] Successfully approved booking {booking_id} by User {user_id}.")
                    return jsonify({"status": "success", "message": "Project approved successfully."})
                else:
                    print(f"❌ [AUTH] Unauthorized approval attempt on {booking_id} by {user_id}")
                    return jsonify({"status": "error", "message": "Unauthorized"}), 403
            else:
                return jsonify({"status": "error", "message": "Order not found"}), 404
        except Exception as e:
            print(f"❌ [SHEETS] Google Sheets approval error: {e}")
            if DEBUG_MODE:
                print(f"🐛 [DEBUG] Exception details: {repr(e)}")
            return jsonify({"status": "error", "message": "Failed to approve project."}), 500
    else:
        return jsonify({"status": "error", "message": "Database disconnected."}), 500

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

    orders = []
    if SHEET_CONNECTED:
        records = get_google_sheet_records()
        orders = list(reversed(records))

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

    current_time = datetime.utcnow().isoformat() + "Z"
    updates['last_updated'] = current_time

    if SHEET_CONNECTED:
        try:
            cell = orders_sheet.find(booking_id)
            if cell:
                row_idx = cell.row
                headers = orders_sheet.row_values(1)

                for key, value in updates.items():
                    col_idx = headers.index(key) + 1
                    orders_sheet.update_cell(row_idx, col_idx, value)

                print(f"✅ [ADMIN] Updated order {booking_id}: {updates}")
                return jsonify({"status": "success", "message": "Order updated successfully."})
            else:
                return jsonify({"status": "error", "message": "Order not found"}), 404
        except Exception as e:
            print(f"❌ [ADMIN] Google Sheets update error: {e}")
            return jsonify({"status": "error", "message": "Failed to update order."}), 500
    else:
        return jsonify({"status": "error", "message": "Database disconnected."}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
