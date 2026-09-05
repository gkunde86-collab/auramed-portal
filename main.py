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

    # Fallback to alternative naming if DB_HOST isn't found
    if not db_host:
        db_host = os.environ.get("MYSQLHOST")
        db_user = os.environ.get("MYSQLUSER")
        db_password = os.environ.get("MYSQLPASSWORD")
        db_name = os.environ.get("MYSQLDATABASE")
        db_port = os.environ.get("MYSQLPORT", "3306")

    return mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=int(db_port)
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
