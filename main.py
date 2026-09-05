import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
import mysql.connector

app = Flask(__name__)

# --- Database Connection Helper ---
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "password"),
        database=os.getenv("DB_NAME", "medicine_db"),
        port=int(os.getenv("DB_PORT", 3306))
    )

# 1. Main Page Route
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
