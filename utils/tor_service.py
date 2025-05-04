import os
import json
import tempfile
import logging
import platform
import subprocess
from shutil import which
import stem.control
from stem.process import launch_tor_with_config


class TorService:
    def __init__(self, hidden_service_port=5000, socks_port=9050, tor_binary=None):
        self.logger = logging.getLogger('JustSocial')
        self.hidden_service_port = hidden_service_port
        self.hidden_service_dir = None
        self.onion_address = None
        self.tor_process = None
        self.socks_port = socks_port
        self.tor_binary = tor_binary

        # Auto-detect Tor binary if not provided
        if self.tor_binary is None:
            self.tor_binary = self._find_tor_binary()

    def start(self):
        """Start Tor with hidden service configuration, logging details."""
        try:
            # First check if Tor is properly installed
            if not self.tor_binary or not self.verify_tor_installation():
                raise Exception(
                    "Tor is not installed or not properly configured. Please install Tor or specify the correct binary path.")

            # 1. Determine Hidden Service Directory (with logging)
            potential_dirs = [
                os.path.expanduser("~/.tor/hidden_service"),  # Common location
                os.path.join(os.getcwd(), "hidden_service")  # In the current dir
            ]

            # First, check if any of the potential directories already exist
            for directory in potential_dirs:
                hostname_path = os.path.join(directory, "hostname")
                if os.path.exists(hostname_path):
                    self.hidden_service_dir = directory
                    self.logger.info(f"Found existing hidden service directory: {self.hidden_service_dir}")
                    break

            # If no existing directory found, create one
            if self.hidden_service_dir is None:
                try:
                    # Use the first option (~/.tor/hidden_service)
                    tor_home_dir = os.path.expanduser("~/.tor")

                    # Ensure the parent directory exists
                    if not os.path.exists(tor_home_dir):
                        os.makedirs(tor_home_dir, mode=0o700)
                        self.logger.info(f"Created Tor home directory: {tor_home_dir}")

                    # Now create the hidden service directory
                    self.hidden_service_dir = os.path.join(tor_home_dir, "hidden_service")
                    if not os.path.exists(self.hidden_service_dir):
                        os.mkdir(self.hidden_service_dir, mode=0o700)
                        self.logger.info(f"Created NEW hidden service directory: {self.hidden_service_dir}")
                    else:
                        self.logger.info(f"Using existing hidden service directory: {self.hidden_service_dir}")

                except Exception as e:
                    self.logger.error(f"Failed to create hidden service directory: {e}")
                    raise  # Re-raise the exception

            if self.hidden_service_dir is None:  # Double-check
                raise Exception("Hidden service directory could not be created or found.")

            # 2. Configuration for Tor
            data_dir = os.path.join(os.path.dirname(self.hidden_service_dir), 'data')

            # Ensure data directory exists
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, mode=0o700)
                self.logger.info(f"Created Tor data directory: {data_dir}")

            tor_config = {
                # 'SocksPort': str(self.socks_port),
                'ControlPort': '9051',
                'DataDirectory': data_dir,
                'HiddenServiceDir': self.hidden_service_dir,
                'HiddenServicePort': f'{self.hidden_service_port} 127.0.0.1:{self.hidden_service_port}'
            }
            self.logger.info(f"Tor configuration: {tor_config}")

            # 3. Start Tor process with the specified binary
            launch_args = {
                'config': tor_config,
                'take_ownership': True,
                'tor_cmd': self.tor_binary  # Always use the detected or specified tor binary
            }

            self.logger.info(f"Launching Tor with binary: {self.tor_binary}")
            self.tor_process = launch_tor_with_config(**launch_args)

            # 4. Read the onion address
            hostname_path = os.path.join(self.hidden_service_dir, 'hostname')
            self.logger.info(f"Looking for hostname file at: {hostname_path}")

            # 5. Wait for hostname file
            max_attempts = 30
            attempts = 0
            while not os.path.exists(hostname_path) and attempts < max_attempts:
                self.logger.info(f"Waiting for hostname file (attempt {attempts + 1}/{max_attempts})...")
                import time
                time.sleep(1)
                attempts += 1

            if os.path.exists(hostname_path):
                with open(hostname_path, 'r') as f:
                    self.onion_address = f.read().strip()
                self.logger.info(f"Tor hidden service running at: {self.onion_address}")
            else:
                self.logger.error(f"Hostname file NOT found at: {hostname_path}")
                raise Exception(f"Hostname file not created after waiting {max_attempts} seconds.")

            return self.onion_address

        except Exception as e:
            self.logger.error(f"Error starting Tor service: {e}")
            raise

    def stop(self):
        """Stop Tor service"""
        try:
            if self.tor_process:
                self.tor_process.kill()
                self.logger.info("Tor process terminated")
                self.tor_process = None

            # Note: We're intentionally not removing the hidden service directory
            # to preserve the same .onion address for future runs
            self.logger.info(f"Tor service stopped. Hidden service directory preserved at: {self.hidden_service_dir}")

        except Exception as e:
            self.logger.error(f"Error stopping Tor service: {e}")

    def get_onion_address(self):
        """Get the .onion address"""
        return self.onion_address

    def _find_tor_binary(self):
        """Find the Tor binary on the system or return None if not found"""
        # First check if tor is in PATH
        tor_cmd = which('tor')
        if tor_cmd:
            self.logger.info(f"Found Tor binary in PATH: {tor_cmd}")
            return tor_cmd

        # Common installation locations based on operating system
        if platform.system() == 'Windows':
            # Common Windows Tor installation paths
            common_paths = [
                # Tor Browser paths
                os.path.expandvars(r'%ProgramFiles%\Tor Browser\Browser\TorBrowser\Tor\tor.exe'),
                os.path.expandvars(r'%ProgramFiles(x86)%\Tor Browser\Browser\TorBrowser\Tor\tor.exe'),
                # User directory paths
                os.path.expanduser(r'~\Desktop\Tor Browser\Browser\TorBrowser\Tor\tor.exe'),
                os.path.expanduser(r'~\Downloads\Tor Browser\Browser\TorBrowser\Tor\tor.exe'),
                # Custom Tor installation
                os.path.expandvars(r'%ProgramFiles%\Tor\tor.exe'),
                os.path.expandvars(r'%ProgramFiles(x86)%\Tor\tor.exe'),
                # Expert Bundle
                os.path.expanduser(r'~\tor\tor.exe'),
                # Current directory
                os.path.join(os.getcwd(), 'tor.exe'),
                os.path.join(os.getcwd(), 'tor', 'tor.exe')
            ]
        elif platform.system() == 'Darwin':  # macOS
            common_paths = [
                '/Applications/Tor Browser.app/Contents/MacOS/Tor/tor',
                '/Applications/TorBrowser.app/Contents/MacOS/Tor/tor',
                '/usr/local/bin/tor',
                '/opt/homebrew/bin/tor',
                os.path.expanduser('~/tor/tor'),
                os.path.join(os.getcwd(), 'tor')
            ]
        else:  # Linux and others
            common_paths = [
                '/usr/bin/tor',
                '/usr/local/bin/tor',
                '/opt/tor/tor',
                os.path.expanduser('~/tor/tor'),
                os.path.join(os.getcwd(), 'tor')
            ]

        # Check each path
        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                self.logger.info(f"Found Tor binary at: {path}")
                return path

        self.logger.warning(
            "Tor binary not found in common locations. Please install Tor or specify the path manually.")
        return None

    def verify_tor_installation(self):
        """Verify if Tor is properly installed and accessible"""
        if not self.tor_binary:
            self.logger.error("Tor binary not found. Please install Tor or specify the path manually.")
            return False

        try:
            # Try to get Tor version to verify it works
            result = subprocess.run(
                [self.tor_binary, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self.logger.info(f"Tor version: {version}")
                return True
            else:
                self.logger.error(f"Tor binary found but returned error: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Error verifying Tor installation: {e}")
            return False