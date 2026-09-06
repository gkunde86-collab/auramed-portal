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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    age INT NOT NULL,
                    disease_type VARCHAR(100) NOT NULL
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS medicines (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    medicine_type VARCHAR(50) NOT NULL,
                    dosage VARCHAR(50) NOT NULL,
                    reminder_time TIME NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
    email = data.get('email', '')
    age = data.get('age', 0)
    disease_type = data.get('disease') or data.get('disease_type') or 'General'

    if not username or not password:
        return render_template('index.html', error="Username and Password required.")

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = "INSERT INTO users (username, password, email, age, disease_type) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (username, password, email, age, disease_type))
            conn.commit()
            cursor.close()
            conn.close()
            return render_template('index.html', success="Registration successful! Please login.")
        except Error as e:
            print(f"Registration Error: {e}")
            return render_template('index.html', error="Username already exists.")
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
        cursor.execute("SELECT id, username, email, age, disease_type FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:
            cursor.execute("SELECT id, name, medicine_type, dosage, CAST(reminder_time AS CHAR) as reminder_time FROM medicines WHERE user_id = %s", (user['id'],))
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
    name = data.get('medicine_name')
    medicine_type = data.get('medicine_type', 'Tablet')
    dosage = data.get('dosage', '1')
    reminder_time = data.get('alarm_time')

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO medicines (user_id, name, medicine_type, dosage, reminder_time) 
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, name, medicine_type, dosage, reminder_time))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
