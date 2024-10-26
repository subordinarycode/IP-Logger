# Flask IP Logger

This Flask application captures and logs client information, such as geolocation, browser details, device settings, and more. It also provides a basic web interface for administrators to view and clear collected client data. The application is highly customizable with command-line arguments, enabling SSL, Cloudflare tunneling, and GPS functionality.

## Features

- **Client Information Logging**: Captures detailed client information, including IP, ISP, screen dimensions, language preferences, cookies enabled, and geolocation (latitude, longitude).
- **SQLite Database**: Stores client data in an SQLite database (`clients.db`) located in the `etc/` directory.
- **Admin Dashboard**: Provides an authenticated route `/clients` for viewing stored client data.
- **Database Management**: Includes a `/clear-database` endpoint for clearing all client data in the database.
- **Flexible Deployment**: Supports SSL, Cloudflared tunnels, and GPS-based geolocation via command-line arguments.

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Usage](#usage)
4. [Routes](#routes)
5. [Command-Line Arguments](#command-line-arguments)
6. [Logging](#logging)
7. [Security Considerations](#security-considerations)

## Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize the SQLite Database**:
   Run the Flask application to automatically create the `clients.db` database in the `etc/` directory:
   ```bash
   python app.py --redirect_url <your_redirect_url>
   ```

## Configuration

The application uses several command-line arguments for configuration, including SSL certificate paths, GPS functionality, and Cloudflare tunneling. See [Command-Line Arguments](#command-line-arguments) for details.

### Setting Up SSL

To use SSL, supply paths to your certificate and key files using the `--ssl_cert` and `--ssl_key` arguments.

### Cloudflared Tunnel (Optional)

To make the application accessible over the internet without configuring your firewall, use the `--cloudflared` argument.

## Usage

To start the Flask application, run the following command:

```bash
python app.py --redirect_url <URL to redirect after data submission>
```

### Example:
```bash
python app.py --redirect_url "http://example.com" --debug
```

## Routes

- `/` - Main route that grabs the clients information.
- `/user_info` - Collects client data via POST requests in JSON format. This route validates the input data and logs it to the SQLite database.
- `/clients` - Admin route for viewing logged client data. This route requires a password, generated on each start.
- `/clear-database` - Clears all entries from the `user_info` table. Only accessible to authenticated users.
- `/login` - Provides the login form for accessing the `/clients` route.

## Command-Line Arguments

- `--redirect_url`: URL to redirect users after form submission.
- `--debug`: Enables Flask debug mode.
- `--ssl_cert`: Path to SSL certificate file.
- `--ssl_key`: Path to SSL key file.
- `--gps`: Enables GPS functionality for obtaining client geolocation.
- `--cloudflared`: Starts a Cloudflared tunnel for public internet access.

### Example
```bash
python app.py --redirect_url "http://example.com" --debug --ssl_cert path/to/cert.pem --ssl_key path/to/key.pem --gps
```

## Logging

The application logs all events, errors, and actions to `etc/flask_app.log` in the following format:
```
[Timestamp] [Log Level]: Message
```

## Security Considerations

- **Session Management**: Secure random keys are used for session management, and failed login attempts are limited.
- **SSL Support**: Strongly recommended to enable SSL to protect client information transmitted over the network.
- **Database Access**: Ensure the `etc/` directory is secured, as it contains sensitive data.

