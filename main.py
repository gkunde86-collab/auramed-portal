import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
import mysql.connector

app = Flask(__name__)

# --- Database Connection Helper ---
def get_db_connection():
    db_host = os.environ.get("DB_HOST")
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_name = os.environ.get("DB_NAME")
    db_port = os.environ.get("DB_PORT", "3306")

    # Connect to MySQL database
    conn = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=int(db_port)
    )

    # Automatically create the 'patients' table if it does not exist
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            age INT,
            disease VARCHAR(255)
        )
    """)
    conn.commit()
    cursor.close()

    return conn

# 1. Main Home Route
@app.route('/')
def home():
    return render_template('index.html')

# 2. Login Endpoint
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM patients WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            return f"<div style='font-family: sans-serif; text-align: center; padding: 50px;'>" \
                   f"<h1>Welcome back, {user['username']}!</h1>" \
                   f"<p>Login successful.</p></div>"
        else:
            return "<div style='font-family: sans-serif; text-align: center; padding: 50px;'>" \
                   "<h3>Invalid username or password.</h3>" \
                   "<a href='/'>Try again</a></div>", 401

    except Exception as e:
        return f"Database error: {str(e)}", 500

# 3. Patient Registration Endpoint
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    age = data.get('age')
    disease = data.get('disease')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO patients (username, password, email, age, disease) VALUES (%s, %s, %s, %s, %s)",
            (username, password, email, age, disease)
        )
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "User registered successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
