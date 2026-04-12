import random
import string
import csv
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def generate_booking_id():
    return "DB-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact', methods=['POST'])
def contact():
    # Handle contact form submission
    data = request.form
    # In a real app, send email or save to DB here
    return jsonify({"status": "success", "message": "Message received. Initiating response protocol..."})

@app.route('/apply', methods=['POST'])
def apply():
    # Handle job application form submission
    data = request.form
    # In a real app, process application here
    return jsonify({"status": "success", "message": "Application accepted. Evaluating credentials..."})

@app.route('/submit-requirements', methods=['POST'])
def submit_requirements():
    data = request.form
    booking_id = generate_booking_id()

    # Extract data
    name = data.get('name', '')
    email = data.get('email', '')
    phone = data.get('phone', '')
    project_type = data.get('projectType', '')
    plan = data.get('plan', '')
    budget = data.get('budget', '')
    timeline = data.get('timeline', '')
    features = data.get('features', '')

    # Mock Google Sheets Integration: Append to a local CSV file
    csv_file = 'leads.csv'
    file_exists = os.path.isfile(csv_file)

    try:
        with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Booking ID', 'Name', 'Email', 'Phone', 'Project Type', 'Plan', 'Budget', 'Timeline', 'Features'])
            writer.writerow([booking_id, name, email, phone, project_type, plan, budget, timeline, features])
    except Exception as e:
        print(f"Error saving lead: {e}")
        # Continue anyway to not break the user flow

    return jsonify({
        "status": "success",
        "message": "Requirements submitted successfully.",
        "booking_id": booking_id
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
