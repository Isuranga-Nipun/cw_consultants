from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_pymongo import PyMongo
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from apscheduler.schedulers.background import BackgroundScheduler
import os
import re
import calendar
from werkzeug.utils import secure_filename

from config import Config
from models import Candidate, FollowUp, Notification
from forms import CandidateForm
from utils import HybridOCR, save_uploaded_file, allowed_file

app = Flask(__name__)
app.config.from_object(Config)

# Initialize MongoDB
mongo = PyMongo(app)

# Initialize Hybrid OCR (CNN + Tesseract)
ocr_engine = HybridOCR(cnn_model_path='models/final_Attention_CNN_V4.h5')

# Initialize scheduler for notifications
scheduler = BackgroundScheduler()
scheduler.start()

# Ensure upload folders exist
os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'photos'), exist_ok=True)
os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'videos'), exist_ok=True)
os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'documents'), exist_ok=True)


# ==================== Context Processor ====================

@app.context_processor
def utility_processor():
    """Make notifications available to all templates"""
    notifications = list(mongo.db.notifications.find({'is_read': False}).sort('created_at', -1).limit(10))
    return dict(notifications=notifications, now=datetime.now())


# ==================== Routes ====================

@app.route('/')
def index():
    """Dashboard with statistics"""
    # Get all candidates for statistics
    all_candidates = list(mongo.db.candidates.find())
    total_candidates = len(all_candidates)

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

    # Pending documents count
    pending_docs = mongo.db.candidates.count_documents({"pending_documents": {"$ne": []}})

    # Recent candidates (last 5)
    recent_candidates = list(mongo.db.candidates.find().sort('created_at', -1).limit(5))

    # Gender statistics
    male_count = mongo.db.candidates.count_documents({'gender': 'Male'})
    female_count = mongo.db.candidates.count_documents({'gender': 'Female'})
    gender_stats = {
        'male': male_count,
        'female': female_count
    }

    # Job title statistics
    skilled_count = mongo.db.candidates.count_documents({'job_title': 'Skilled'})
    non_skilled_count = mongo.db.candidates.count_documents({'job_title': 'Non-skilled'})
    job_stats = {
        'skilled': skilled_count,
        'non_skilled': non_skilled_count
    }

    # Passport status statistics
    passport_having = mongo.db.candidates.count_documents({'passport_status': 'Having'})
    passport_pending = mongo.db.candidates.count_documents({'passport_status': 'Pending'})
    passport_need_apply = mongo.db.candidates.count_documents({'passport_status': 'Need Apply'})
    passport_stats = {
        'having': passport_having,
        'pending': passport_pending,
        'need_apply': passport_need_apply
    }

    # Document statistics
    police_report_pending = 0
    gs_report_pending = 0
    birth_certificate_pending = 0

    for candidate in all_candidates:
        if candidate.get('documents', {}).get('police_report') == 'Pending':
            police_report_pending += 1
        if candidate.get('documents', {}).get('gs_report') == 'Pending':
            gs_report_pending += 1
        if candidate.get('documents', {}).get('birth_certificate') == 'Pending':
            birth_certificate_pending += 1

    document_stats = {
        'police_report_pending': police_report_pending,
        'gs_report_pending': gs_report_pending,
        'birth_certificate_pending': birth_certificate_pending
    }

    # Follow-ups statistics
    now_dt = datetime.now()
    today_start = datetime.combine(now_dt.date(), datetime.min.time())
    today_end = datetime.combine(now_dt.date(), datetime.max.time())

    # Today's follow-ups
    today_followups = list(mongo.db.follow_ups.find({
        "follow_up_date": {"$gte": today_start, "$lte": today_end},
        "status": "Pending"
    }))

    # Upcoming follow-ups (next 7 days, excluding today)
    upcoming_start = today_end + timedelta(seconds=1)
    upcoming_end = today_start + timedelta(days=8)
    upcoming_followups = list(mongo.db.follow_ups.find({
        "follow_up_date": {"$gte": upcoming_start, "$lte": upcoming_end},
        "status": "Pending"
    }))

    # Missed follow-ups (past, not completed)
    missed_followups = list(mongo.db.follow_ups.find({
        "follow_up_date": {"$lt": today_start},
        "status": "Pending"
    }))

    # Get candidate names for followups
    for fu in today_followups + upcoming_followups + missed_followups:
        candidate = mongo.db.candidates.find_one({'_id': fu['candidate_id']})
        fu['candidate_name'] = candidate['full_name'] if candidate else 'Unknown'

    # Calculate monthly registrations data for the chart
    monthly_reg_data = [0] * 12
    for candidate in all_candidates:
        if candidate.get('created_at'):
            month = candidate['created_at'].month - 1  # 0-based index
            monthly_reg_data[month] += 1

    # Get current month for "This Month" display
    current_month = now_dt.month - 1  # 0-based index
    this_month_count = monthly_reg_data[current_month]

    return render_template('index.html',
                           total_candidates=total_candidates,
                           total_payments=total_payments,
                           total_remaining=total_remaining,
                           pending_docs=pending_docs,
                           recent_candidates=recent_candidates,
                           all_candidates=all_candidates,
                           gender_stats=gender_stats,
                           job_stats=job_stats,
                           passport_stats=passport_stats,
                           document_stats=document_stats,
                           today_followups=today_followups,
                           upcoming_followups=upcoming_followups,
                           missed_followups=missed_followups,
                           today_count=len(today_followups),
                           upcoming_count=len(upcoming_followups),
                           missed_count=len(missed_followups),
                           monthlyRegData=monthly_reg_data,
                           this_month_count=this_month_count)


