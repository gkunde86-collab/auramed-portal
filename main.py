import os
from flask import Flask, render_template, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "auramed_super_secret_key")

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            database=os.environ.get("DB_NAME"),
            port=int(os.environ.get("DB_PORT", 3306)),
            ssl_ca=os.environ.get("DB_SSL_CA", None)
        )
        return connection
    except Error as e:
        print(f"Database Connection Error: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Patients Table
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
            # Medicines & Alarms Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alarms (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    medicine_name VARCHAR(255) NOT NULL,
                    alarm_time VARCHAR(10) NOT NULL,
                    notes VARCHAR(255),
                    FOREIGN KEY (user_id) REFERENCES patients(id) ON DELETE CASCADE
                );
            """)
            conn.commit()
            cursor.close()
            conn.close()
        except Error as e:
            print(f"Init DB Error: {e}")

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.form if request.form else request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    age = data.get('age')
    disease = data.get('disease')

    if not username or not password:
        return render_template('index.html', error="Username and Password required.")

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = "INSERT INTO patients (username, password, email, age, disease) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (username, password, email, age, disease))
            conn.commit()
            cursor.close()
            conn.close()
            return render_template('index.html', success="Registration successful! Please login.")
        except Error as e:
            return render_template('index.html', error="Username already exists or database error.")
    return render_template('index.html', error="Database connection failed.")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('index.html')

    data = request.form if request.form else request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM patients WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:
            # Fetch alarms for this specific patient
            cursor.execute("SELECT * FROM alarms WHERE user_id = %s", (user['id'],))
            alarms = cursor.fetchall()
            cursor.close()
            conn.close()
            return render_template('index.html', user=user, alarms=alarms)
        cursor.close()
        conn.close()

    return render_template('index.html', error="Invalid credentials.")

@app.route('/add_alarm', methods=['POST'])
def add_alarm():
    data = request.get_json()
    user_id = data.get('user_id')
    medicine_name = data.get('medicine_name')
    alarm_time = data.get('alarm_time')
    notes = data.get('notes')

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO alarms (user_id, medicine_name, alarm_time, notes) VALUES (%s, %s, %s, %s)",
                       (user_id, medicine_name, alarm_time, notes))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
