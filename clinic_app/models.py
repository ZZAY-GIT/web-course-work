from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'patient', 'doctor', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи (backref)
    patient = db.relationship('Patient', backref='user', uselist=False, cascade="all, delete-orphan")
    doctor = db.relationship('Doctor', backref='user', uselist=False, cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    
    # Связи
    appointments = db.relationship('Appointment', backref='patient', lazy=True, cascade="all, delete-orphan")
    medical_record = db.relationship('MedicalRecord', backref='patient', uselist=False, cascade="all, delete-orphan")
    documents = db.relationship('Document', backref='patient', lazy=True, cascade="all, delete-orphan")

class Doctor(db.Model):
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    cabinet = db.Column(db.String(20), nullable=False)
    
    # Связи
    slots = db.relationship('ScheduleSlot', backref='doctor', lazy=True, cascade="all, delete-orphan")
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False, default=30)
    
    # Связи
    appointments = db.relationship('Appointment', backref='service', lazy=True)

class ScheduleSlot(db.Model):
    __tablename__ = 'schedule_slots'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='free')  # 'free', 'booked'
    
    # Связи
    appointment = db.relationship('Appointment', backref='slot', uselist=False)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('schedule_slots.id'), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='created')  # 'created', 'confirmed', 'cancelled', 'completed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    visit = db.relationship('Visit', backref='appointment', uselist=False, cascade="all, delete-orphan")

class MedicalRecord(db.Model):
    __tablename__ = 'medical_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), unique=True, nullable=False)
    card_number = db.Column(db.String(50), unique=True, nullable=False)
    blood_type = db.Column(db.String(10))
    rh_factor = db.Column(db.String(5))
    allergies = db.Column(db.Text)
    chronic_diseases = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    visits = db.relationship('Visit', backref='record', lazy=True, cascade="all, delete-orphan")

class Visit(db.Model):
    __tablename__ = 'visits'
    
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id', ondelete='CASCADE'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id', ondelete='CASCADE'), unique=True, nullable=False)
    complaints = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    documents = db.relationship('Document', backref='visit', lazy=True)

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id', ondelete='SET NULL'), nullable=True)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