# Add this new route for rescheduling follow-ups
@app.route('/update_followup_date/<followup_id>', methods=['POST'])
def update_followup_date(followup_id):
    """Update follow-up date"""
    try:
        new_date = request.json.get('follow_up_date')
        if new_date:
            follow_up_date = datetime.strptime(new_date, '%Y-%m-%dT%H:%M')
            mongo.db.follow_ups.update_one(
                {'_id': ObjectId(followup_id)},
                {'$set': {'follow_up_date': follow_up_date, 'status': 'Pending'}}
            )
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error updating follow-up date: {e}")
    return jsonify({'success': False}), 500


@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


# ==================== Section 1: Candidate Registration ====================

@app.route('/section1', methods=['GET', 'POST'])
def section1():
    """Candidate registration form with CNN OCR"""
    form = CandidateForm()

    if request.method == 'POST':
        print(f"Form data: {request.form}")
        print(f"Files: {request.files}")

        if form.validate_on_submit():
            try:
                # Process uploaded files
                photos = []
                if request.files.getlist('photos'):
                    for photo in request.files.getlist('photos')[:4]:
                        if photo and allowed_file(photo.filename, Config.ALLOWED_PHOTO_EXTENSIONS):
                            filepath = save_uploaded_file(photo, 'photos')
                            if filepath:
                                photos.append(filepath)

                # Process uploaded files - Videos section
                videos = []
                if request.files.getlist('videos'):
                    for video in request.files.getlist('videos')[:3]:  # Max 3 videos
                        if video and allowed_file(video.filename, Config.ALLOWED_VIDEO_EXTENSIONS):
                            filepath = save_uploaded_file(video, 'videos')
                            if filepath:
                                videos.append(filepath)
                                print(f"✅ Video saved: {filepath}")  # Add this debug line
                    print(f"📹 Total videos uploaded: {len(videos)}")  # Add this debug line

                # Process passport photo with CNN OCR
                passport_photo = None
                passport_info = {}
                if request.files.get('passport_photo'):
                    passport_file = request.files['passport_photo']
                    if passport_file and allowed_file(passport_file.filename, Config.ALLOWED_PHOTO_EXTENSIONS):
                        passport_photo = save_uploaded_file(passport_file, 'documents')

                        # Extract text using Hybrid OCR
                        if passport_photo:
                            full_path = os.path.join(app.root_path, 'static', passport_photo)
                            passport_info = ocr_engine.extract_text_from_passport(full_path)
                            print(f"📸 OCR extracted: {passport_info}")

                # Process NIC photo
                nic_photo = None
                nic_info = {}
                if request.files.get('nic_photo'):
                    nic_file = request.files['nic_photo']
                    if nic_file and allowed_file(nic_file.filename, Config.ALLOWED_PHOTO_EXTENSIONS):
                        nic_photo = save_uploaded_file(nic_file, 'documents')

                        # Extract NIC info
                        if nic_photo:
                            full_path = os.path.join(app.root_path, 'static', nic_photo)
                            nic_result = ocr_engine.extract_from_document(full_path, 'nic')
                            if nic_result.get('success'):
                                nic_info = {'nic_no': nic_result.get('raw_prediction', '')}
                            else:
                                # Fallback to Tesseract
                                text = ocr_engine.tesseract.extract_text_from_image(full_path)
                                nic_match = re.search(r'\d{9}[V|v]|\d{12}', text)
                                nic_info = {'nic_no': nic_match.group() if nic_match else ''}

                # Handle document file uploads (Police Report, GS Report, Birth Certificate)
                # Define allowed extensions for documents
                allowed_doc_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'pdf', 'doc', 'docx'}

                police_report_file = None
                if request.files.get('police_report_file'):
                    file = request.files['police_report_file']
                    if file and file.filename:
                        if allowed_file(file.filename, allowed_doc_extensions):
                            police_report_file = save_uploaded_file(file, 'documents')
                            print(f"Police Report file saved: {police_report_file}")

                gs_report_file = None
                if request.files.get('gs_report_file'):
                    file = request.files['gs_report_file']
                    if file and file.filename:
                        if allowed_file(file.filename, allowed_doc_extensions):
                            gs_report_file = save_uploaded_file(file, 'documents')
                            print(f"GS Report file saved: {gs_report_file}")

                birth_certificate_file = None
                if request.files.get('birth_certificate_file'):
                    file = request.files['birth_certificate_file']
                    if file and file.filename:
                        if allowed_file(file.filename, allowed_doc_extensions):
                            birth_certificate_file = save_uploaded_file(file, 'documents')
                            print(f"Birth Certificate file saved: {birth_certificate_file}")

                # Combine extracted information
                full_name = form.full_name.data
                if not full_name and passport_info.get('full_name'):
                    full_name = passport_info['full_name']

                surname = request.form.get('surname', '')
                if not surname and passport_info.get('surname'):
                    surname = passport_info['surname']

                other_names = request.form.get('other_names', '')
                if not other_names and passport_info.get('other_names'):
                    other_names = passport_info['other_names']
                elif not other_names and passport_info.get('given_name'):
                    other_names = passport_info['given_name']

                birthday = form.birthday.data
                if not birthday and passport_info.get('birthday'):
                    birthday = passport_info['birthday']

                nic_no = form.nic_no.data
                if not nic_no:
                    if passport_info.get('nic_no'):
                        nic_no = passport_info['nic_no']
                    elif nic_info.get('nic_no'):
                        nic_no = nic_info['nic_no']

                passport_no = form.passport_no.data
                if not passport_no and passport_info.get('passport_id'):
                    passport_no = passport_info['passport_id']

                # Validate NIC format
                nic_format = 'Unknown'
                if nic_no:
                    if re.match(r'^\d{9}[V|v]$', nic_no):
                        nic_format = 'Old Format'
                    elif re.match(r'^\d{12}$', nic_no):
                        nic_format = 'New Format'

                # Prepare documents dictionary with file paths
                documents = {
                    'police_report': request.form.get('police_report', 'Pending'),
                    'police_report_file': police_report_file,
                    'gs_report': request.form.get('gs_report', 'Pending'),
                    'gs_report_file': gs_report_file,
                    'birth_certificate': request.form.get('birth_certificate', 'Pending'),
                    'birth_certificate_file': birth_certificate_file,
                    'other': request.form.get('other_doc', '')
                }

                # Determine pending documents
                pending_docs = []
                if documents['police_report'] == 'Pending':
                    pending_docs.append('Police Report')
                if documents['gs_report'] == 'Pending':
                    pending_docs.append('GS Report')
                if documents['birth_certificate'] == 'Pending':
                    pending_docs.append('Birth Certificate')
                if form.passport_status.data != 'Having':
                    pending_docs.append('Passport')

                # Prepare candidate data with ALL required fields
                candidate_data = {
                    'full_name': full_name,
                    'surname': surname,
                    'other_names': other_names,
                    'address_line1': form.address_line1.data,
                    'address_line2': form.address_line2.data,
                    'birthday': birthday,
                    'gender': form.gender.data,
                    'age': form.age.data or passport_info.get('age', 0),
                    'current_job': form.current_job.data,
                    'email': form.email.data,
                    'mobile_no': form.mobile_no.data,
                    'nic_no': nic_no,
                    'nic_format': nic_format,
                    'passport_status': form.passport_status.data,
                    'passport_no': passport_no,
                    'job_title': form.job_title.data,
                    'visa_refusals': form.visa_refusals.data == 'Yes',
                    'visa_refusal_details': form.visa_refusal_details.data if form.visa_refusals.data == 'Yes' else '',
                    'photos': photos,
                    'videos': videos,
                    'passport_photo': passport_photo,
                    'nic_photo': nic_photo,
                    'total_payment': float(form.total_payment.data) if form.total_payment.data else 0,
                    'payments': [],
                    'remaining_payment': float(form.total_payment.data) if form.total_payment.data else 0,
                    'documents': documents,
                    'pending_documents': pending_docs,
                    'pending_payment': float(form.total_payment.data) if form.total_payment.data else 0,
                    'follow_ups': [],
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }

                # Insert into database
                result = mongo.db.candidates.insert_one(candidate_data)

                # Create notification
                notification = {
                    'candidate_id': result.inserted_id,
                    'message': f"New candidate registered: {candidate_data['full_name']}",
                    'notification_type': 'new_candidate',
                    'is_read': False,
                    'created_at': datetime.now()
                }
                mongo.db.notifications.insert_one(notification)

                flash('Candidate registered successfully!', 'success')
                return redirect(url_for('section1'))

            except Exception as e:
                flash(f'Error registering candidate: {str(e)}', 'danger')
                print(f"Registration error: {str(e)}")
                import traceback
                traceback.print_exc()

    return render_template('section1.html', form=form)


