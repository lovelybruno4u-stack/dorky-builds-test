import os
import json
import random
import string
import csv
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import time
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from services.sheets_service import (
    init_google_client, get_worksheet, get_orders_sheet, get_payments_sheet,
    get_admin_logs_sheet, get_banner_sheet, get_settings_sheet, get_coupons_sheet,
    get_launch_tracker_sheet, SHEET_CONNECTED
)
from utils.logger import log_api_hit, write_admin_log

from routes.orders import orders_bp
from routes.admin import admin_bp
from routes.payments import payments_bp

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dorky_builds_super_secret_dev_key")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB max upload size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.register_blueprint(orders_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(payments_bp)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

DEBUG_MODE = os.environ.get("DEBUG", "true").lower() == "true"

def generate_booking_id():
    return "DB-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_orders_sheet():
    global orders_sheet
    if SHEET_CONNECTED and orders_sheet is not None:
        return orders_sheet
    raise Exception("Database disconnected or Orders sheet missing")

def get_banner_sheet():
    global banner_sheet
    if SHEET_CONNECTED and banner_sheet is not None:
        return banner_sheet
    raise Exception("Database disconnected or Banner sheet missing")

def get_settings_sheet():
    global settings_sheet
    if SHEET_CONNECTED and settings_sheet is not None:
        return settings_sheet
    raise Exception("Database disconnected or Settings sheet missing")

def get_coupons_sheet():
    global coupons_sheet
    if SHEET_CONNECTED and coupons_sheet is not None:
        return coupons_sheet
    raise Exception("Database disconnected or Coupons sheet missing")

def get_logs_sheet():
    global logs_sheet
    if SHEET_CONNECTED and logs_sheet is not None:
        return logs_sheet
    raise Exception("Database disconnected or Logs sheet missing")


def log_admin_action(action, details):
    if SHEET_CONNECTED:
        try:
            logs_sheet = get_logs_sheet()
            timestamp = datetime.utcnow().isoformat() + "Z"
            logs_sheet.append_row([action, details, timestamp])
        except Exception as e:
            print(f"❌ [LOGS] Failed to write to Admin_Logs: {e}")


@app.before_request
def require_login():
    protected_routes = ['/dashboard', '/requirements']
    if request.path in protected_routes and 'user_id' not in session:
        return redirect(url_for('login'))


@app.route('/robots.txt')
def static_from_root():
    return "User-agent: *\nDisallow:", 200, {'Content-Type': 'text/plain'}

@app.route('/favicon.ico')
def favicon():
    return "", 204


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
            print("⚠️ [SIGNUP] Database offline. Mocking login for UI debug.")
            import uuid
            session['user_id'] = str(uuid.uuid4())
            session['email'] = email
            session['name'] = name
            return redirect(url_for('requirements'))

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

def get_google_sheet_records():
    if SHEET_CONNECTED:
        try:
            worksheet = get_orders_sheet()
            records = worksheet.get_all_records()
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
    fallback_banner = {"banner_text": "Welcome to Dorky Builds", "active": True}
    try:
        banner_sheet = get_banner_sheet()
        records = banner_sheet.get_all_records()
        if records:
            banner = records[0]
            if str(banner.get('active', '')).upper() == 'TRUE':
                return jsonify({"status": "success", "banner": banner})
    except Exception as e:
        print(f"❌ [BANNER] Fallback used. Error: {e}")
        return jsonify({"status": "success", "banner": fallback_banner})
    return jsonify({"status": "success", "banner": fallback_banner})

@app.route('/api/settings', methods=['GET'])
def api_settings():
    fallback_settings = {"SITE_MODE": "LIVE", "MIN_ADVANCE": "10"}
    try:
        settings_sheet = get_settings_sheet()
        records = settings_sheet.get_all_records()
        settings_dict = {str(r.get('setting_name')).strip(): str(r.get('value')).strip() for r in records if r.get('setting_name')}
        return jsonify({"status": "success", "settings": settings_dict})
    except Exception as e:
        print(f"❌ [SETTINGS] Fallback used. Error: {e}")
        return jsonify({"status": "success", "settings": fallback_settings})

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



