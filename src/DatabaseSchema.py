import sqlite3
from marshmallow import Schema, fields, validate


def get_all_links(db_path):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT link1, link2 FROM links')
        return cursor.fetchall()  # Returns a list of tuples


def insert_link(db_path, link1, link2):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO links (link1, link2) VALUES (?, ?)
        ''', (link1, link2))
        conn.commit()


def init_db(db_path):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link1 TEXT NOT NULL,
                link2 TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL,
                longitude REAL,
                city TEXT,
                region TEXT,
                country_code TEXT,
                zip_code INTEGER,
                org TEXT,
                region_name TEXT,
                public_ip TEXT NOT NULL,
                isp TEXT,
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
                timezone_offset INTEGER NOT NULL,
                cookies_enabled TEXT NOT NULL,
                do_not_track TEXT NOT NULL,
                connection_type TEXT NOT NULL,
                browser_name TEXT NOT NULL,
                browser_version TEXT NOT NULL,
                time_on_page REAL NOT NULL,
                referrer TEXT,
                device_type TEXT NOT NULL,
                installed_plugins TEXT NOT NULL,
                available_fonts TEXT NOT NULL,
                screen_orientation TEXT NOT NULL,
                audio_capabilities TEXT NOT NULL,
                touch_support TEXT NOT NULL,
                hardware_concurrency INTEGER NOT NULL,
                session_storage_supported TEXT NOT NULL,
                canvas_fingerprint TEXT NOT NULL,
                webgl_fingerprint TEXT NOT NULL,
                is_dst TEXT NOT NULL,
                features_supported TEXT NOT NULL,
                device_memory REAL NOT NULL,
                battery_status TEXT NOT NULL,
                effective_type TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()


class UserInfoSchema(Schema):
    latitude = fields.Float(required=False)
    longitude = fields.Float(required=False)
    publicIP = fields.Str(required=True)
    isp = fields.Str(required=False)
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
    timezoneOffset = fields.Int(required=True)
    cookiesEnabled = fields.Str(required=True, validate=validate.OneOf(["Yes", "No", "Unknown"]))
    doNotTrack = fields.Str(required=True, validate=validate.OneOf(["Yes", "No", "Unknown"]))
    connectionType = fields.Str(required=True)
    browserName = fields.Str(required=True)
    browserVersion = fields.Str(required=True)
    timeOnPage = fields.Float(required=True)
    referrer = fields.Str(required=False)
    deviceType = fields.Str(required=True)
    installedPlugins = fields.List(fields.Str(), required=True)
    availableFonts = fields.List(fields.Str(), required=True)
    screenOrientation = fields.Str(required=True)
    audioCapabilities = fields.List(fields.Str(), required=True)
    touchSupport = fields.Bool(required=True)
    hardwareConcurrency = fields.Int(required=True)
    sessionStorageSupported = fields.Bool(required=True)
    webGLFingerprint = fields.Str(required=True)
    isDST = fields.Bool(required=True)
    featuresSupported = fields.Dict( required=True)
    deviceMemory = fields.Float(required=True)
    batteryStatus = fields.Dict(required=True)
    effectiveType = fields.Str(required=True)
    timestamp = fields.Str(required=True)

