import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # MongoDB configuration
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/candidate_registration'

    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

    # Allowed file extensions - Define these FIRST
    ALLOWED_PHOTO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'rtf'}

    # Combined allowed extensions for all file types (defined AFTER the individual sets)
    ALLOWED_EXTENSIONS = ALLOWED_PHOTO_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

    # Tesseract path (update this according to your system)
    # Windows example: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    # Linux/Mac: usually just 'tesseract'
    TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Change this