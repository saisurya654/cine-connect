from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_cors import CORS
import boto3
import os
import uuid
from botocore.exceptions import NoCredentialsError
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'super_secret_key'
CORS(app)

# AWS S3 Configuration
S3_KEY = "AKIAVWABKA7LVAH2J45G"
S3_SECRET = "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"
S3_REGION = "us-east-1"
MEDIA_BUCKET = "cinemaindustry-01"  # Bucket for all media types

s3 = boto3.client('s3', aws_access_key_id=S3_KEY, aws_secret_access_key=S3_SECRET, region_name=S3_REGION)

# MySQL Database Configuration
DB_HOST = 'localhost'  # Replace with your database host
DB_USER = 'root'       # Replace with your MySQL username
DB_PASSWORD = 'Surya@123'  # Replace with your MySQL password
DB_NAME = 'cinema_industry'

# Connect to MySQL Database
def get_db_connection():
    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    return connection if connection.is_connected() else None

# Create tables for users and files if they do not exist
def create_tables():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                file_url TEXT NOT NULL,
                role VARCHAR(20) NOT NULL,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
        cursor.close()
        connection.close()

create_tables()

# Register User
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
        role = data.get('role')

        if not all([username, email, phone, password, role]):
            return jsonify({"error": "All fields are required"}), 400

        save_user_to_db(username, email, phone, password, role)
        return redirect(url_for('login'))

    return render_template('register.html')

def save_user_to_db(username, email, phone, password, role):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO users (username, email, phone, password, role)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, email, phone, password, role))
        connection.commit()
        cursor.close()
        connection.close()

# Login User
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            cursor.close()
            connection.close()

            if user and user[4] == password:
                session['username'] = username
                session['role'] = user[5]
                return redirect(url_for('dashboard'))

        return "Invalid username or password", 401

    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    username = session.get('username')
    role = session.get('role')

    if not username:
        return redirect(url_for('login'))

    if role == 'writer':
        writer_files = get_files_by_role(username, 'writer')
        actor_files = get_files_by_role(None, 'actor')
        return render_template('writer_dashboard.html', title="Writer Dashboard", username=username, writer_files=writer_files, actor_files=actor_files)
    elif role == 'actor':
        actor_files = get_files_by_role(username, 'actor')
        other_actor_files = get_files_by_role(None, 'actor')
        return render_template('actor_dashboard.html', title="Actor Dashboard", username=username, actor_files=actor_files, other_actor_files=other_actor_files)
    elif role == 'director':
        actor_files = get_files_by_role(None, 'actor')
        writer_files = get_files_by_role(None, 'writer')
        return render_template('director_dashboard.html', title="Director Dashboard", username=username, actor_files=actor_files, writer_files=writer_files)

    return "Invalid role", 400

# Upload File - Writers and Actors only
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        # Upload file to S3
        try:
            file_key = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]  # Unique file key
            s3.upload_fileobj(file, MEDIA_BUCKET, file_key)
            file_url = f"https://{MEDIA_BUCKET}.s3.{S3_REGION}.amazonaws.com/{file_key}"

            # Save file metadata to MySQL database
            username = session.get('username')
            role = session.get('role')
            save_file_metadata_to_db(username, file_url, role)

            flash('File successfully uploaded')
            return redirect(url_for('dashboard'))
        except NoCredentialsError:
            flash('Credentials not available for AWS S3')
            return redirect(request.url)
        
    return render_template('upload.html')  # For GET, show the upload form

def save_file_metadata_to_db(username, file_url, role):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO files (username, file_url, role)
            VALUES (%s, %s, %s)
        """, (username, file_url, role))
        connection.commit()
        cursor.close()
        connection.close()

# Get files by role (actor or writer)
def get_files_by_role(username, role):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        if username:
            cursor.execute("SELECT file_url FROM files WHERE username = %s AND role = %s", (username, role))
        else:
            cursor.execute("SELECT file_url FROM files WHERE role = %s", (role,))
        files = cursor.fetchall()
        cursor.close()
        connection.close()
        return [file[0] for file in files]
    return []

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    
    # Fetch additional user details if necessary
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT username, email, phone, role FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        
        return render_template('profile.html', user=user)

    return "User not found", 404


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
