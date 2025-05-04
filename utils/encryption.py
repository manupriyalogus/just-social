from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import padding
import base64
import os


class MessageEncryption:
    def __init__(self, key=None):
        """Initialize encryption with an optional key"""
        if key:
            self.key = base64.urlsafe_b64decode(key)
        else:
            self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)

    @classmethod
    def generate_key(cls):
        """Generate a new encryption key"""
        return base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')

    def encrypt_message(self, message):
        """Encrypt a message"""
        if isinstance(message, str):
            message = message.encode()
        return self.fernet.encrypt(message)

    def decrypt_message(self, encrypted_message):
        """Decrypt a message"""
        try:
            decrypted = self.fernet.decrypt(encrypted_message)
            return decrypted.decode()
        except Exception as e:
            print(f"Error decrypting message: {e}")
            return None

    def encrypt_file(self, file_path, output_path=None):
        """Encrypt a file"""
        if not output_path:
            output_path = file_path + '.encrypted'

        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()

            encrypted_data = self.fernet.encrypt(file_data)

            with open(output_path, 'wb') as file:
                file.write(encrypted_data)

            return output_path
        except Exception as e:
            print(f"Error encrypting file: {e}")
            return None

    def decrypt_file(self, encrypted_file_path, output_path=None):
        """Decrypt a file"""
        if not output_path:
            output_path = encrypted_file_path.replace('.encrypted', '')

        try:
            with open(encrypted_file_path, 'rb') as file:
                encrypted_data = file.read()

            decrypted_data = self.fernet.decrypt(encrypted_data)

            with open(output_path, 'wb') as file:
                file.write(decrypted_data)

            return output_path
        except Exception as e:
            print(f"Error decrypting file: {e}")
            return None


class E2EEncryption:
    """End-to-End Encryption implementation"""

    def __init__(self):
        self.private_key = None
        self.public_key = None

    def generate_keypair(self):
        """Generate public/private key pair"""
        from cryptography.hazmat.primitives.asymmetric import rsa
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        self.private_key = private_key
        self.public_key = public_key
        return private_key, public_key

    def encrypt_message(self, message, recipient_public_key):
        """Encrypt a message using recipient's public key"""
        try:
            encrypted = recipient_public_key.encrypt(
                message.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return base64.b64encode(encrypted)
        except Exception as e:
            print(f"Error in E2E encryption: {e}")
            return None

    def decrypt_message(self, encrypted_message):
        """Decrypt a message using own private key"""
        if not self.private_key:
            raise ValueError("Private key not initialized")

        try:
            decrypted = self.private_key.decrypt(
                base64.b64decode(encrypted_message),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted.decode()
        except Exception as e:
            print(f"Error in E2E decryption: {e}")
            return None

    def export_public_key(self):
        """Export public key in PEM format"""
        from cryptography.hazmat.primitives import serialization

        if not self.public_key:
            raise ValueError("Public key not initialized")

        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem

    def import_public_key(self, pem_data):
        """Import public key from PEM format"""
        from cryptography.hazmat.primitives import serialization

        try:
            public_key = serialization.load_pem_public_key(pem_data)
            return public_key
        except Exception as e:
            print(f"Error importing public key: {e}")
            return None
