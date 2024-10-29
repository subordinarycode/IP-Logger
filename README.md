
# Flask IP Logger

This Flask application captures and logs client information, including geolocation, browser details, device settings, and more. It provides a web interface for administrators to view and manage collected data.

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Routes](#routes)
6. [Command-Line Arguments](#command-line-arguments)
7. [Logging](#logging)
8. [Security Considerations](#security-considerations)

## Features

### 1. **Client Information Logging**
   - Collects and logs detailed information about each client that connects to the application, utilizing their IP address for enhanced data collection.

### 2. **Data Collected**
   The application captures the following data points:

   - **Geolocation Data**:
     - **Latitude**: Geographical latitude of the client.
     - **Longitude**: Geographical longitude of the client.
     - **City**: City associated with the client's IP address.
     - **Region**: State or region associated with the client's IP address.
     - **Country Code**: ISO code of the country from which the request originated.
     - **Zip Code**: Postal code, if available.
     - **ISP**: Internet Service Provider of the client.
     - **Organization**: The organization associated with the IP address.

   - **IP Address**:
     - **Public IP**: The public IP address of the client.

   - **User Agent Information**:
     - **User Agent**: The user agent string from the client's request, detailing the browser and operating system.
     - **Platform**: The operating system of the client (e.g., Windows, macOS, Linux).
     - **Browser Name and Version**: Information about the browser used by the client.

   - **Screen and Display Metrics**:
     - **Screen Width**: Width of the client's screen in pixels.
     - **Screen Height**: Height of the client's screen in pixels.
     - **Color Depth**: The color depth of the client’s display.
     - **Viewport Width/Height**: Dimensions of the viewport for responsive design.
     - **Screen Orientation**: Orientation of the client's screen (portrait or landscape).

   - **Performance and Capabilities**:
     - **Device Type**: Type of device (e.g., desktop, mobile, tablet).
     - **Installed Plugins**: List of browser plugins installed by the client.
     - **Available Fonts**: Fonts available on the client's system.
     - **Hardware Concurrency**: Number of logical processors available to the client.
     - **Device Memory**: Amount of device memory available to the client.
     - **Battery Status**: Information about the client's battery charging status.
     - **Touch Support**: Indicates if the device supports touch interactions.

   - **Miscellaneous Data**:
     - **Language**: The primary language set in the client's browser.
     - **Language Preferences**: List of preferred languages.
     - **Timezone**: Timezone of the client.
     - **Do Not Track**: Indicates if the client has opted out of tracking.
     - **Cookies Enabled**: Indicates whether cookies are enabled in the browser.
     - **Time Spent on Page**: Duration the client spent on the page.

   - **Timestamp**: Records the date and time of the client's visit.
     
### 3. **User Authentication**
   - The application features a password-protected interface for accessing the statistics page, ensuring that sensitive data is only viewable by authorized users.

### 4. **Web Interface**
   - A responsive and user-friendly web interface allows users to log data and view statistics easily. Navigation is straightforward, providing access to various functionalities.

### 5. **Database Management**
   - All collected data is stored in a SQLite database, facilitating easy querying and management.
   - Users can clear the database through a secure endpoint, ensuring efficient data management.

### 6. **Logging and Monitoring**
   - The application maintains a log file to track actions and errors, providing insights into its operation and assisting with debugging.

### 7. **Threaded Processing**
   - Incoming requests for client data are processed in separate threads, enabling the application to handle multiple requests efficiently without blocking.


## Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize the SQLite Database**:
   Run the Flask application to automatically create the `clients.db` database in the `etc/` directory:
   ```bash
   python app.py
   ```

## Configuration

The application uses several command-line arguments for configuration, including SSL certificate paths, GPS functionality, and Cloudflare tunneling. 

### Setting Up SSL

To use SSL, supply paths to your certificate and key files using the `--ssl_cert` and `--ssl_key` arguments.

### Cloudflared Tunnel (Optional)

To make the application accessible over the internet without configuring your firewall, use the `--cloudflared` argument.

## Usage

To start the Flask application, run the following command:

```bash
python app.py
```

### Example:
```bash
python app.py -i 0.0.0.0 -p 8080 --debug
```

## Routes

- `/` - Collects client data via POST requests in JSON format, validates it, and logs it to the database.
- `/statistics` - Admin route for viewing logged client data. This route requires a password for authentication.
- `/clear-database` - Clears all entries from the `user_info` table. Only accessible to authenticated users.

## Command-Line Arguments

- `--debug`: Enables Flask debug mode.
- `--ssl_cert`: Path to SSL certificate file.
- `--ssl_key`: Path to SSL key file.
- `--cloudflared`: Starts a Cloudflared tunnel for public internet access.
- `-p, --port`: Specify the port number (default: 5000).
- `-i, --interface`: Specify the interface to use (default: `127.0.0.1`).

### Example
```bash
python app.py -i 0.0.0.0 -p 8080 --debug --ssl_cert path/to/cert.pem --ssl_key path/to/key.pem --gps
```

## Logging

The application logs all events, errors, and actions to `etc/flask.log` in the following format:
```
[Timestamp] [Log Level]: Message
```

## Security Considerations

- **Session Management**: Uses secure random keys for session management, with limited failed login attempts to enhance security.
- **SSL Support**: Strongly recommended to enable SSL to protect client information transmitted over the network.
- **Database Access**: Ensure the `etc/` directory is secured, as it contains sensitive data.

