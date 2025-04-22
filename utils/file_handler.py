import base64
import os
import shutil
import mimetypes
import hashlib
from PIL import Image
import appdirs


class FileHandler:
    def __init__(self, config):
        self.config = config
        self.app_name = "JustSocial"
        self.media_dir = os.path.join(appdirs.user_data_dir(self.app_name), "media")
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.media_dir,
            os.path.join(self.media_dir, "images"),
            os.path.join(self.media_dir, "videos"),
            os.path.join(self.media_dir, "documents"),
            os.path.join(self.media_dir, "voice"),
            os.path.join(self.media_dir, "temp")
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def save_attachment(self, file_path, file_type=None):
        """
        Save an attachment file to the appropriate directory
        Returns the new file path relative to the media directory
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Generate unique filename using hash of file content
        file_hash = self._get_file_hash(file_path)
        _, ext = os.path.splitext(file_path)
        new_filename = f"{file_hash}{ext}"

        # Determine file type and destination directory
        if not file_type:
            file_type = self._get_file_type(file_path)

        if file_type == 'image':
            dest_dir = os.path.join(self.media_dir, "images")
            # Create thumbnail
            self._create_thumbnail(file_path, file_hash)
        elif file_type == 'video':
            dest_dir = os.path.join(self.media_dir, "videos")
            # Create video thumbnail
            self._create_video_thumbnail(file_path, file_hash)
        else:
            dest_dir = os.path.join(self.media_dir, "documents")

        # Copy file to destination
        dest_path = os.path.join(dest_dir, new_filename)
        shutil.copy2(file_path, dest_path)

        return os.path.relpath(dest_path, self.media_dir)

    def get_thumbnail_path(self, file_path):
        """Get the thumbnail path for an image or video"""
        file_hash = self._get_file_hash(file_path)
        thumb_path = os.path.join(self.media_dir, "temp", f"{file_hash}_thumb.jpg")
        return thumb_path if os.path.exists(thumb_path) else None

    def _get_file_hash(self, file_path):
        """Generate SHA-256 hash of file content"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_file_type(self, file_path):
        """Determine file type based on mime type"""
        mime_type, _ = mimetypes.guess_type(file_path)

        if not mime_type:
            return 'document'

        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type == 'application/pdf':
            return 'pdf'
        else:
            return 'document'

    def _create_thumbnail(self, image_path, file_hash, size=(200, 200)):
        """Create a thumbnail for an image"""
        try:
            with Image.open(image_path) as img:
                img.thumbnail(size)
                thumb_path = os.path.join(self.media_dir, "temp", f"{file_hash}_thumb.jpg")
                img.save(thumb_path, "JPEG")
                return thumb_path
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return None

    def _create_video_thumbnail(self, video_path, file_hash):
        """Create a thumbnail for a video"""
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            if ret:
                thumb_path = os.path.join(self.media_dir, "temp", f"{file_hash}_thumb.jpg")
                cv2.imwrite(thumb_path, frame)
                cap.release()
                return thumb_path
        except Exception as e:
            print(f"Error creating video thumbnail: {e}")
            return None

    def cleanup_temp_files(self):
        """Clean up temporary files"""
        temp_dir = os.path.join(self.media_dir, "temp")
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting temporary file {file_path}: {e}")

    def save_sent_image(self, receiver_onion, image_data_base64, filename):
        dest_dir = os.path.join(self.media_dir, f"images/{receiver_onion}")
        image_data = base64.b64decode(image_data_base64)

        # Save the image
        file_path = os.path.join(dest_dir, filename)
        os.makedirs(dest_dir, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(image_data)
        print(f"sent image copied to:{file_path}")
        return file_path
