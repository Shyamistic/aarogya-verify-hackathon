from flask import Flask, jsonify

app = Flask(__name__)

# This is our mock database. In the real world, this would be a real database.
NPI_DATABASE = {
    "1234567890": {
        "status": "success",
        "data": {
            "name": "Dr. Priya Sharma",
            "phone": "555-1233", # Note: This is different from the CSV!
            "address": "123 Main St, Mumbai",
            "license": "MH-98765" 
        }
    },
    "2345678901": {
        "status": "success",
        "data": {
            "name": "Dr. Arjun Gupta",
            "phone": "555-5678",
            "address": "456 Old Rd, Delhi",
            "license": "DL-12345"
        }
    }
}

@app.route('/lookup/<npi_number>')
def lookup_npi(npi_number):
    data = NPI_DATABASE.get(npi_number)
    if data:
        return jsonify(data)
    else:
        return jsonify({"status": "error", "message": "NPI not found"}), 404

if __name__ == '__main__':
    app.run(port=5000, debug=True)