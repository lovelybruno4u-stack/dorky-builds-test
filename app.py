import os
import json
import random
import string
import csv
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import gspread
import time
from google.oauth2.service_account import Credentials
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dorky_builds_super_secret_dev_key")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB max upload size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

DEBUG_MODE = os.environ.get("DEBUG", "true").lower() == "true"

SHEET_CONNECTED = False
orders_sheet = None
payments_sheet = None
preview_sheet = None
order_status_sheet = None
users_sheet = None
coupons_sheet = None
banner_sheet = None
settings_sheet = None
logs_sheet = None

def init_google_sheets():
    global orders_sheet, users_sheet, coupons_sheet, banner_sheet, settings_sheet, logs_sheet, SHEET_CONNECTED

    creds_json_str = os.environ.get("GOOGLE_CREDS_JSON", "").strip()
    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "").strip()

    # 1. SHEET ID HARDENING & ENV VALIDATION
    if not creds_json_str:
        print("❌ [FATAL] GOOGLE_CREDS_JSON is missing. System will NOT save data to Google Sheets.")
        SHEET_CONNECTED = False
        return

    if not sheet_id:
        print("❌ [FATAL] GOOGLE_SHEET_ID is missing. System will NOT save data to Google Sheets.")
        SHEET_CONNECTED = False
        return

    if len(sheet_id) < 20 or " " in sheet_id:
        print(f"❌ [FATAL] Invalid GOOGLE_SHEET_ID format: {repr(sheet_id)}")
        SHEET_CONNECTED = False
        return

    print(f"✅ [DEBUG] SHEET_ID format validated: {repr(sheet_id)}")

    # 2. GOOGLE AUTH FIX
    try:
        import json
        creds_dict = json.loads(creds_json_str)
    except json.JSONDecodeError as e:
        print(f"❌ [FATAL] GOOGLE_CREDS_JSON is not valid JSON: {e}")
        SHEET_CONNECTED = False
        return

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    try:
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        print("✅ [AUTH] Google Auth Service Account credentials verified successfully.")
    except Exception as e:
        print(f"❌ [FATAL] Google Auth failed. Check GOOGLE_CREDS_JSON permissions/format: {e}")
        SHEET_CONNECTED = False
        return

    # 3. CONNECTION FLOW IMPROVEMENT (RETRY LOGIC & 404/403 HANDLING)
    import time
    max_retries = 3
    spreadsheet = None

    for attempt in range(1, max_retries + 1):
        try:
            print(f"⏳ [CONNECT] Attempting to open spreadsheet (Attempt {attempt}/{max_retries})...")
            spreadsheet = client.open_by_key(sheet_id)
            print("✅ [CONNECT] Spreadsheet opened successfully.")
            break
        except gspread.exceptions.APIError as e:
            error_msg = str(e)
            if "403" in error_msg or "PERMISSION_DENIED" in error_msg:
                print(f"❌ [API_ERROR 403] Permission Denied or Google Sheets API disabled. Ensure the Google Sheets API is enabled in Google Cloud Console and the Service Account has Editor access.")
                break # Non-recoverable without admin action
            elif "404" in error_msg or "NOT_FOUND" in error_msg:
                print(f"❌ [API_ERROR 404] Spreadsheet Not Found. The SHEET_ID is wrong, OR the Service Account ({creds_dict.get('client_email')}) has not been invited to edit the sheet.")
                break # Non-recoverable without admin action
            else:
                print(f"⚠️ [API_ERROR] Unexpected API error: {e}")
                time.sleep(2 ** attempt)
        except Exception as e:
            print(f"⚠️ [CONNECT] Failed to open spreadsheet on attempt {attempt}: {e}")
            time.sleep(2 ** attempt)

    if not spreadsheet:
        print("❌ [FATAL] Failed to connect to spreadsheet after retries. Entering failsafe mode.")
        SHEET_CONNECTED = False
        return

    # Helper function to get or create worksheets safely
    def get_or_create_worksheet(title, rows="1000", cols="20"):
        try:
            return spreadsheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            print(f"⏳ [WORKSHEET] '{title}' not found. Creating...")
            if title == "Orders" and len(spreadsheet.worksheets()) == 1 and spreadsheet.sheet1.title != "Orders":
                ws = spreadsheet.sheet1
                ws.update_title("Orders")
                return ws
            return spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)

    try:
        # 1. ARCHIVE OLD SYSTEM
        try:
            old_orders = spreadsheet.worksheet("Orders")
            print("⏳ [ARCHIVE] Archiving old 'Orders' sheet to 'OLD_ORDERS_BACKUP'...")
            old_orders.update_title("OLD_ORDERS_BACKUP")
        except gspread.exceptions.WorksheetNotFound:
            pass # No old orders sheet to archive

        # 2. CREATE MODULAR SHEETS
        orders_sheet = get_or_create_worksheet("ORDERS")
        payments_sheet = get_or_create_worksheet("PAYMENTS")
        preview_sheet = get_or_create_worksheet("PREVIEW")
        order_status_sheet = get_or_create_worksheet("ORDER_STATUS")

        users_sheet = get_or_create_worksheet("Users")
        coupons_sheet = get_or_create_worksheet("Coupons")
        banner_sheet = get_or_create_worksheet("Banner_Control")
        settings_sheet = get_or_create_worksheet("Settings")
        logs_sheet = get_or_create_worksheet("Admin_Logs")
    except Exception as e:
        print(f"❌ [FATAL] Error configuring worksheets: {e}")
        SHEET_CONNECTED = False
        return

    # 5. AUTO-CREATE HEADERS & DEFAULTS
    SHEET_CONNECTED = True

    def ensure_headers(ws, headers, default_data=None):
        try:
            existing = ws.row_values(1)
            if existing != headers:
                print(f"⚠️ [SHEETS] {ws.title} headers do not match. Fixing...")
                ws.insert_row(headers, 1)
                if default_data and len(ws.get_all_values()) <= 1:
                    for row in default_data:
                        ws.append_row(row)
        except Exception as e:
            print(f"⚠️ [SHEETS] {ws.title} empty. Initializing headers...")
            ws.insert_row(headers, 1)
            if default_data:
                for row in default_data:
                    ws.append_row(row)

    ensure_headers(orders_sheet, [
        "booking_id", "user_id", "name", "email", "phone",
        "project_type", "plan", "delivery_speed", "features",
        "created_at", "last_updated"
    ])

    ensure_headers(payments_sheet, [
        "booking_id", "total_price", "advance_paid", "remaining_amount",
        "payment_status", "upi_ref_id", "screenshot_url",
        "discount_amount", "final_price", "coupon_applied"
    ])

    ensure_headers(preview_sheet, [
        "booking_id", "preview_link", "preview_status", "approved", "feedback"
    ])

    ensure_headers(order_status_sheet, [
        "booking_id", "order_status", "last_updated"
    ])

    ensure_headers(users_sheet, ["uid", "name", "email", "password_hash", "created_at"])

    ensure_headers(coupons_sheet, [
        "coupon_code", "discount_type", "discount_value",
        "min_order_value", "expiry_date", "active"
    ], [["FIRST100", "flat", "100", "0", "2026-12-31", "TRUE"]])

    ensure_headers(banner_sheet, [
        "banner_text", "active", "duration_seconds", "background_color", "text_color"
    ], [["🔥 Use code FIRST100 and get ₹100 OFF!", "TRUE", "30", "#000000", "#00FF41"]])

    ensure_headers(settings_sheet, [
        "setting_name", "value"
    ], [
        ["UPI_ID", "bina.patil@axl"],
        ["MIN_ADVANCE", "10"],
        ["MAX_ADVANCE_PERCENT", "100"],
        ["SITE_MODE", "LIVE"]
    ])

    ensure_headers(logs_sheet, ["action", "details", "timestamp"])

    print("🚀 [READY] Google Sheets backend is fully configured and online.")