@app.route('/api/approve/<booking_id>', methods=['POST'])
def api_approve(booking_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    user_email = session.get('email') or session.get('user_email')

    if not booking_id:
        return jsonify({"status": "error", "message": "Order ID required"}), 400

    current_time = datetime.utcnow().isoformat() + "Z"

    try:
        worksheet = get_orders_sheet()
        col_values = worksheet.col_values(1)
        if booking_id in col_values:
            row_idx = col_values.index(booking_id) + 1
            row_data = worksheet.row_values(row_idx)
            headers = worksheet.row_values(1)

            email_col_idx = headers.index('Email') + 1
            status_col_idx = headers.index('Status') + 1
            ts_col_idx = headers.index('Timestamp') + 1

            # Verify ownership
            stored_email = row_data[email_col_idx-1] if len(row_data) >= email_col_idx else ""

            if str(stored_email).strip().lower() == str(user_email).strip().lower():
                worksheet.update_cell(row_idx, status_col_idx, 'Completed')
                worksheet.update_cell(row_idx, ts_col_idx, current_time)
                print(f"✅ [SHEETS] Successfully approved order {booking_id} by {user_email}.")
                return jsonify({"status": "success", "message": "Project approved successfully."})
            else:
                print(f"❌ [AUTH] Unauthorized approval attempt on {booking_id} by {user_email}")
                return jsonify({"status": "error", "message": "Unauthorized"}), 403
        else:
            return jsonify({"status": "error", "message": "Order not found"}), 404
    except Exception as e:
        print(f"❌ [SHEETS] Google Sheets approval error: {e}")
        if DEBUG_MODE:
            print(f"🐛 [DEBUG] Exception details: {repr(e)}")
        return jsonify({"status": "error", "message": "Failed to approve project."}), 500

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
            orders_sheet = get_orders_sheet()
            records = orders_sheet.get_all_records()
            orders = list(reversed(records))

            coupons_sheet = get_coupons_sheet()
            coupons = coupons_sheet.get_all_records()

            banner_sheet = get_banner_sheet()
            banners = banner_sheet.get_all_records()
            if banners:
                banner = banners[0]
                banner['active'] = str(banner.get('active', '')).upper() == 'TRUE'

            settings_sheet = get_settings_sheet()
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
        banner_sheet = get_banner_sheet()
    except Exception:
        banner_sheet = None
    if not SHEET_CONNECTED or banner_sheet is None:
        print('❌ [ADMIN] Cannot update banner. Sheet disconnected.')
        return redirect(url_for('admin_dashboard'))
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
        settings_sheet = get_settings_sheet()
    except Exception:
        settings_sheet = None
    if not SHEET_CONNECTED or settings_sheet is None:
        print('❌ [ADMIN] Cannot update settings. Sheet disconnected.')
        return redirect(url_for('admin_dashboard'))
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
        coupons_sheet = get_coupons_sheet()
    except Exception:
        coupons_sheet = None
    if not SHEET_CONNECTED or coupons_sheet is None:
        print('❌ [ADMIN] Cannot add coupon. Sheet disconnected.')
        return redirect(url_for('admin_dashboard'))
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

# --- LAUNCH TRACKER SYSTEM ---
@app.route('/internal-dashboard-7843')
def internal_dashboard():
    try:
        launch_tracker_sheet = get_launch_tracker_sheet()
    except Exception:
        launch_tracker_sheet = None
    if not SHEET_CONNECTED or launch_tracker_sheet is None:
        return "System Offline: Database is disconnected.", 500

    try:
        # Fetch all records
        records = launch_tracker_sheet.get_all_records()

        # Group by category
        categories = {}
        total_features = len(records)
        working_count = 0

        for record in records:
            cat = record.get('Category', 'UNCATEGORIZED')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(record)

            if record.get('Status') == 'Working':
                working_count += 1

        progress = int((working_count / total_features * 100)) if total_features > 0 else 0

        return render_template('internal_dashboard.html', categories=categories, progress=progress, total=total_features, working=working_count)
    except Exception as e:
        print(f"❌ [LAUNCH TRACKER] Error fetching data: {e}")
        return f"System Error: {e}", 500

@app.route('/api/internal/launch-tracker/update', methods=['POST'])
def update_launch_tracker():
    try:
        launch_tracker_sheet = get_launch_tracker_sheet()
    except Exception:
        launch_tracker_sheet = None
    if not SHEET_CONNECTED or launch_tracker_sheet is None:
        return jsonify({"status": "error", "message": "Database disconnected"}), 500

    data = request.json or {}
    feature_name = data.get('feature_name')
    status = data.get('status')
    notes = data.get('notes')

    if not feature_name:
        return jsonify({"status": "error", "message": "Feature Name required"}), 400

    try:
        col_values = launch_tracker_sheet.col_values(1)
        if feature_name in col_values:
            row_idx = col_values.index(feature_name) + 1
            headers = launch_tracker_sheet.row_values(1)

            current_time = datetime.utcnow().isoformat() + "Z"

            if 'Status' in headers and status is not None:
                status_idx = headers.index('Status') + 1
                launch_tracker_sheet.update_cell(row_idx, status_idx, status)

            if 'Notes' in headers and notes is not None:
                notes_idx = headers.index('Notes') + 1
                launch_tracker_sheet.update_cell(row_idx, notes_idx, notes)

            if 'Last Updated Timestamp' in headers:
                time_idx = headers.index('Last Updated Timestamp') + 1
                launch_tracker_sheet.update_cell(row_idx, time_idx, current_time)

            print(f"✅ [LAUNCH TRACKER] Updated '{feature_name}' to '{status}'")
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Feature not found"}), 404

    except Exception as e:
        print(f"❌ [LAUNCH TRACKER] Update error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
