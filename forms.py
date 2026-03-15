from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SelectField, BooleanField, DateField, \
    FileField, FieldList, FormField
from wtforms.validators import DataRequired, Email, Optional, Length, ValidationError
from flask_wtf.file import FileAllowed
from config import Config
import re


class PaymentForm(FlaskForm):
    payment_type = StringField('Payment Type', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    description = StringField('Description', validators=[Optional()])


class DocumentForm(FlaskForm):
    document_type = StringField('Document Type', validators=[DataRequired()])
    status = SelectField('Status', choices=[('Having', 'Having'), ('Pending', 'Pending')], validators=[DataRequired()])


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
            if not re.match(r'^[P|N]\d{7}$', field.data):
                raise ValidationError('Passport number must be in format P1234567 or N1234567')

    # Custom validation for birthday format
    def validate_birthday(self, field):
        if field.data:
            if not re.match(r'^\d{2}/\d{2}/\d{4}$', field.data):
                raise ValidationError('Birthday must be in DD/MM/YYYY format')

    # Custom validation for NIC
    def validate_nic_no(self, field):
        if field.data:
            # Old format: 9 digits + V
            if not re.match(r'^\d{9}[V|v]$', field.data) and not re.match(r'^\d{12}$', field.data):
                raise ValidationError('NIC must be in format 940730406V or 199407300406')