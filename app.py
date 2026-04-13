import random
import string
import csv
import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Try to set up Google Sheets, but don't break if credentials are missing
SHEET_CONNECTED = False
try:
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("DorkyBuildsOrders").sheet1
    SHEET_CONNECTED = True
except Exception as e:
    print(f"Warning: Could not connect to Google Sheets. Using local CSV only. Error: {e}")

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
    booking_id = generate_booking_id()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Payload matching Google Sheets structure
    # Columns: booking_id, name, email, phone, project_type, plan, features, budget, timeline, status, preview_link, payment_status, created_at, delivery_speed
    # Note: delivery_speed is requested in prompt #6 but in #10 code snippet it's slightly different. We'll add it in.

    row_data = [
        booking_id,
        data.get('name', ''),
        data.get('email', ''),
        data.get('phone', ''),
        data.get('projectType', ''),
        data.get('plan', ''),
        data.get('features', ''),
        data.get('budget', ''),
        data.get('timeline', ''),
        "REQUESTED",    # status
        "",             # preview_link
        "PENDING",      # payment_status
        current_time,   # created_at
        data.get('deliverySpeed', '') # delivery_speed
    ]

    # Save to Google Sheets
    if SHEET_CONNECTED:
        try:
            sheet.append_row(row_data)
        except Exception as e:
            print(f"Error appending to Google Sheets: {e}")

    # Save locally to CSV (as database fallback)
    csv_file = 'leads.csv'
    file_exists = os.path.isfile(csv_file)
    try:
        with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['booking_id', 'name', 'email', 'phone', 'project_type', 'plan', 'features', 'budget', 'timeline', 'status', 'preview_link', 'payment_status', 'created_at', 'delivery_speed'])
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

def get_google_sheet_records():
    if SHEET_CONNECTED:
        try:
            return sheet.get_all_records()
        except Exception as e:
            print(f"Google Sheets fetch error: {e}")
    return []

@app.route('/api/track/<booking_id>', methods=['GET'])
def api_track(booking_id):
    order = None

    if SHEET_CONNECTED:
        records = get_google_sheet_records()
        for r in records:
            if r.get('booking_id') == booking_id:
                order = r
                break

    if not order:
        # Fallback to CSV
        orders = fetch_orders_from_csv(booking_id=booking_id)
        if orders:
            order = orders[0]

    if order:
        return jsonify({"status": "success", "order": order})
    else:
        return jsonify({"status": "error", "message": "Booking ID not found."}), 404

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
        # Fallback to CSV
        orders = fetch_orders_from_csv(email=email)

    return jsonify({"status": "success", "orders": orders})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
