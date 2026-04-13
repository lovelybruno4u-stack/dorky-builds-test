import random
import string
import csv
import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

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

    payload = {
        "booking_id": booking_id,
        "name": data.get('name', ''),
        "email": data.get('email', ''),
        "phone": data.get('phone', ''),
        "project_type": data.get('projectType', ''),
        "plan": data.get('plan', ''),
        "budget": data.get('budget', ''),
        "timeline": data.get('timeline', ''),
        "features": data.get('features', '')
    }

    # Mock Google Sheets Integration via webhook
    # In a real app, you would send this payload to a Zapier/Make webhook or directly to Google Sheets API
    try:
        # Example webhook URL (replace with actual if needed)
        # requests.post("https://hook.us1.make.com/xxxxxx", json=payload)
        pass
    except Exception as e:
        print(f"Webhook error: {e}")

    # Also save locally for verification/backup
    csv_file = 'leads.csv'
    file_exists = os.path.isfile(csv_file)
    try:
        with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Booking ID', 'Name', 'Email', 'Phone', 'Project Type', 'Plan', 'Budget', 'Timeline', 'Features'])
            writer.writerow([payload["booking_id"], payload["name"], payload["email"], payload["phone"],
                             payload["project_type"], payload["plan"], payload["budget"], payload["timeline"], payload["features"]])
    except Exception as e:
        print(f"Error saving lead locally: {e}")

    return jsonify({
        "status": "success",
        "message": "Requirements submitted successfully.",
        "booking_id": booking_id
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