# ==================== Section 2: Follow-ups and Statistics ====================

@app.route('/section2')
def section2():
    """Follow-ups and statistics dashboard with complete stats"""
    # Get all candidates
    candidates = list(mongo.db.candidates.find().sort('created_at', -1))

    # Get all follow-ups
    follow_ups = list(mongo.db.follow_ups.find().sort('follow_up_date', -1))

    # Get follow-ups for each candidate
    for candidate in candidates:
        candidate['follow_ups'] = list(mongo.db.follow_ups.find({
            'candidate_id': candidate['_id']
        }).sort('follow_up_date', -1))

    # Calculate comprehensive statistics
    total_candidates = len(candidates)

    # Gender distribution
    male_count = mongo.db.candidates.count_documents({'gender': 'Male'})
    female_count = mongo.db.candidates.count_documents({'gender': 'Female'})

    # Job title distribution
    skilled_count = mongo.db.candidates.count_documents({'job_title': 'Skilled'})
    non_skilled_count = mongo.db.candidates.count_documents({'job_title': 'Non-skilled'})

    # Passport status
    passport_having = mongo.db.candidates.count_documents({'passport_status': 'Having'})
    passport_pending = mongo.db.candidates.count_documents({'passport_status': 'Pending'})
    passport_need_apply = mongo.db.candidates.count_documents({'passport_status': 'Need Apply'})

    # Payment statistics
    total_collected = 0
    total_remaining_sum = 0
    for c in candidates:
        paid = c.get('total_payment', 0) - c.get('remaining_payment', 0)
        total_collected += paid
        total_remaining_sum += c.get('remaining_payment', 0)

    # Document statistics
    police_report_pending = sum(1 for c in candidates if c.get('documents', {}).get('police_report') == 'Pending')
    gs_report_pending = sum(1 for c in candidates if c.get('documents', {}).get('gs_report') == 'Pending')
    birth_certificate_pending = sum(
        1 for c in candidates if c.get('documents', {}).get('birth_certificate') == 'Pending')

    # Monthly registrations
    monthly_stats = list(mongo.db.candidates.aggregate([
        {
            "$group": {
                "_id": {"$month": "$created_at"},
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]))

    # Prepare stats dictionary for template
    stats = {
        'total_candidates': total_candidates,
        'gender_distribution': {
            'male': male_count,
            'female': female_count
        },
        'job_title_distribution': {
            'skilled': skilled_count,
            'non_skilled': non_skilled_count
        },
        'passport_status': {
            'having': passport_having,
            'pending': passport_pending,
            'need_apply': passport_need_apply
        },
        'payment_stats': {
            'total_collected': total_collected,
            'total_remaining': total_remaining_sum
        },
        'document_stats': {
            'police_report_pending': police_report_pending,
            'gs_report_pending': gs_report_pending,
            'birth_certificate_pending': birth_certificate_pending
        },
        'monthly_registrations': monthly_stats
    }

    print(f"📊 Stats calculated: {stats}")  # Debug print

    return render_template('section2.html', candidates=candidates, follow_ups=follow_ups, stats=stats)


# ==================== Section 3: Scheduler and Notifications ====================

@app.route('/section3')
def section3():
    """Scheduler and notifications page"""
    # Get all upcoming follow-ups
    upcoming_followups = list(mongo.db.follow_ups.find({
        'follow_up_date': {'$gte': datetime.now()},
        'status': 'Pending'
    }).sort('follow_up_date', 1).limit(20))

    # Get candidate names for follow-ups
    for fu in upcoming_followups:
        candidate = mongo.db.candidates.find_one({'_id': fu['candidate_id']})
        fu['candidate_name'] = candidate['full_name'] if candidate else 'Unknown'

    # Get unread notifications
    notifications = list(mongo.db.notifications.find({
        'is_read': False
    }).sort('created_at', -1))

    # Get follow-ups for today
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    today_followups = list(mongo.db.follow_ups.find({
        'follow_up_date': {
            '$gte': datetime.combine(today, datetime.min.time()),
            '$lt': datetime.combine(tomorrow, datetime.min.time())
        },
        'status': 'Pending'
    }))

    for fu in today_followups:
        candidate = mongo.db.candidates.find_one({'_id': fu['candidate_id']})
        fu['candidate_name'] = candidate['full_name'] if candidate else 'Unknown'

    return render_template('section3.html',
                           upcoming_followups=upcoming_followups,
                           notifications=notifications,
                           today_followups=today_followups)


# ==================== Candidate Details ====================

@app.route('/candidate/<candidate_id>')
def candidate_detail(candidate_id):
    """View candidate details"""
    try:
        candidate = mongo.db.candidates.find_one({'_id': ObjectId(candidate_id)})
        if candidate:
            # Get follow-ups for this candidate
            candidate['follow_ups'] = list(mongo.db.follow_ups.find({
                'candidate_id': ObjectId(candidate_id)
            }).sort('follow_up_date', -1))

            # Ensure all required fields exist
            if 'payments' not in candidate:
                candidate['payments'] = []
            if 'follow_ups' not in candidate:
                candidate['follow_ups'] = []
            if 'documents' not in candidate:
                candidate['documents'] = {
                    'police_report': 'Pending',
                    'police_report_file': None,
                    'gs_report': 'Pending',
                    'gs_report_file': None,
                    'birth_certificate': 'Pending',
                    'birth_certificate_file': None,
                    'other': ''
                }

            return render_template('candidate_detail.html', candidate=candidate)
        else:
            flash('Candidate not found!', 'danger')
            return redirect(url_for('section2'))
    except Exception as e:
        flash(f'Error loading candidate: {str(e)}', 'danger')
        print(f"Error in candidate_detail: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('section2'))


# ==================== Payment Routes ====================

@app.route('/add_payment/<candidate_id>', methods=['POST'])
def add_payment(candidate_id):
    """Add payment installment for candidate"""
    try:
        payment_type = request.form.get('payment_type')
        amount = float(request.form.get('amount', 0))

        candidate = mongo.db.candidates.find_one({'_id': ObjectId(candidate_id)})
        if candidate:
            payment = {
                'type': payment_type,
                'amount': amount,
                'date': datetime.now(),
                'description': request.form.get('description', '')
            }

            mongo.db.candidates.update_one(
                {'_id': ObjectId(candidate_id)},
                {
                    '$push': {'payments': payment},
                    '$inc': {'remaining_payment': -amount, 'pending_payment': -amount}
                }
            )

            # Create notification for payment
            notification = {
                'candidate_id': ObjectId(candidate_id),
                'message': f"Payment of LKR {amount:,.0f} added for {candidate['full_name']}",
                'notification_type': 'payment_added',
                'is_read': False,
                'created_at': datetime.now()
            }
            mongo.db.notifications.insert_one(notification)

            flash('Payment added successfully!', 'success')
        else:
            flash('Candidate not found!', 'danger')
    except Exception as e:
        flash(f'Error adding payment: {str(e)}', 'danger')
        print(f"Payment error: {e}")
        import traceback
        traceback.print_exc()

    return redirect(url_for('candidate_detail', candidate_id=candidate_id))


# ==================== Follow-up Routes ====================

@app.route('/add_followup/<candidate_id>', methods=['POST'])
def add_followup(candidate_id):
    """Add follow-up for candidate"""
    try:
        follow_up_date = request.form.get('follow_up_date')
        if not follow_up_date:
            flash('Follow-up date is required!', 'danger')
            return redirect(url_for('candidate_detail', candidate_id=candidate_id))

        # Parse the datetime
        follow_up_date = datetime.strptime(follow_up_date, '%Y-%m-%dT%H:%M')
        follow_up_type = request.form.get('follow_up_type')
        notes = request.form.get('notes')

        if not follow_up_type:
            flash('Follow-up type is required!', 'danger')
            return redirect(url_for('candidate_detail', candidate_id=candidate_id))

        follow_up = {
            'candidate_id': ObjectId(candidate_id),
            'follow_up_date': follow_up_date,
            'follow_up_type': follow_up_type,
            'notes': notes,
            'status': 'Pending',
            'created_at': datetime.now()
        }

        result = mongo.db.follow_ups.insert_one(follow_up)

        candidate = mongo.db.candidates.find_one({'_id': ObjectId(candidate_id)})
        if candidate:
            notification = {
                'candidate_id': ObjectId(candidate_id),
                'message': f"Follow-up scheduled for {candidate['full_name']} on {follow_up_date.strftime('%d/%m/%Y %H:%M')}",
                'notification_type': 'follow_up',
                'is_read': False,
                'created_at': datetime.now()
            }
            mongo.db.notifications.insert_one(notification)

        flash('Follow-up added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding follow-up: {str(e)}', 'danger')
        print(f"Follow-up error: {e}")
        import traceback
        traceback.print_exc()

    return redirect(url_for('candidate_detail', candidate_id=candidate_id))


# ==================== Notification Routes ====================

@app.route('/mark_notification_read/<notification_id>')
def mark_notification_read(notification_id):
    """Mark notification as read"""
    mongo.db.notifications.update_one(
        {'_id': ObjectId(notification_id)},
        {'$set': {'is_read': True}}
    )
    return jsonify({'success': True})


@app.route('/update_followup_status/<followup_id>', methods=['POST'])
def update_followup_status(followup_id):
    """Update follow-up status"""
    status = request.json.get('status')
    mongo.db.follow_ups.update_one(
        {'_id': ObjectId(followup_id)},
        {'$set': {'status': status}}
    )
    return jsonify({'success': True})


# ==================== API Endpoint for OCR Testing ====================

@app.route('/api/ocr-test', methods=['POST'])
def api_ocr_test():
    """API endpoint to test OCR on uploaded image with detailed error handling"""
    try:
        print("=" * 50)
        print("OCR API CALLED")
        print("=" * 50)

        # Check if image is in request
        if 'image' not in request.files:
            print("ERROR: No image in request")
            return jsonify({
                'success': False,
                'error': 'No image provided',
                'debug': 'image field missing'
            }), 400

        file = request.files['image']
        doc_type = request.form.get('doc_type', 'passport')

        print(f"File received: {file.filename}")
        print(f"Content type: {file.content_type}")
        print(f"Document type: {doc_type}")

        # Check if file is valid
        if not file or file.filename == '':
            print("ERROR: Empty filename")
            return jsonify({
                'success': False,
                'error': 'Empty file',
                'debug': 'filename is empty'
            }), 400

        # Check file extension
        if not allowed_file(file.filename, Config.ALLOWED_PHOTO_EXTENSIONS):
            print(f"ERROR: Invalid file extension: {file.filename}")
            return jsonify({
                'success': False,
                'error': 'Invalid file type',
                'debug': f'Allowed extensions: {Config.ALLOWED_PHOTO_EXTENSIONS}'
            }), 400

        # Create temp directory if it doesn't exist
        temp_dir = os.path.join(Config.UPLOAD_FOLDER, 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        # Save file with unique name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"temp_{timestamp}_{secure_filename(file.filename)}"
        temp_path = os.path.join(temp_dir, safe_filename)

        print(f"Saving to: {temp_path}")
        file.save(temp_path)

        # Check if file was saved
        if not os.path.exists(temp_path):
            print("ERROR: File was not saved")
            return jsonify({
                'success': False,
                'error': 'Failed to save file',
                'debug': 'file save failed'
            }), 500

        file_size = os.path.getsize(temp_path)
        print(f"File saved successfully. Size: {file_size} bytes")

        # Process with OCR based on document type
        try:
            if doc_type == 'passport':
                print("Processing passport with OCR...")
                result = ocr_engine.extract_text_from_passport(temp_path)
                print(f"Passport OCR result: {result}")

                # Ensure we have a dictionary
                if result is None:
                    result = {}

                response_data = {
                    'success': True,
                    'full_name': result.get('full_name', ''),
                    'surname': result.get('surname', ''),
                    'other_names': result.get('other_names', ''),
                    'given_name': result.get('given_name', ''),
                    'passport_id': result.get('passport_id', ''),
                    'birthday': result.get('birthday', ''),
                    'age': result.get('age', 0),
                    'nic_no': result.get('nic_no', ''),
                    'doc_type': doc_type,
                    'debug': 'processed with passport OCR'
                }
            else:
                print(f"Processing {doc_type} with document OCR...")
                result = ocr_engine.extract_from_document(temp_path, doc_type)
                print(f"Document OCR result: {result}")

                if result is None:
                    result = {'success': False, 'error': 'No result from OCR engine'}

                response_data = {
                    'success': result.get('success', False),
                    'raw_prediction': result.get('raw_prediction', ''),
                    'confidence': result.get('confidence', 0),
                    'alternatives': result.get('alternatives', []),
                    'needs_review': result.get('needs_review', False),
                    'doc_type': doc_type,
                    'debug': 'processed with document OCR'
                }

            # Clean up temp file
            try:
                os.remove(temp_path)
                print(f"Temp file removed: {temp_path}")
            except Exception as e:
                print(f"Warning: Could not remove temp file: {e}")

            print(f"Sending response: {response_data}")
            return jsonify(response_data)

        except Exception as e:
            print(f"ERROR during OCR processing: {str(e)}")
            import traceback
            traceback.print_exc()

            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

            return jsonify({
                'success': False,
                'error': f'OCR processing failed: {str(e)}',
                'debug': 'exception in OCR processing',
                'traceback': traceback.format_exc()
            }), 500

    except Exception as e:
        print(f"UNHANDLED EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}',
            'debug': 'unhandled exception'
        }), 500


# ==================== Debug Routes ====================

@app.route('/debug/routes')
def debug_routes():
    """List all registered routes (for debugging)"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': str(rule)
        })
    return jsonify(routes)


@app.route('/test_db')
def test_db():
    """Test database connection"""
    try:
        test_id = mongo.db.test.insert_one({'test': 'connection', 'time': datetime.now()}).inserted_id
        test_doc = mongo.db.test.find_one({'_id': test_id})
        mongo.db.test.delete_one({'_id': test_id})

        return jsonify({
            'status': 'success',
            'message': 'MongoDB connection working!',
            'test_doc': str(test_doc)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'MongoDB connection failed: {str(e)}'
        }), 500


# Scheduled job to check for follow-ups
@scheduler.scheduled_job('interval', hours=1)
def check_followups():
    """Check for upcoming follow-ups and create notifications"""
    with app.app_context():
        now = datetime.now()
        tomorrow = now + timedelta(days=1)

        upcoming = mongo.db.follow_ups.find({
            'follow_up_date': {'$gte': now, '$lte': tomorrow},
            'status': 'Pending'
        })

        for fu in upcoming:
            candidate = mongo.db.candidates.find_one({'_id': fu['candidate_id']})
            if candidate:
                existing = mongo.db.notifications.find_one({
                    'candidate_id': fu['candidate_id'],
                    'notification_type': 'follow_up_reminder',
                    'created_at': {'$gte': now - timedelta(hours=23)}
                })

                if not existing:
                    notification = {
                        'candidate_id': fu['candidate_id'],
                        'message': f"Follow-up reminder for {candidate['full_name']} at {fu['follow_up_date'].strftime('%d/%m/%Y %H:%M')}",
                        'notification_type': 'follow_up_reminder',
                        'is_read': False,
                        'created_at': now
                    }
                    mongo.db.notifications.insert_one(notification)


if __name__ == '__main__':
    app.run(debug=True)