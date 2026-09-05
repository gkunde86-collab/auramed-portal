from flask import Flask, render_template, request, jsonify
import mysql.connector

app = Flask(__name__)

# --- Database Connection Helper ---
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",          # Change to your MySQL username
        password="password",  # Change to your MySQL password
        database="medicine_db"
    )

# --- Routes ---

# 1. Render Main Frontend UI
@app.route('/')
def home():
    return render_template('index.html')

# 2. Patient Registration Endpoint
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    age = data.get('age')
    disease = data.get('disease')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
            INSERT INTO users (username, password, email, age, disease_type)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (username, password, email, age, disease))
        conn.commit()
        return jsonify({"message": "Registration successful!"}), 201

    except mysql.connector.Error as err:
        return jsonify({"error": "Username already exists or database error occurred."}), 400

    finally:
        cursor.close()
        conn.close()

# 3. Patient Login Endpoint
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "disease": user['disease_type']
            }
        }), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

# 4. Fetch Reminders for Specific User
@app.route('/api/medicines/<int:user_id>', methods=['GET'])
def get_medicines(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM medicines WHERE user_id = %s ORDER BY reminder_time ASC"
    cursor.execute(query, (user_id,))
    medicines = cursor.fetchall()

    # Format TIME objects to string (HH:MM:SS) for JSON output
    for med in medicines:
        med['reminder_time'] = str(med['reminder_time'])

    cursor.close()
    conn.close()
    return jsonify(medicines), 200

# 5. Add New Medicine Reminder
@app.route('/api/medicines', methods=['POST'])
def add_medicine():
    data = request.json
    user_id = data.get('user_id')
    name = data.get('name')
    medicine_type = data.get('medicine_type')
    dosage = data.get('dosage')
    reminder_time = data.get('reminder_time')

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO medicines (user_id, name, medicine_type, dosage, reminder_time)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (user_id, name, medicine_type, dosage, reminder_time))
    conn.commit()

    cursor.close()
    conn.close()
    return jsonify({"message": "Medicine reminder added successfully!"}), 201

# 6. Delete Medicine Reminder
@app.route('/api/medicines/<int:med_id>', methods=['DELETE'])
def delete_medicine(med_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "DELETE FROM medicines WHERE id = %s"
    cursor.execute(query, (med_id,))
    conn.commit()

    cursor.close()
    conn.close()
    return jsonify({"message": "Medicine reminder deleted!"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)