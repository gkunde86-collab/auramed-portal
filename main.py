import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "auramed_super_secret_key")

# Aiven MySQL Database Connection Configuration from Environment Variables
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            database=os.environ.get("DB_NAME"),
            port=int(os.environ.get("DB_PORT", 3306)),
            ssl_ca=os.environ.get("DB_SSL_CA", None)  # Optional SSL path if required by Aiven
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Auto-initialize database schema on startup
def init_db():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(100),
                    age INT,
                    disease VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cursor.close()
            conn.close()
            print("Database initialized successfully.")
        except Error as e:
            print(f"Failed to initialize table: {e}")

# Initialize table when server starts
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    # Handle both JSON payloads and standard form submissions
    if request.is_json:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        age = data.get('age')
        disease = data.get('disease')
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        age = request.form.get('age')
        disease = request.form.get('disease')

    if not username or not password:
        if request.is_json:
            return jsonify({"status": "error", "message": "Username and password required"}), 400
        return render_template('index.html', error="Username and password required")

    conn = get_db_connection()
    if not conn:
        if request.is_json:
            return jsonify({"status": "error", "message": "Database connection failed"}), 500
        return render_template('index.html', error="Database connection failed")

    try:
        cursor = conn.cursor()
        query = "INSERT INTO patients (username, password, email, age, disease) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (username, password, email, age, disease))
        conn.commit()
        cursor.close()
        conn.close()

        if request.is_json:
            return jsonify({"status": "success", "message": "Registration successful"}), 200
        # Serve main page upon successful registration
        return render_template('index.html', success="Account created successfully! Please sign in.")

    except Error as e:
        print(f"Database error during registration: {e}")
        if request.is_json:
            return jsonify({"status": "error", "message": "Username already exists or database error"}), 400
        return render_template('index.html', error="Registration failed. Username may already exist.")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('index.html')

    if request.is_json:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
    else:
        username = request.form.get('username')
        password = request.form.get('password')

    conn = get_db_connection()
    if not conn:
        if request.is_json:
            return jsonify({"status": "error", "message": "Database connection failed"}), 500
        return render_template('index.html', error="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM patients WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            if request.is_json:
                return jsonify({"status": "success", "message": f"Welcome back, {user['username']}!"}), 200
            # Render index page with logged-in view
            return render_template('index.html', user=user)
        else:
            if request.is_json:
                return jsonify({"status": "error", "message": "Invalid username or password"}), 401
            return render_template('index.html', error="Invalid username or password")

    except Error as e:
        print(f"Database error during login: {e}")
        if request.is_json:
            return jsonify({"status": "error", "message": "Login failed due to database error"}), 500
        return render_template('index.html', error="Login failed. Please try again.")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
