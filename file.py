#!/usr/bin/env python3
"""
Automatic Project Structure Creator for Candidate Registration System
Run this script to create the complete project structure and all files
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


class ProjectCreator:
    def __init__(self, project_name="candidate_registration"):
        self.project_name = project_name
        self.base_path = Path.cwd() / project_name

    def create_directory_structure(self):
        """Create all directories"""
        print(f"Creating project structure in: {self.base_path}")

        directories = [
            '',
            'templates',
            'static',
            'static/css',
            'static/js',
            'static/uploads',
            'static/uploads/photos',
            'static/uploads/videos',
            'static/uploads/documents',
            'venv'
        ]

        for directory in directories:
            dir_path = self.base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")

    def create_requirements_file(self):
        """Create requirements.txt"""
        content = """Flask==2.3.3
Flask-PyMongo==2.3.0
Flask-WTF==1.1.1
WTForms==3.0.1
python-dotenv==1.0.0
Pillow==10.0.0
pytesseract==0.3.10
opencv-python==4.8.0.74
werkzeug==2.3.7
APScheduler==3.10.4
email-validator==2.0.0
"""
        file_path = self.base_path / 'requirements.txt'
        file_path.write_text(content)
        print(f"Created: {file_path}")

    def create_config_file(self):
        """Create config.py"""
        content = '''import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # MongoDB configuration
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/candidate_registration'

    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

    # Allowed file extensions
    ALLOWED_PHOTO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

    # Tesseract path (update this according to your system)
    # Windows example: r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
    # Linux/Mac: usually just 'tesseract'
    TESSERACT_PATH = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'  # Change this
'''
        file_path = self.base_path / 'config.py'
        file_path.write_text(content)
        print(f"Created: {file_path}")

    def create_models_file(self):
        """Create models.py"""
        content = '''from datetime import datetime

class Candidate:
    def __init__(self, data=None):
        if data:
            self.id = data.get('_id')
            self.full_name = data.get('full_name', '')
            self.address_line1 = data.get('address_line1', '')
            self.address_line2 = data.get('address_line2', '')
            self.birthday = data.get('birthday', '')
            self.gender = data.get('gender', '')
            self.age = data.get('age', 0)
            self.current_job = data.get('current_job', '')
            self.email = data.get('email', '')
            self.mobile_no = data.get('mobile_no', '')
            self.nic_no = data.get('nic_no', '')
            self.nic_format = data.get('nic_format', '')
            self.passport_status = data.get('passport_status', 'Pending')
            self.passport_no = data.get('passport_no', '')
            self.job_title = data.get('job_title', '')
            self.visa_refusals = data.get('visa_refusals', False)
            self.visa_refusal_details = data.get('visa_refusal_details', '')

            # Media files
            self.photos = data.get('photos', [])
            self.videos = data.get('videos', [])
            self.passport_photo = data.get('passport_photo', '')
            self.nic_photo = data.get('nic_photo', '')

            # Payment details
            self.total_payment = data.get('total_payment', 0)
            self.payments = data.get('payments', [])
            self.remaining_payment = data.get('remaining_payment', 0)

            # Required documents
            self.documents = data.get('documents', {
                'police_report': 'Pending',
                'gs_report': 'Pending',
                'birth_certificate': 'Pending',
                'other': ''
            })

            # Pending items
            self.pending_documents = data.get('pending_documents', [])
            self.pending_payment = data.get('pending_payment', 0)

            # Follow-up
            self.follow_ups = data.get('follow_ups', [])
            self.created_at = data.get('created_at', datetime.now())
            self.updated_at = data.get('updated_at', datetime.now())

    def to_dict(self):
        return {
            'full_name': self.full_name,
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'birthday': self.birthday,
            'gender': self.gender,
            'age': self.age,
            'current_job': self.current_job,
            'email': self.email,
            'mobile_no': self.mobile_no,
            'nic_no': self.nic_no,
            'nic_format': self.nic_format,
            'passport_status': self.passport_status,
            'passport_no': self.passport_no,
            'job_title': self.job_title,
            'visa_refusals': self.visa_refusals,
            'visa_refusal_details': self.visa_refusal_details,
            'photos': self.photos,
            'videos': self.videos,
            'passport_photo': self.passport_photo,
            'nic_photo': self.nic_photo,
            'total_payment': self.total_payment,
            'payments': self.payments,
            'remaining_payment': self.remaining_payment,
            'documents': self.documents,
            'pending_documents': self.pending_documents,
            'pending_payment': self.pending_payment,
            'follow_ups': self.follow_ups,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class FollowUp:
    def __init__(self, data=None):
        if data:
            self.id = data.get('_id')
            self.candidate_id = data.get('candidate_id')
            self.follow_up_date = data.get('follow_up_date')
            self.follow_up_type = data.get('follow_up_type')
            self.notes = data.get('notes')
            self.status = data.get('status', 'Pending')
            self.created_at = data.get('created_at', datetime.now())

    def to_dict(self):
        return {
            'candidate_id': self.candidate_id,
            'follow_up_date': self.follow_up_date,
            'follow_up_type': self.follow_up_type,
            'notes': self.notes,
            'status': self.status,
            'created_at': self.created_at
        }

class Notification:
    def __init__(self, data=None):
        if data:
            self.id = data.get('_id')
            self.candidate_id = data.get('candidate_id')
            self.message = data.get('message')
            self.notification_type = data.get('notification_type')
            self.is_read = data.get('is_read', False)
            self.created_at = data.get('created_at', datetime.now())

    def to_dict(self):
        return {
            'candidate_id': self.candidate_id,
            'message': self.message,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'created_at': self.created_at
        }
'''
        file_path = self.base_path / 'models.py'
        file_path.write_text(content)
        print(f"Created: {file_path}")

    def create_utils_file(self):
        """Create utils.py"""
        content = '''import os
import re
import pytesseract
from PIL import Image
import cv2
import numpy as np
from datetime import datetime
from werkzeug.utils import secure_filename
from config import Config

class ImageTextExtractor:
    def __init__(self):
        # Configure Tesseract path
        pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_PATH

    def extract_text_from_image(self, image_path):
        """Extract text from image using Tesseract OCR"""
        try:
            # Read image using OpenCV
            img = cv2.imread(image_path)

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply thresholding to preprocess the image
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

            # Apply median blur
            gray = cv2.medianBlur(gray, 3)

            # Save temporary image
            temp_path = image_path.replace('.', '_processed.')
            cv2.imwrite(temp_path, gray)

            # Extract text using Tesseract
            text = pytesseract.image_to_string(Image.open(temp_path))

            # Clean up temporary file
            os.remove(temp_path)

            return text
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""

    def extract_passport_info(self, text):
        """Extract passport information from OCR text"""
        info = {
            'full_name': '',
            'passport_id': '',
            'birthday': '',
            'age': 0,
            'nic_no': ''
        }

        # Extract Name (adjust patterns based on passport format)
        name_patterns = [
            r'Name\\s*[:\\-]?\\s*([A-Z\\s]+)',
            r'Surname\\s*[:\\-]?\\s*([A-Z\\s]+)',
            r'Given\\s*Names?\\s*[:\\-]?\\s*([A-Z\\s]+)'
        ]

        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['full_name'] = match.group(1).strip()
                break

        # Extract Passport ID - Format: P1234567 or N1234567
        passport_pattern = r'[P|N]\\d{7}'
        match = re.search(passport_pattern, text)
        if match:
            info['passport_id'] = match.group()

        # Extract Birthday (DD/MM/YYYY)
        birthday_pattern = r'\\d{2}/\\d{2}/\\d{4}'
        match = re.search(birthday_pattern, text)
        if match:
            info['birthday'] = match.group()
            # Calculate age
            try:
                birth_date = datetime.strptime(info['birthday'], '%d/%m/%Y')
                today = datetime.now()
                info['age'] = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            except:
                pass

        # Extract NIC - Old format: 940730406V, New: 199407300406
        nic_old_pattern = r'\\d{9}[V|v]'
        nic_new_pattern = r'\\d{12}'

        match = re.search(nic_old_pattern, text)
        if match:
            info['nic_no'] = match.group()
        else:
            match = re.search(nic_new_pattern, text)
            if match:
                info['nic_no'] = match.group()

        return info

def save_uploaded_file(file, subfolder):
    """Save uploaded file and return the filename"""
    if file and file.filename:
        filename = secure_filename(file.filename)
        # Add timestamp to filename to make it unique
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_{timestamp}{ext}"

        # Create subfolder if it doesn't exist
        upload_path = os.path.join(Config.UPLOAD_FOLDER, subfolder)
        os.makedirs(upload_path, exist_ok=True)

        # Save file
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)

        return f"uploads/{subfolder}/{filename}"
    return None

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
'''
        file_path = self.base_path / 'utils.py'
        file_path.write_text(content)
        print(f"Created: {file_path}")

    def create_forms_file(self):
        """Create forms.py"""
        content = '''from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SelectField, BooleanField, DateField, FileField
from wtforms.validators import DataRequired, Email, Optional, Length, ValidationError
from flask_wtf.file import FileAllowed
import re

class CandidateForm(FlaskForm):
    # Personal Information
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=200)])
    address_line1 = StringField('Address Line 1', validators=[DataRequired(), Length(max=200)])
    address_line2 = StringField('Address Line 2', validators=[Optional(), Length(max=200)])
    birthday = StringField('Birthday (DD/MM/YYYY)', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    age = IntegerField('Age', validators=[Optional()])
    current_job = StringField('Current Job', validators=[Optional(), Length(max=200)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    mobile_no = StringField('Mobile No', validators=[DataRequired(), Length(max=20)])
    nic_no = StringField('NIC No', validators=[Optional(), Length(max=20)])

    # Passport Information
    passport_status = SelectField('Passport Status', 
                                 choices=[('Having', 'Having'), ('Pending', 'Pending'), ('Need Apply', 'Need Apply')],
                                 validators=[DataRequired()])
    passport_no = StringField('Passport No', validators=[Optional(), Length(max=20)])

    # Job Information
    job_title = SelectField('Job Title', choices=[('Skilled', 'Skilled'), ('Non-skilled', 'Non-skilled')],
                           validators=[DataRequired()])

    # Visa Information
    visa_refusals = SelectField('Visa Refusals', choices=[('No', 'No'), ('Yes', 'Yes')],
                               validators=[DataRequired()])
    visa_refusal_details = TextAreaField('Visa Refusal Details', validators=[Optional()])

    # Files
    photos = FileField('Candidate Photos (Max 4)', validators=[Optional()], render_kw={"multiple": True})
    videos = FileField('Candidate Videos (Max 3)', validators=[Optional()], render_kw={"multiple": True})
    passport_photo = FileField('Passport Photo', validators=[Optional()])
    nic_photo = FileField('NIC Photo', validators=[Optional()])

    # Payment
    total_payment = FloatField('Total Payment', validators=[Optional()])

    # Custom validation for passport number
    def validate_passport_no(self, field):
        if self.passport_status.data == 'Having':
            if not field.data:
                raise ValidationError('Passport number is required when passport status is "Having"')
            # Validate passport number format
            if not re.match(r'^[P|N]\\d{7}$', field.data):
                raise ValidationError('Passport number must be in format P1234567 or N1234567')

    # Custom validation for birthday format
    def validate_birthday(self, field):
        if field.data:
            if not re.match(r'^\\d{2}/\\d{2}/\\d{4}$', field.data):
                raise ValidationError('Birthday must be in DD/MM/YYYY format')

    # Custom validation for NIC
    def validate_nic_no(self, field):
        if field.data:
            # Old format: 9 digits + V
            if not re.match(r'^\\d{9}[V|v]$', field.data) and not re.match(r'^\\d{12}$', field.data):
                raise ValidationError('NIC must be in format 940730406V or 199407300406')
'''
        file_path = self.base_path / 'forms.py'
        file_path.write_text(content)
        print(f"Created: {file_path}")

    def create_app_file(self):
        """Create app.py"""
        content = '''from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_pymongo import PyMongo
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from apscheduler.schedulers.background import BackgroundScheduler
import os

from config import Config
from models import Candidate
from forms import CandidateForm
from utils import ImageTextExtractor, save_uploaded_file, allowed_file

app = Flask(__name__)
app.config.from_object(Config)

# Initialize MongoDB
mongo = PyMongo(app)

# Initialize OCR
ocr_extractor = ImageTextExtractor()

# Initialize scheduler for notifications
scheduler = BackgroundScheduler()
scheduler.start()

# Ensure upload folders exist
os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'photos'), exist_ok=True)
os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'videos'), exist_ok=True)
os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'documents'), exist_ok=True)

@app.route('/')
def index():
    """Dashboard with statistics"""
    total_candidates = mongo.db.candidates.count_documents({})

    # Payment statistics
    pipeline = [
        {"$group": {
            "_id": None,
            "total_payments": {"$sum": "$total_payment"},
            "total_remaining": {"$sum": "$remaining_payment"}
        }}
    ]
    payment_stats = list(mongo.db.candidates.aggregate(pipeline))
    total_payments = payment_stats[0]['total_payments'] if payment_stats else 0
    total_remaining = payment_stats[0]['total_remaining'] if payment_stats else 0

    pending_docs = mongo.db.candidates.count_documents({"pending_documents": {"$ne": []}})
    recent_candidates = list(mongo.db.candidates.find().sort('created_at', -1).limit(5))

    return render_template('index.html',
                         total_candidates=total_candidates,
                         total_payments=total_payments,
                         total_remaining=total_remaining,
                         pending_docs=pending_docs,
                         recent_candidates=recent_candidates)

@app.route('/section1', methods=['GET', 'POST'])
def section1():
    """Candidate registration form"""
    form = CandidateForm()
    return render_template('section1.html', form=form)

@app.route('/section2')
def section2():
    """Follow-ups and statistics dashboard"""
    candidates = list(mongo.db.candidates.find().sort('created_at', -1))
    return render_template('section2.html', candidates=candidates)

@app.route('/section3')
def section3():
    """Scheduler and notifications page"""
    return render_template('section3.html')

@app.route('/candidate/<candidate_id>')
def candidate_detail(candidate_id):
    """View candidate details"""
    candidate = mongo.db.candidates.find_one({'_id': ObjectId(candidate_id)})
    if candidate:
        return render_template('candidate_detail.html', candidate=candidate)
    flash('Candidate not found!', 'danger')
    return redirect(url_for('section2'))

if __name__ == '__main__':
    app.run(debug=True)
'''
        file_path = self.base_path / 'app.py'
        file_path.write_text(content)
        print(f"Created: {file_path}")

    def create_template_files(self):
        """Create all HTML template files"""
        templates = {
            'base.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Candidate Registration System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <div class="col-md-2 p-0">
                <div class="sidebar">
                    <div class="text-center py-4">
                        <i class="fas fa-user-tie fa-3x text-white"></i>
                        <h5 class="text-white mt-2">Visa Consultant</h5>
                    </div>
                    <nav class="nav flex-column">
                        <a class="nav-link {% if request.endpoint == 'index' %}active{% endif %}" href="{{ url_for('index') }}">
                            <i class="fas fa-tachometer-alt"></i> Dashboard
                        </a>
                        <a class="nav-link {% if request.endpoint == 'section1' %}active{% endif %}" href="{{ url_for('section1') }}">
                            <i class="fas fa-user-plus"></i> Section 1: Registration
                        </a>
                        <a class="nav-link {% if request.endpoint == 'section2' %}active{% endif %}" href="{{ url_for('section2') }}">
                            <i class="fas fa-chart-line"></i> Section 2: Follow-ups
                        </a>
                        <a class="nav-link {% if request.endpoint == 'section3' %}active{% endif %}" href="{{ url_for('section3') }}">
                            <i class="fas fa-bell"></i> Section 3: Alerts
                        </a>
                    </nav>
                </div>
            </div>

            <!-- Main Content -->
            <div class="col-md-10 main-content p-4">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}

                {% block content %}{% endblock %}
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>''',

            'index.html': '''{% extends "base.html" %}

{% block content %}
<div class="container-fluid">
    <h2 class="mb-4">Dashboard</h2>

    <div class="row mb-4">
        <div class="col-md-3">
            <div class="stat-card" style="background: linear-gradient(45deg, #2193b0, #6dd5ed);">
                <h3>{{ total_candidates }}</h3>
                <p>Total Candidates</p>
                <i class="fas fa-users stat-icon"></i>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card" style="background: linear-gradient(45deg, #ee0979, #ff6a00);">
                <h3>LKR {{ "{:,.0f}".format(total_payments) }}</h3>
                <p>Total Payments</p>
                <i class="fas fa-money-bill-wave stat-icon"></i>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card" style="background: linear-gradient(45deg, #11998e, #38ef7d);">
                <h3>LKR {{ "{:,.0f}".format(total_remaining) }}</h3>
                <p>Remaining Payments</p>
                <i class="fas fa-clock stat-icon"></i>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card" style="background: linear-gradient(45deg, #8e2de2, #4a00e0);">
                <h3>{{ pending_docs }}</h3>
                <p>Pending Documents</p>
                <i class="fas fa-file-alt stat-icon"></i>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5>Recent Candidates</h5>
                </div>
                <div class="card-body">
                    <div class="list-group">
                        {% for candidate in recent_candidates %}
                        <a href="{{ url_for('candidate_detail', candidate_id=candidate._id) }}" class="list-group-item list-group-item-action">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="mb-1">{{ candidate.full_name }}</h6>
                                    <small class="text-muted">{{ candidate.email }}</small>
                                </div>
                                <span class="badge bg-{{ 'success' if candidate.passport_status == 'Having' else 'warning' }}">
                                    {{ candidate.passport_status }}
                                </span>
                            </div>
                        </a>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}''',

            'section1.html': '''{% extends "base.html" %}

{% block content %}
<div class="container-fluid">
    <h2 class="mb-4">Section 1: Candidate Registration</h2>

    <div class="card">
        <div class="card-header">
            <h5>Registration Form</h5>
        </div>
        <div class="card-body">
            <form method="POST" enctype="multipart/form-data">
                {{ form.hidden_tag() }}

                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label>Full Name *</label>
                        {{ form.full_name(class="form-control") }}
                    </div>
                    <div class="col-md-6 mb-3">
                        <label>Email *</label>
                        {{ form.email(class="form-control") }}
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label>Address Line 1 *</label>
                        {{ form.address_line1(class="form-control") }}
                    </div>
                    <div class="col-md-6 mb-3">
                        <label>Address Line 2</label>
                        {{ form.address_line2(class="form-control") }}
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-3 mb-3">
                        <label>Birthday *</label>
                        {{ form.birthday(class="form-control", placeholder="DD/MM/YYYY") }}
                    </div>
                    <div class="col-md-3 mb-3">
                        <label>Gender *</label>
                        {{ form.gender(class="form-select") }}
                    </div>
                    <div class="col-md-3 mb-3">
                        <label>Mobile No *</label>
                        {{ form.mobile_no(class="form-control") }}
                    </div>
                </div>

                <button type="submit" class="btn btn-primary">Register Candidate</button>
            </form>
        </div>
    </div>
</div>
{% endblock %}''',

            'section2.html': '''{% extends "base.html" %}

{% block content %}
<div class="container-fluid">
    <h2 class="mb-4">Section 2: Follow-ups and Statistics</h2>

    <div class="card">
        <div class="card-header">
            <h5>Candidates List</h5>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Contact</th>
                            <th>Passport Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for candidate in candidates %}
                        <tr>
                            <td>{{ candidate.full_name }}</td>
                            <td>{{ candidate.mobile_no }}<br><small>{{ candidate.email }}</small></td>
                            <td>
                                <span class="badge bg-{{ 'success' if candidate.passport_status == 'Having' else 'warning' }}">
                                    {{ candidate.passport_status }}
                                </span>
                            </td>
                            <td>
                                <a href="{{ url_for('candidate_detail', candidate_id=candidate._id) }}" class="btn btn-sm btn-info">
                                    <i class="fas fa-eye"></i> View
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}''',

            'section3.html': '''{% extends "base.html" %}

{% block content %}
<div class="container-fluid">
    <h2 class="mb-4">Section 3: Scheduler and Alerts</h2>
    <div class="alert alert-info">
        <i class="fas fa-info-circle"></i> Scheduler and notifications will be implemented here.
    </div>
</div>
{% endblock %}''',

            'candidate_detail.html': '''{% extends "base.html" %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>Candidate Details</h2>
        <a href="{{ url_for('section2') }}" class="btn btn-secondary">
            <i class="fas fa-arrow-left"></i> Back
        </a>
    </div>

    <div class="row">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5>Personal Information</h5>
                </div>
                <div class="card-body">
                    <p><strong>Name:</strong> {{ candidate.full_name }}</p>
                    <p><strong>Email:</strong> {{ candidate.email }}</p>
                    <p><strong>Mobile:</strong> {{ candidate.mobile_no }}</p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
        }

        for filename, content in templates.items():
            file_path = self.base_path / 'templates' / filename
            file_path.write_text(content)
            print(f"Created template: {file_path}")

    def create_static_files(self):
        """Create CSS and JS files"""
        # CSS file
        css_content = '''/* Custom styles */
.sidebar {
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.sidebar .nav-link {
    color: rgba(255,255,255,.8);
    padding: 1rem;
    transition: all 0.3s;
}

.sidebar .nav-link:hover,
.sidebar .nav-link.active {
    color: white;
    background: rgba(255,255,255,.2);
    transform: translateX(5px);
}

.sidebar .nav-link i {
    margin-right: 10px;
}

.main-content {
    background: #f8f9fa;
    min-height: 100vh;
}

.stat-card {
    position: relative;
    border-radius: 10px;
    padding: 1.5rem;
    color: white;
    overflow: hidden;
    transition: transform 0.3s;
}

.stat-card:hover {
    transform: translateY(-5px);
}

.stat-icon {
    font-size: 3rem;
    opacity: 0.3;
    position: absolute;
    right: 1rem;
    top: 50%;
    transform: translateY(-50%);
}

.card {
    border: none;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    transition: all 0.3s;
}

.card:hover {
    box-shadow: 0 5px 20px rgba(0,0,0,0.15);
}

.card-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px 10px 0 0 !important;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
}

.btn-primary:hover {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}'''

        css_path = self.base_path / 'static' / 'css' / 'style.css'
        css_path.write_text(css_content)
        print(f"Created: {css_path}")

        # JS file
        js_content = '''// Common JavaScript functions

// Format currency
function formatCurrency(amount) {
    return 'LKR ' + amount.toFixed(2).replace(/\\d(?=(\\d{3})+\\.)/g, '$&,');
}

// Show loading spinner
function showLoading() {
    let spinner = document.createElement('div');
    spinner.className = 'spinner-overlay';
    spinner.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
    document.body.appendChild(spinner);
}

// Hide loading spinner
function hideLoading() {
    let spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.remove();
    }
}

// Show notification toast
function showToast(message, type = 'info') {
    let toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    document.body.appendChild(toast);
    let bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// Add spinner styles
const style = document.createElement('style');
style.textContent = `
    .spinner-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    }

    .toast {
        z-index: 10000;
    }
`;
document.head.appendChild(style);'''

        js_path = self.base_path / 'static' / 'js' / 'main.js'
        js_path.write_text(js_content)
        print(f"Created: {js_path}")

    def create_gitignore(self):
        """Create .gitignore file"""
        content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Flask
instance/
.webassets-cache

# Uploads
static/uploads/*

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Environment
.env
*.log
"""
        file_path = self.base_path / '.gitignore'
        file_path.write_text(content)
        print(f"Created: {file_path}")

    def create_readme(self):
        """Create README.md file"""
        content = """# Candidate Registration System

A Flask-based candidate registration system for visa consultant companies.

## Features

- Section 1: Candidate registration with photo/video upload and OCR
- Section 2: Follow-ups and statistics dashboard
- Section 3: Scheduler and alerts system

## Installation

1. Create virtual environment:
```bash
python -m venv venv
# Windows:
venv\\Scripts\\activate
# Linux/Mac:
source venv/bin/activate"""