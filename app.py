from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
