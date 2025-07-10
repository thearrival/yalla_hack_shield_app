from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    company_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(50), nullable=True)
    subscription_tier = db.Column(db.String(20), default='free')  # free, personal, pro, enterprise
    subscription_status = db.Column(db.String(20), default='active')  # active, inactive, pending
    subscription_start_date = db.Column(db.DateTime, nullable=True)
    subscription_end_date = db.Column(db.DateTime, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    devices = db.relationship('Device', backref='user', lazy=True, cascade='all, delete-orphan')
    security_events = db.relationship('SecurityEvent', backref='user', lazy=True, cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'company_name': self.company_name,
            'phone': self.phone,
            'country': self.country,
            'subscription_tier': self.subscription_tier,
            'subscription_status': self.subscription_status,
            'subscription_start_date': self.subscription_start_date.isoformat() if self.subscription_start_date else None,
            'subscription_end_date': self.subscription_end_date.isoformat() if self.subscription_end_date else None,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    device_name = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(50), nullable=False)  # desktop, laptop, mobile, server
    operating_system = db.Column(db.String(50), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    mac_address = db.Column(db.String(17), nullable=True)
    agent_version = db.Column(db.String(20), nullable=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='online')  # online, offline, compromised
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'operating_system': self.operating_system,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
            'agent_version': self.agent_version,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SecurityEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=True)
    event_type = db.Column(db.String(50), nullable=False)  # malware, rootkit, suspicious_activity, etc.
    severity = db.Column(db.String(20), nullable=False)  # low, medium, high, critical
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    rule_triggered = db.Column(db.String(100), nullable=True)
    source_ip = db.Column(db.String(45), nullable=True)
    destination_ip = db.Column(db.String(45), nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    process_name = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='open')  # open, investigating, resolved, false_positive
    email_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    # Relationship
    device = db.relationship('Device', backref='security_events')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_id': self.device_id,
            'event_type': self.event_type,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'rule_triggered': self.rule_triggered,
            'source_ip': self.source_ip,
            'destination_ip': self.destination_ip,
            'file_path': self.file_path,
            'process_name': self.process_name,
            'status': self.status,
            'email_sent': self.email_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'device_name': self.device.device_name if self.device else None
        }

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'description': self.description,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'username': self.user.username if self.user else 'System'
        }

class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

