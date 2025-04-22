import os
import logging
from stem.process import launch_tor_with_config


class TorService:
    def __init__(self, hidden_service_port=5000, socks_port=9050, tor_binary=None):  # Add socks_port here
        self.logger = logging.getLogger('JustSocial')
        self.hidden_service_port = hidden_service_port
        self.hidden_service_dir = None
        self.onion_address = None
        self.tor_process = None
        self.socks_port = socks_port  # Store the socks_port
        self.tor_binary = tor_binary  # Store the tor_binary path

    def start(self):
        """Start Tor with hidden service configuration, logging details."""
        try:
            # 1. Determine Hidden Service Directory (with logging)
            potential_dirs = [
                os.path.expanduser("~/.tor/hidden_service"),  # Common location
                os.path.join(os.getcwd(), "hidden_service")  # In the current dir
                # Add any other paths you want to check
            ]

            for directory in potential_dirs:
                full_path = os.path.join(directory, "hostname")
                if os.path.exists(full_path):
                    self.hidden_service_dir = directory
                    self.logger.info(f"Found existing hidden service directory: {self.hidden_service_dir}")
                    self.logger.info(f"Hostname file found at: {full_path}")  # Log hostname file path
                    break

            if self.hidden_service_dir is None:
                try:
                    if not os.path.exists(potential_dirs[0]):
                        os.mkdir(potential_dirs[0], mode=0o700)
                    self.hidden_service_dir = potential_dirs[0]
                   # self.hidden_service_dir = tempfile.mkdtemp()
                    self.logger.info(f"Creating NEW hidden service directory: {self.hidden_service_dir}")
                except Exception as e:
                    self.logger.error(f"Failed to create hidden service directory: {e}")
                    raise  # Re-raise the exception

            if self.hidden_service_dir is None:  # Double-check
                raise Exception("Hidden service directory could not be created or found.")

            # 2. Configuration for Tor (log the directory being used)
            print("as0adasdasdasdsadas")
            print(self.hidden_service_dir )
            tor_config = {
                #  'SocksPort': str(self.socks_port),  # Use the provided socks_port
                'ControlPort': '9051',
                'HiddenServiceDir': self.hidden_service_dir,  # Log this!
                'HiddenServicePort': f'{self.hidden_service_port} 127.0.0.1:{self.hidden_service_port}'
            }
            self.logger.info(f"Tor configuration: HiddenServiceDir = {tor_config['HiddenServiceDir']}")

            # 3. Start Tor process
            self.tor_process = launch_tor_with_config(
                config=tor_config,
                take_ownership=True
            )

            # 4. Read the onion address (from the correct location)
            hostname_path = os.path.join(self.hidden_service_dir, 'hostname')  # Use correct path!
            self.logger.info(f"Looking for hostname file at: {hostname_path}")  # Log the full path

            # 5. Wait for hostname file (improved logging)
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
                self.logger.error(f"Hostname file NOT found at: {hostname_path}")  # Log the error
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
                self.tor_process = None

            # Cleanup temporary directory
            # if os.path.exists(self.hidden_service_dir):
            #     for file in os.listdir(self.hidden_service_dir):
            #         filepath = os.path.join(self.hidden_service_dir, file)
            #         if os.path.isfile(filepath):
            #             os.remove(filepath)
            #     os.rmdir(self.hidden_service_dir)

        except Exception as e:
            self.logger.error(f"Error stopping Tor service: {e}")

    def get_onion_address(self):
        """Get the .onion address"""
        return self.onion_address