# Initialize on startup
try:
    init_google_sheets()
except Exception as e:
    print(f"❌ [CRITICAL] Unhandled exception during init_google_sheets: {e}")
    SHEET_CONNECTED = False

def generate_booking_id():
    return "DB-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def log_admin_action(action, details):
    if SHEET_CONNECTED and logs_sheet:
        try:
            timestamp = datetime.utcnow().isoformat() + "Z"
            logs_sheet.append_row([action, details, timestamp])
        except Exception as e:
            print(f"❌ [LOGS] Failed to write to Admin_Logs: {e}")


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
        # Mock session for testing
        session['user_id'] = 'test-uid-123'
        print("⚠️ [SUBMIT] Mocking session for testing purposes")

    data = request.form

    # Input validation
    required_fields = ['name', 'email', 'projectType', 'plan', 'upi_ref_id']
    for field in required_fields:
        if not data.get(field):
            print(f"❌ [VALIDATION] Missing required field: {field}")
            return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400

    # File upload handling
    screenshot_url = ""
    print(f"⏳ [UPLOAD] Processing file upload for user: {session.get('user_id')}")
    try:
        if 'screenshot' not in request.files:
            print("❌ [UPLOAD] No 'screenshot' key in request.files")
            return jsonify({"status": "error", "message": "Screenshot upload is required"}), 400

        file = request.files['screenshot']
        if file.filename == '':
            print("❌ [UPLOAD] Empty filename received")
            return jsonify({"status": "error", "message": "Screenshot file is empty"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_name = f"{int(time.time())}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)

            print(f"⏳ [UPLOAD] Saving file to: {file_path}")
            file.save(file_path)

            screenshot_url = f"/static/uploads/{unique_name}"
            print(f"✅ [UPLOAD] File saved successfully. URL: {screenshot_url}")
        else:
            print(f"❌ [UPLOAD] Invalid file type: {file.filename}")
            return jsonify({"status": "error", "message": "Invalid file type. Only PNG, JPG, JPEG allowed."}), 400
    except Exception as e:
        print(f"❌ [UPLOAD] Exception during file processing: {e}")
        return jsonify({"status": "error", "message": "File processing failed"}), 500

    user_id = session.get('user_id')
    booking_id = generate_booking_id()
    current_time = datetime.utcnow().isoformat() + "Z"

    # New Modualr Schema
    order_data = [
        booking_id,
        user_id,
        data.get('name', ''),
        data.get('email', ''),
        data.get('phone', ''),
        data.get('projectType', ''),
        data.get('plan', ''),
        data.get('deliverySpeed', ''),
        data.get('features', ''),
        current_time,
        current_time
    ]

    payment_data = [
        booking_id,
        data.get('total_price', '0'),
        data.get('advance_paid', '0'),
        data.get('remaining_amount', '0'),
        "PENDING",
        data.get('upi_ref_id', ''),
        screenshot_url,
        data.get('discount_amount', '0'),
        data.get('final_price', '0'),
        data.get('coupon_applied', '')
    ]

    preview_data = [
        booking_id,
        "",
        "NOT_READY",
        "NO",
        ""
    ]

    status_data = [
        booking_id,
        "CREATED",
        current_time
    ]

    print(f"✅ [SUBMIT] Received payload from User ID: {user_id}")
    if DEBUG_MODE:
        print(f"📦 [DEBUG] Incoming request payload: {data}")

    if SHEET_CONNECTED:
        try:
            print(f"⏳ [SHEETS] Writing booking {booking_id} to Google Sheets...")
            # Check for uniqueness in ORDERS sheet
            existing_records = orders_sheet.col_values(1)
            while booking_id in existing_records:
                print(f"⚠️ [COLLISION] Booking ID {booking_id} already exists. Regenerating...")
                booking_id = generate_booking_id()
                order_data[0] = booking_id
                payment_data[0] = booking_id
                preview_data[0] = booking_id
                status_data[0] = booking_id

            orders_sheet.append_row(order_data)
            payments_sheet.append_row(payment_data)
            preview_sheet.append_row(preview_data)
            order_status_sheet.append_row(status_data)

            print(f"✅ [SHEETS] Successfully wrote booking {booking_id} to all modular sheets.")
            log_admin_action("ORDER_CREATED", f"User {user_id} created order {booking_id}")

            return jsonify({
                "status": "success",
                "message": "Requirements submitted successfully.",
                "booking_id": booking_id
            })
        except Exception as e:
            print(f"❌ [SHEETS] Error writing booking {booking_id} to Google Sheets: {e}")
            if DEBUG_MODE:
                print(f"🐛 [DEBUG] Full Google Sheets exception: {repr(e)}")
            return jsonify({"status": "error", "message": "Database error while saving request."}), 500
    else:
        print(f"❌ [FATAL] SHEET_CONNECTED is False. System dropped order {booking_id}.")
        return jsonify({"status": "error", "message": "Database connection is offline. Cannot process order."}), 500

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

@app.route('/api/banner', methods=['GET'])
def api_banner():
    if not SHEET_CONNECTED or not banner_sheet:
        return jsonify({"status": "error"}), 500
    try:
        records = banner_sheet.get_all_records()
        if records:
            # Assuming first row has the active banner
            banner = records[0]
            if str(banner.get('active', '')).upper() == 'TRUE':
                return jsonify({"status": "success", "banner": banner})
    except Exception as e:
        print(f"❌ [BANNER] Error: {e}")
    return jsonify({"status": "success", "banner": None})

@app.route('/api/settings', methods=['GET'])
def api_settings():
    if not SHEET_CONNECTED or not settings_sheet:
        return jsonify({"status": "error"}), 500
    try:
        records = settings_sheet.get_all_records()
        settings_dict = {str(r.get('setting_name')).strip(): str(r.get('value')).strip() for r in records if r.get('setting_name')}
        return jsonify({"status": "success", "settings": settings_dict})
    except Exception as e:
        print(f"❌ [SETTINGS] Error: {e}")
    return jsonify({"status": "error"}), 500

@app.route('/api/validate_coupon', methods=['POST'])
def validate_coupon():
    data = request.json or {}
    code = data.get('code', '').strip().upper()
    order_value = float(data.get('order_value', 0))

    if not code:
        return jsonify({"status": "error", "message": "No code provided"}), 400

    if not SHEET_CONNECTED or not coupons_sheet:
        return jsonify({"status": "error", "message": "Database disconnected"}), 500

    try:
        records = coupons_sheet.get_all_records()
        for r in records:
            if str(r.get('coupon_code', '')).strip().upper() == code:
                # Check if active
                if str(r.get('active', '')).upper() != 'TRUE':
                    return jsonify({"status": "error", "message": "Coupon is inactive"}), 400

                # Check expiry
                expiry_str = r.get('expiry_date', '').strip()
                if expiry_str:
                    try:
                        expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                        if datetime.now().date() > expiry_date:
                            return jsonify({"status": "error", "message": "Coupon has expired"}), 400
                    except Exception:
                        pass # Ignore malformed dates

                # Check min order
                min_order = float(r.get('min_order_value', 0) or 0)
                if order_value < min_order:
                    return jsonify({"status": "error", "message": f"Minimum order value is ₹{min_order}"}), 400

                # Success
                return jsonify({
                    "status": "success",
                    "coupon": {
                        "code": code,
                        "type": r.get('discount_type', 'flat').lower(),
                        "value": float(r.get('discount_value', 0))
                    }
                })
        return jsonify({"status": "error", "message": "Invalid coupon code"}), 404
    except Exception as e:
        print(f"❌ [COUPON] Error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/api/track/<booking_id>', methods=['GET'])
def api_track(booking_id):
    booking_id = booking_id.strip().upper()
    if not booking_id:
        return jsonify({"status": "error", "message": "Booking ID required"}), 400

    if not SHEET_CONNECTED:
        return jsonify({"status": "error", "message": "Database is currently disconnected"}), 500

    order = None
    records = get_google_sheet_records()
    for r in records:
        # Normalize stored ID just in case
        stored_id = str(r.get('booking_id', '')).strip().upper()
        if stored_id == booking_id:
            order = r
            break

    if order:
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
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "dorkybuildsadmin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Poorvi@2011")

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
    coupons = []
    banner = {}
    settings = {}

    if SHEET_CONNECTED:
        try:
            records = orders_sheet.get_all_records()
            orders = list(reversed(records))

            coupons = coupons_sheet.get_all_records()

            banners = banner_sheet.get_all_records()
            if banners:
                banner = banners[0]
                # Normalize 'active' to boolean for template logic
                banner['active'] = str(banner.get('active', '')).upper() == 'TRUE'

            sett = settings_sheet.get_all_records()
            settings = {str(r.get('setting_name')).strip(): str(r.get('value')).strip() for r in sett if r.get('setting_name')}
        except Exception as e:
            print(f"❌ [ADMIN] Dashboard data fetch error: {e}")

    return render_template('admin_dashboard.html', orders=orders, coupons=coupons, banner=banner, settings=settings)


@app.route('/admin/update_banner', methods=['POST'])
def admin_update_banner():
    if not session.get('is_admin'):
        return jsonify({"status": "error"}), 403
    data = request.form
    try:
        # Assuming banner is always row 2
        banner_sheet.update_cell(2, 1, data.get('banner_text', ''))
        banner_sheet.update_cell(2, 2, 'TRUE' if data.get('active') else 'FALSE')
        banner_sheet.update_cell(2, 3, data.get('duration_seconds', '30'))
        banner_sheet.update_cell(2, 4, data.get('background_color', '#000000'))
        banner_sheet.update_cell(2, 5, data.get('text_color', '#00FF41'))
        log_admin_action("BANNER_UPDATE", "Admin updated banner settings")
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        print(f"❌ [ADMIN] Banner update failed: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_settings', methods=['POST'])
def admin_update_settings():
    if not session.get('is_admin'):
        return jsonify({"status": "error"}), 403
    data = request.form
    try:
        # Need to iterate and update or just clear and rewrite settings
        # Faster: just update matching keys
        records = settings_sheet.get_all_records()
        for idx, r in enumerate(records):
            key = r.get('setting_name')
            if key in data:
                settings_sheet.update_cell(idx + 2, 2, data[key])
        log_admin_action("SETTINGS_UPDATE", "Admin updated global settings")
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        print(f"❌ [ADMIN] Settings update failed: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_coupon', methods=['POST'])
def admin_add_coupon():
    if not session.get('is_admin'):
        return jsonify({"status": "error"}), 403
    data = request.form
    try:
        coupons_sheet.append_row([
            data.get('coupon_code', '').upper().strip(),
            data.get('discount_type', 'flat'),
            data.get('discount_value', '0'),
            data.get('min_order_value', '0'),
            data.get('expiry_date', ''),
            'TRUE' if data.get('active') else 'FALSE'
        ])
        log_admin_action("COUPON_ADDED", f"Admin added coupon {data.get('coupon_code')}")
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        print(f"❌ [ADMIN] Coupon add failed: {e}")
        return redirect(url_for('admin_dashboard'))

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
