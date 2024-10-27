import os
import requests
import subprocess
import time
import re
import shutil
import threading
import zipfile
import tarfile


class Cloudflared:
    """
    Class for managing Cloudflared tunnel.

    Args:
        app: Flask application instance to tunnel.
        host (str): The host address to tunnel traffic to (default is "127.0.0.1").
        port (int): The port number to tunnel traffic to (default is 5000).
        download_dir (str): Directory to download Cloudflared binary (default is "Cloudflared").

    Attributes:
        host (str): The host address to tunnel traffic to.
        port (int): The port number to tunnel traffic to.
        app: Flask application instance to tunnel.
        url (str): The URL of the Cloudflared tunnel once started.
        _process: Process object representing the Cloudflared subprocess.
        _download_dir (str): Directory to download Cloudflared binary.

    Methods:
        install: Install Cloudflared binary if not already installed.
        start: Start the Cloudflared tunnel.
        stop: Stop the Cloudflared tunnel.
    """

    def __init__(self, flask_app, host="127.0.0.1", port=5000, download_dir="Cloudflared", socketio_app=None):
        self.host = host
        self.port = port
        self.app = flask_app
        self.url = ""
        self._process = None
        self._download_dir = download_dir

        if socketio_app:
            self.flask_thread = threading.Thread(target=self.app.run, kwargs={"threaded": True, "host": self.host, "port": self.port, "app": self.app})
        else:
            self.flask_thread = threading.Thread(target=self.app.run, kwargs={"threaded": True, "host": self.host, "port": self.port})

        if not os.path.isdir(self._download_dir):
            os.mkdir(self._download_dir)

        self._install()

    def _install(self) -> bool:
        # Check if in Termux
        if os.path.exists('/data/data/com.termux/files/home'):
            if not os.path.exists('/data/data/com.termux/files/usr/bin/cloudflared'):
                print("Detected Termux environment. Installing cloudflared via pkg.")
                subprocess.run(["pkg", "install", "-y", "cloudflared"], check=True)
                return os.path.isfile('/data/data/com.termux/files/usr/bin/cloudflared')

        # Download the latest release of cloudflared
        if not os.path.isfile(f"{self._download_dir}/cloudflared"):
            print(f"Installing cloudflared in {self._download_dir}/cloudflared")
            arch = os.uname().machine
            if 'arm' in arch or 'Android' in arch:
                self._download('https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm', 'cloudflared')
            elif 'aarch64' in arch:
                self._download('https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64', 'cloudflared')
            elif 'x86_64' in arch:
                self._download('https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64', 'cloudflared')
            else:
                self._download('https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-386', 'cloudflared')

        if os.path.isfile(f"{self._download_dir}/cloudflared"):
            return True

        return False

    def _download(self, url, output):
        file_name = os.path.basename(url)

        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(file_name, 'wb') as f:
                    f.write(response.content)

                if file_name.endswith('.zip'):
                    with zipfile.ZipFile(file_name, 'r') as zip_ref:
                        zip_ref.extractall(self._download_dir)
                    shutil.move(output, os.path.join(self._download_dir, output))

                elif file_name.endswith('.tgz'):
                    with tarfile.open(file_name, 'r:gz') as tar_ref:
                        tar_ref.extractall(self._download_dir)
                    shutil.move(output, os.path.join(self._download_dir, output))

                else:
                    shutil.move(file_name, os.path.join(self._download_dir, output))

                os.chmod(os.path.join(self._download_dir, output), 0o755)
                if os.path.isfile(file_name):
                    os.remove(file_name)

        except Exception as e:
            print(e)

    def start(self) -> str:
        # Setup the variables
        log_file = os.path.join(self._download_dir, "cloudflared.log")
        binary_file = os.path.join(self._download_dir, "cloudflared")
        termux_chroot = "/data/data/com.termux/files/usr/bin/termux-chroot"
        cloudflared_url_regex = r'https://[-0-9a-z]*\.trycloudflare.com'

        # Remove previous log file
        if os.path.isfile(log_file):
            os.remove(log_file)

        # Start flask
        self._start_flask()

        # Launching Cloudflared
        if os.path.exists(termux_chroot):
            binary_file = '/data/data/com.termux/files/usr/bin/cloudflared'
            self._process = subprocess.Popen([termux_chroot, binary_file, "tunnel", "-url", f"{self.host}:{self.port}", "--logfile", log_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            self._process = subprocess.Popen([binary_file, "tunnel", "-url", f"{self.host}:{self.port}", "--logfile", log_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Delay
        time.sleep(8)

        # Read the cloudflared log file
        with open(log_file, "r") as log_file:
            log_content = log_file.read()

        # Extract the url from the log file
        cldflr_url_match = re.search(cloudflared_url_regex, log_content)
        if cldflr_url_match:
            self.url = cldflr_url_match.group(0)
            return self.url
        else:
            return ""

    def _start_flask(self) -> None:
        self.flask_thread.daemon = True
        self.flask_thread.start()

    def stop(self) -> None:
        if self._process:
            self._process.kill()


