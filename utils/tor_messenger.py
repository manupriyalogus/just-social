import os
import sys
import json
import time
import requests
import threading
import concurrent.futures
from flask import Flask, request, jsonify
from nacl.public import PrivateKey, PublicKey, Box
from nacl.encoding import HexEncoder
import wx
import logging
import base64

from . import TorService  # Assuming this contains your TorService class


class TorMessenger:
    def __init__(self, user_id, message_callback=None, socks_port=5000, tor_port=9050, tor_binary=None):
        self.user_id = user_id
        self.message_callback = message_callback
        self.logger = logging.getLogger('TorMessenger')
        self.TOR_PORT = tor_port
        self.tor_available = True
        self.socks_port = socks_port
        self.keys_file = f"{user_id}_keys.json"
        self.pending_messages = {}
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

        try:
            # Initialize Tor Service
            from . import TorService
            self.tor_service = TorService(socks_port=socks_port, tor_binary=tor_binary)
            self.onion_address = self.tor_service.start()
            self.logger.info(f"Tor service initialized with address: {self.onion_address}")

            # Load or generate encryption keys
            self.load_or_generate_keys()
            self.logger.info(f"Public Key (Hex): {self.public_key.encode(HexEncoder).decode()}")

            # Start message server
            self.server_thread = threading.Thread(target=self.start_message_server, daemon=True)
            self.server_thread.start()

            self.logger.info("TorMessenger initialization complete")

        except Exception as e:
            self.logger.error(f"Error initializing TorMessenger: {e}")
            self.tor_available = False
            raise

    def load_or_generate_keys(self):
        """Load existing keys from file or generate new ones"""
        try:
            if os.path.exists(self.keys_file):
                self.logger.info(f"Loading keys from {self.keys_file}")
                with open(self.keys_file, 'r') as f:
                    keys_data = json.load(f)

                # Load private key from saved data
                private_key_bytes = base64.b64decode(keys_data['private_key'])
                self.private_key = PrivateKey(private_key_bytes)
                self.public_key = self.private_key.public_key

                self.logger.info("Keys loaded successfully")
            else:
                self.logger.info("Generating new keys")
                # Generate new keys
                self.private_key = PrivateKey.generate()
                self.public_key = self.private_key.public_key

                # Save the keys
                self.save_keys()
        except Exception as e:
            self.logger.error(f"Error loading keys: {e}. Generating new ones.")
            # If loading fails, generate new keys
            self.private_key = PrivateKey.generate()
            self.public_key = self.private_key.public_key
            self.save_keys()

    def save_keys(self):
        """Save keys to file"""
        try:
            # Convert private key to storable format
            private_key_bytes = bytes(self.private_key)
            private_key_b64 = base64.b64encode(private_key_bytes).decode('ascii')

            # Create JSON structure
            keys_data = {
                'private_key': private_key_b64,
                'public_key': self.public_key.encode(HexEncoder).decode(),
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            # Save to file
            with open(self.keys_file, 'w') as f:
                json.dump(keys_data, f)

            self.logger.info(f"Keys saved to {self.keys_file}")
        except Exception as e:
            self.logger.error(f"Error saving keys: {e}")

    def set_status_update_callback(self, callback):
        """Set callback function to be called when message status changes"""
        self.logger.info(f"Setting status update callback: {callback}")
        self.status_update_callback = callback

    def get_connection_info(self):
        """Get connection information for sharing"""
        return {
            'onion_address': self.onion_address,
            'public_key': self.public_key.encode(HexEncoder).decode(),
            'user_id': self.user_id
        }

    def start_message_server(self):
        """Start the Flask server to receive messages"""
        app = Flask(__name__)

        @app.route("/receive", methods=["POST"])
        def receive():
            try:
                data = request.get_json()
                sender_public_key = data["sender_public_key"]
                encrypted_message = data["encrypted_message"]
                sender_id = data["sender_public_key"]

                decrypted_message = self.decrypt_message(encrypted_message, sender_public_key)

                # Notify the UI if a callback is set
                if self.message_callback:
                    wx.CallAfter(self.message_callback, {
                        'sender_id': sender_id,
                        'message': decrypted_message,
                        'timestamp': time.time(),
                        'sender_public_key': sender_public_key
                    })

                return jsonify({"status": "success"}), 200

            except Exception as e:
                self.logger.error(f"Error receiving message: {e}")
                return jsonify({"status": "error", "message": str(e)}), 400

        try:
            app.run(host="0.0.0.0", port=self.socks_port)  # Use self.SERVER_PORT here
        except Exception as e:
            self.logger.error(f"Failed to start server on port {self.socks_port}: {e}")

    def send_message(self, recipient_address, recipient_public_key, message, message_id=None):
        """
        Send a message asynchronously and update status when response is received

        Args:
            recipient_address: The .onion address of the recipient
            recipient_public_key: The public key of the recipient
            message: The message text to send
            message_id: Optional ID to track the message for status updates

        Returns:
            bool: True if the message was queued successfully, False otherwise
        """
        try:
            # Create a unique ID for this message if none provided
            if not message_id:
                message_id = f"msg_{int(time.time())}_{hash(message)}"

            self.logger.info(f"Queueing message {message_id} for {recipient_address}")

            # Add to pending messages with 'sending' status
            self.pending_messages[message_id] = {
                'status': 'sending',
                'timestamp': time.time(),
                'recipient': recipient_address,
                'message': message
            }

            # Update UI immediately if callback exists
            if self.status_update_callback:
                self.logger.info(f"Calling status update callback for message {message_id}: sending")
                wx.CallAfter(self.status_update_callback, message_id, 'sending')

            # Submit the async task to thread pool
            self.executor.submit(
                self._send_message_thread,
                recipient_address,
                recipient_public_key,
                message,
                message_id
            )

            return True

        except Exception as e:
            self.logger.error(f"Error queueing message: {e}")

            # Update status if there was an error
            if message_id and self.status_update_callback:
                wx.CallAfter(self.status_update_callback, message_id, 'failed')

            return False

    def _send_message_thread(self, recipient_address, recipient_public_key, message, message_id):
        """Background thread to send message and handle response"""
        try:
            print("==========Before encrypting============")
            print(message)
            encrypted_message = self.encrypt_message(message, recipient_public_key)
            print("==========encrypted_message============")
            print(encrypted_message)

            payload = {
                "sender_public_key": self.public_key.encode(HexEncoder).decode(),
                "encrypted_message": encrypted_message,
                "sender_id": self.user_id
            }

            # Make sure recipient address has the correct format
            # Remove any http:// prefix if present
            if recipient_address.startswith("http://"):
                recipient_address = recipient_address[7:]

            # If no port is specified, add port 5000
            if ":" not in recipient_address:
                recipient_address = f"{recipient_address}:5000"

            # Configure the requests session to use the Tor SOCKS proxy
            session = requests.Session()
            session.proxies = {
                'http': f'socks5h://127.0.0.1:{self.TOR_PORT}',
                'https': f'socks5h://127.0.0.1:{self.TOR_PORT}'
            }

            url = f"http://{recipient_address}/receive"
            self.logger.info(f"Sending message {message_id} to {url} through Tor proxy on port {self.TOR_PORT}")

            # Update status to 'sent' before sending
            if self.status_update_callback:
                self.logger.info(f"Calling status update callback for message {message_id}: sent")
                wx.CallAfter(self.status_update_callback, message_id, 'sent')

            # If pending_messages exists, update it
            if message_id in self.pending_messages:
                self.pending_messages[message_id]['status'] = 'sent'

            # Increase the timeout for Tor connections, which can be slow
            response = session.post(url, json=payload, timeout=60)

            if response.status_code == 200:
                self.logger.info(f"Message {message_id} delivered successfully")

                # Update status to 'delivered'
                if self.status_update_callback:
                    self.logger.info(f"Calling status update callback for message {message_id}: delivered")
                    wx.CallAfter(self.status_update_callback, message_id, 'delivered')

                # Update pending_messages
                if message_id in self.pending_messages:
                    self.pending_messages[message_id]['status'] = 'delivered'
                    self.pending_messages[message_id]['delivered_at'] = time.time()

                return True
            else:
                self.logger.error(f"Error sending message {message_id}: HTTP {response.status_code} - {response.text}")

                # Update status to 'failed'
                if self.status_update_callback:
                    self.logger.info(f"Calling status update callback for message {message_id}: failed")
                    wx.CallAfter(self.status_update_callback, message_id, 'failed')

                # Update pending_messages
                if message_id in self.pending_messages:
                    self.pending_messages[message_id]['status'] = 'failed'
                    self.pending_messages[message_id]['error'] = f"HTTP {response.status_code}"

                return False

        except requests.exceptions.Timeout:
            self.logger.error(
                f"Timeout connecting to {recipient_address}. Tor connection may be slow or the address is unreachable.")

            # Update status to 'timeout'
            if self.status_update_callback:
                self.logger.info(f"Calling status update callback for message {message_id}: timeout")
                wx.CallAfter(self.status_update_callback, message_id, 'timeout')

            # Update pending_messages
            if message_id in self.pending_messages:
                self.pending_messages[message_id]['status'] = 'timeout'

            return False

        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error: {e}. Check if the recipient address is correct and online.")

            # Update status to 'connection_error'
            if self.status_update_callback:
                self.logger.info(f"Calling status update callback for message {message_id}: connection_error")
                wx.CallAfter(self.status_update_callback, message_id, 'connection_error')

            # Update pending_messages
            if message_id in self.pending_messages:
                self.pending_messages[message_id]['status'] = 'connection_error'
                self.pending_messages[message_id]['error'] = str(e)

            return False

        except Exception as e:
            self.logger.error(f"Error sending message: {e}")

            # Update status to 'error'
            if self.status_update_callback:
                self.logger.info(f"Calling status update callback for message {message_id}: error")
                wx.CallAfter(self.status_update_callback, message_id, 'error')

            # Update pending_messages
            if message_id in self.pending_messages:
                self.pending_messages[message_id]['status'] = 'error'
                self.pending_messages[message_id]['error'] = str(e)

            import traceback
            traceback.print_exc()
            return False

    def encrypt_message(self, message, recipient_public_key):
        """Encrypt a message for a recipient"""
        try:
            recipient_key = PublicKey(recipient_public_key.encode(), encoder=HexEncoder)
            box = Box(self.private_key, recipient_key)
            encrypted = box.encrypt(message.encode(), encoder=HexEncoder)
            return encrypted.decode()
        except Exception as e:
            self.logger.error(f"Encryption error: {e}")
            raise

    def decrypt_message(self, encrypted_message, sender_public_key):
        """Decrypt a message from a sender"""
        try:
            sender_key = PublicKey(sender_public_key.encode(), encoder=HexEncoder)
            box = Box(self.private_key, sender_key)
            decrypted = box.decrypt(encrypted_message.encode(), encoder=HexEncoder)
            print("msggg")
            print(decrypted)
            return decrypted.decode()
        except Exception as e:
            self.logger.error(f"Decryption error: {e}")
            raise

    def get_message_status(self, message_id):
        """Get current status of a message by ID"""
        if message_id in self.pending_messages:
            return self.pending_messages[message_id]['status']
        return None

    def mark_as_read(self, message_id):
        """Mark a message as read"""
        if message_id in self.pending_messages and self.pending_messages[message_id]['status'] == 'delivered':
            self.pending_messages[message_id]['status'] = 'read'
            if self.status_update_callback:
                wx.CallAfter(self.status_update_callback, message_id, 'read')
            return True
        return False

    def close(self):
        """Clean up resources"""
        try:
            # Shutdown the thread pool
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=False)

            # Stop Tor service
            if hasattr(self, 'tor_service') and self.tor_service:
                self.tor_service.stop()

        except Exception as e:
            self.logger.error(f"Error closing TorMessenger: {e}")