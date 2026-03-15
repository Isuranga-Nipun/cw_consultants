# models.py

from datetime import datetime


class Candidate:
    """Candidate model for MongoDB documents"""

    def __init__(self, data=None):
        """Initialize Candidate from MongoDB document"""
        if data:
            self.id = data.get('_id')
            self.full_name = data.get('full_name', '')
            self.surname = data.get('surname', '')
            self.other_names = data.get('other_names', '')
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
            self.pending_payment = data.get('pending_payment', 0)

            # Required documents
            self.documents = data.get('documents', {
                'police_report': 'Pending',
                'police_report_file': None,
                'gs_report': 'Pending',
                'gs_report_file': None,
                'birth_certificate': 'Pending',
                'birth_certificate_file': None,
                'other': ''
            })

            # Pending items
            self.pending_documents = data.get('pending_documents', [])

            # Follow-up
            self.follow_ups = data.get('follow_ups', [])
            self.created_at = data.get('created_at', datetime.now())
            self.updated_at = data.get('updated_at', datetime.now())
        else:
            # Initialize empty candidate
            self.id = None
            self.full_name = ''
            self.surname = ''
            self.other_names = ''
            self.address_line1 = ''
            self.address_line2 = ''
            self.birthday = ''
            self.gender = ''
            self.age = 0
            self.current_job = ''
            self.email = ''
            self.mobile_no = ''
            self.nic_no = ''
            self.nic_format = ''
            self.passport_status = 'Pending'
            self.passport_no = ''
            self.job_title = ''
            self.visa_refusals = False
            self.visa_refusal_details = ''
            self.photos = []
            self.videos = []
            self.passport_photo = ''
            self.nic_photo = ''
            self.total_payment = 0
            self.payments = []
            self.remaining_payment = 0
            self.pending_payment = 0
            self.documents = {
                'police_report': 'Pending',
                'police_report_file': None,
                'gs_report': 'Pending',
                'gs_report_file': None,
                'birth_certificate': 'Pending',
                'birth_certificate_file': None,
                'other': ''
            }
            self.pending_documents = []
            self.follow_ups = []
            self.created_at = datetime.now()
            self.updated_at = datetime.now()

    def to_dict(self):
        """Convert Candidate object to dictionary for MongoDB"""
        return {
            'full_name': self.full_name,
            'surname': self.surname,
            'other_names': self.other_names,
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
            'pending_payment': self.pending_payment,
            'documents': self.documents,
            'pending_documents': self.pending_documents,
            'follow_ups': self.follow_ups,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class FollowUp:
    """Follow-up model for MongoDB"""

    def __init__(self, data=None):
        if data:
            self.id = data.get('_id')
            self.candidate_id = data.get('candidate_id')
            self.follow_up_date = data.get('follow_up_date')
            self.follow_up_type = data.get('follow_up_type')
            self.notes = data.get('notes')
            self.status = data.get('status', 'Pending')
            self.created_at = data.get('created_at', datetime.now())
        else:
            self.id = None
            self.candidate_id = None
            self.follow_up_date = None
            self.follow_up_type = ''
            self.notes = ''
            self.status = 'Pending'
            self.created_at = datetime.now()

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
    """Notification model for MongoDB"""

    def __init__(self, data=None):
        if data:
            self.id = data.get('_id')
            self.candidate_id = data.get('candidate_id')
            self.message = data.get('message')
            self.notification_type = data.get('notification_type')
            self.is_read = data.get('is_read', False)
            self.created_at = data.get('created_at', datetime.now())
        else:
            self.id = None
            self.candidate_id = None
            self.message = ''
            self.notification_type = ''
            self.is_read = False
            self.created_at = datetime.now()

    def to_dict(self):
        return {
            'candidate_id': self.candidate_id,
            'message': self.message,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'created_at': self.created_at
        }