import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db, User, SystemSettings
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.admin import admin_bp
from src.routes.subscription import subscription_bp
from src.routes.device import device_bp
from src.routes.email_service import email_bp
from src.routes.paypal_service import paypal_bp
from datetime import datetime

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'YallaHack2025!SecureKey#$%'

# Enable CORS for all routes
CORS(app, supports_credentials=True)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(subscription_bp, url_prefix='/api/subscription')
app.register_blueprint(device_bp, url_prefix='/api')
app.register_blueprint(email_bp, url_prefix='/api/email')
app.register_blueprint(paypal_bp, url_prefix='/api/paypal')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def create_default_admin():
    """Create default admin user if it doesn't exist"""
    try:
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@yalla-hack.net',
                first_name='Admin',
                last_name='User',
                company_name='Yalla-Hack',
                is_admin=True,
                subscription_tier='enterprise',
                subscription_status='active',
                subscription_start_date=datetime.utcnow()
            )
            admin_user.set_password('YallaHack2025!')
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created: admin / YallaHack2025!")
    except Exception as e:
        print(f"Error creating default admin: {e}")

def create_default_settings():
    """Create default system settings"""
    try:
        default_settings = [
            {
                'key': 'company_name',
                'value': 'Yalla-Hack Shield',
                'description': 'Company name displayed in the application'
            },
            {
                'key': 'support_email',
                'value': 'support@yalla-hack.net',
                'description': 'Support email address'
            },
            {
                'key': 'paypal_link',
                'value': 'https://paypal.me/yallahack',
                'description': 'PayPal payment link'
            },
            {
                'key': 'email_notifications_enabled',
                'value': 'true',
                'description': 'Enable email notifications for security events'
            }
        ]
        
        for setting_data in default_settings:
            existing_setting = SystemSettings.query.filter_by(key=setting_data['key']).first()
            if not existing_setting:
                setting = SystemSettings(
                    key=setting_data['key'],
                    value=setting_data['value'],
                    description=setting_data['description']
                )
                db.session.add(setting)
        
        db.session.commit()
    except Exception as e:
        print(f"Error creating default settings: {e}")

with app.app_context():
    db.create_all()
    create_default_admin()
    create_default_settings()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

