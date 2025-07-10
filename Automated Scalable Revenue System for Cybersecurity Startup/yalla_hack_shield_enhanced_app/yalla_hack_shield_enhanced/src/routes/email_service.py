from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Device, SecurityEvent, ActivityLog, SystemSettings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import threading

email_bp = Blueprint('email', __name__)

def log_activity(user_id, action, description, ip_address=None, user_agent=None):
    """Helper function to log user activities"""
    try:
        activity = ActivityLog(
            user_id=user_id,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")

def get_email_template(event_type, user, device, event):
    """Generate email template based on event type"""
    
    # Base template for security alerts
    if event_type == "security_alert":
        subject = f"Yalla-Hack Alert: {event.title}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
                .header {{ background: linear-gradient(135deg, #0A2342 0%, #1B4F72 50%, #2CA58D 100%); color: white; padding: 30px; text-align: center; }}
                .logo {{ width: 60px; height: 60px; border-radius: 50%; margin-bottom: 15px; }}
                .content {{ padding: 30px; }}
                .alert-box {{ background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 20px 0; }}
                .alert-critical {{ background-color: #f8d7da; border-color: #f5c6cb; }}
                .alert-high {{ background-color: #fff3cd; border-color: #ffeaa7; }}
                .alert-medium {{ background-color: #d1ecf1; border-color: #bee5eb; }}
                .alert-low {{ background-color: #d4edda; border-color: #c3e6cb; }}
                .details-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .details-table th, .details-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                .details-table th {{ background-color: #f8f9fa; font-weight: 600; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; font-size: 14px; }}
                .btn {{ display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #2CA58D, #1B4F72); color: white; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
                .severity-badge {{ padding: 4px 12px; border-radius: 15px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
                .severity-critical {{ background-color: #dc3545; color: white; }}
                .severity-high {{ background-color: #fd7e14; color: white; }}
                .severity-medium {{ background-color: #ffc107; color: black; }}
                .severity-low {{ background-color: #28a745; color: white; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ Yalla-Hack Shield</h1>
                    <h2>Security Alert Notification</h2>
                </div>
                
                <div class="content">
                    <p>Dear {user.first_name} {user.last_name},</p>
                    
                    <p>This is an automatic message from your Yalla-Hack Shield Instance.</p>
                    
                    <div class="alert-box alert-{event.severity}">
                        <h3>🚨 Security Event Detected</h3>
                        <p><strong>Event:</strong> {event.title}</p>
                        <p><strong>Severity:</strong> <span class="severity-badge severity-{event.severity}">{event.severity.upper()}</span></p>
                        <p><strong>Device:</strong> {device.device_name if device else 'Unknown Device'}</p>
                        <p><strong>Time:</strong> {event.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    </div>
                    
                    <h3>Event Details</h3>
                    <table class="details-table">
                        <tr>
                            <th>Rule Triggered</th>
                            <td>{event.rule_triggered or 'N/A'}</td>
                        </tr>
                        <tr>
                            <th>Event Type</th>
                            <td>{event.event_type}</td>
                        </tr>
                        <tr>
                            <th>Source IP</th>
                            <td>{event.source_ip or 'N/A'}</td>
                        </tr>
                        <tr>
                            <th>Destination IP</th>
                            <td>{event.destination_ip or 'N/A'}</td>
                        </tr>
                        <tr>
                            <th>File Path</th>
                            <td>{event.file_path or 'N/A'}</td>
                        </tr>
                        <tr>
                            <th>Process Name</th>
                            <td>{event.process_name or 'N/A'}</td>
                        </tr>
                    </table>
                    
                    <h3>Description</h3>
                    <p>{event.description}</p>
                    
                    <h3>Recommended Actions</h3>
                    <ul>
                        <li>Review the affected device immediately</li>
                        <li>Check for any suspicious activities</li>
                        <li>Update your security policies if necessary</li>
                        <li>Contact our support team if you need assistance</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://yalla-hack.net/dashboard" class="btn">View Dashboard</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>Yalla-Hack Shield</strong> - Advanced Cybersecurity Platform</p>
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>For support, contact us at support@yalla-hack.net</p>
                    <p>&copy; 2025 Yalla-Hack. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_body = f"""
        YALLA-HACK SHIELD - SECURITY ALERT
        
        Dear {user.first_name} {user.last_name},
        
        This is an automatic message from your Yalla-Hack Shield Instance.
        
        SECURITY EVENT DETECTED:
        - Event: {event.title}
        - Severity: {event.severity.upper()}
        - Device: {device.device_name if device else 'Unknown Device'}
        - Time: {event.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
        
        EVENT DETAILS:
        - Rule Triggered: {event.rule_triggered or 'N/A'}
        - Event Type: {event.event_type}
        - Source IP: {event.source_ip or 'N/A'}
        - Destination IP: {event.destination_ip or 'N/A'}
        - File Path: {event.file_path or 'N/A'}
        - Process Name: {event.process_name or 'N/A'}
        
        DESCRIPTION:
        {event.description}
        
        RECOMMENDED ACTIONS:
        - Review the affected device immediately
        - Check for any suspicious activities
        - Update your security policies if necessary
        - Contact our support team if you need assistance
        
        View your dashboard: https://yalla-hack.net/dashboard
        
        ---
        Yalla-Hack Shield - Advanced Cybersecurity Platform
        This is an automated message. Please do not reply to this email.
        For support, contact us at support@yalla-hack.net
        """
        
        return subject, html_body, text_body
    
    # Welcome email template
    elif event_type == "welcome":
        subject = "Welcome to Yalla-Hack Shield - Your Cybersecurity Journey Begins!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
                .header {{ background: linear-gradient(135deg, #0A2342 0%, #1B4F72 50%, #2CA58D 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .feature-box {{ background-color: #f8f9fa; border-radius: 8px; padding: 20px; margin: 15px 0; }}
                .btn {{ display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #2CA58D, #1B4F72); color: white; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ Welcome to Yalla-Hack Shield!</h1>
                    <p>Your Advanced Cybersecurity Platform</p>
                </div>
                
                <div class="content">
                    <p>Dear {user.first_name} {user.last_name},</p>
                    
                    <p>Welcome to Yalla-Hack Shield! We're excited to have you on board and help protect your digital assets.</p>
                    
                    <h3>What's Next?</h3>
                    
                    <div class="feature-box">
                        <h4>🖥️ Add Your Devices</h4>
                        <p>Start by adding your devices to begin monitoring their security status.</p>
                    </div>
                    
                    <div class="feature-box">
                        <h4>🔍 Run Security Scans</h4>
                        <p>Perform comprehensive security scans to identify vulnerabilities.</p>
                    </div>
                    
                    <div class="feature-box">
                        <h4>📊 Monitor Dashboard</h4>
                        <p>Keep track of your security posture through our intuitive dashboard.</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://yalla-hack.net/dashboard" class="btn">Access Your Dashboard</a>
                    </div>
                    
                    <p>If you have any questions or need assistance, our support team is here to help!</p>
                </div>
                
                <div class="footer">
                    <p><strong>Yalla-Hack Shield</strong> - Advanced Cybersecurity Platform</p>
                    <p>For support, contact us at support@yalla-hack.net</p>
                    <p>&copy; 2025 Yalla-Hack. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        WELCOME TO YALLA-HACK SHIELD!
        
        Dear {user.first_name} {user.last_name},
        
        Welcome to Yalla-Hack Shield! We're excited to have you on board and help protect your digital assets.
        
        WHAT'S NEXT?
        
        1. Add Your Devices
           Start by adding your devices to begin monitoring their security status.
        
        2. Run Security Scans
           Perform comprehensive security scans to identify vulnerabilities.
        
        3. Monitor Dashboard
           Keep track of your security posture through our intuitive dashboard.
        
        Access your dashboard: https://yalla-hack.net/dashboard
        
        If you have any questions or need assistance, our support team is here to help!
        
        ---
        Yalla-Hack Shield - Advanced Cybersecurity Platform
        For support, contact us at support@yalla-hack.net
        """
        
        return subject, html_body, text_body
    
    return None, None, None

def send_email_async(to_email, subject, html_body, text_body):
    """Send email asynchronously"""
    def send_email():
        try:
            # For demo purposes, we'll simulate email sending
            # In a real implementation, you would configure SMTP settings
            print(f"📧 EMAIL SENT TO: {to_email}")
            print(f"📧 SUBJECT: {subject}")
            print(f"📧 CONTENT: {text_body[:200]}...")
            
            # Here you would implement actual email sending logic:
            # smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
            # smtp_server.starttls()
            # smtp_server.login(smtp_username, smtp_password)
            # smtp_server.send_message(msg)
            # smtp_server.quit()
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    # Run email sending in a separate thread
    thread = threading.Thread(target=send_email)
    thread.daemon = True
    thread.start()

def send_security_alert_email(user_id, device_id, event_id):
    """Send security alert email to user"""
    try:
        user = User.query.get(user_id)
        device = Device.query.get(device_id) if device_id else None
        event = SecurityEvent.query.get(event_id)
        
        if not user or not event:
            return False
        
        # Check if email notifications are enabled
        email_setting = SystemSettings.query.filter_by(key='email_notifications_enabled').first()
        if email_setting and email_setting.value.lower() != 'true':
            return False
        
        # Generate email content
        subject, html_body, text_body = get_email_template('security_alert', user, device, event)
        
        if not subject:
            return False
        
        # Send email asynchronously
        send_email_async(user.email, subject, html_body, text_body)
        
        # Mark event as email sent
        event.email_sent = True
        db.session.commit()
        
        # Log email activity
        log_activity(
            user_id,
            'security_alert_email_sent',
            f'Security alert email sent for event: {event.title}',
            None,
            None
        )
        
        return True
        
    except Exception as e:
        print(f"Error sending security alert email: {e}")
        return False

def send_welcome_email(user_id):
    """Send welcome email to new user"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return False
        
        # Generate email content
        subject, html_body, text_body = get_email_template('welcome', user, None, None)
        
        if not subject:
            return False
        
        # Send email asynchronously
        send_email_async(user.email, subject, html_body, text_body)
        
        # Log email activity
        log_activity(
            user_id,
            'welcome_email_sent',
            f'Welcome email sent to user: {user.username}',
            None,
            None
        )
        
        return True
        
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False

@email_bp.route('/test-email', methods=['POST'])
def test_email():
    """Test email functionality (admin only)"""
    try:
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        
        if not user_id or not is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        email_type = data.get('type', 'welcome')
        target_user_id = data.get('user_id', user_id)
        
        if email_type == 'welcome':
            success = send_welcome_email(target_user_id)
        elif email_type == 'security_alert':
            # Create a test security event
            user = User.query.get(target_user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Get user's first device or create a dummy one
            device = Device.query.filter_by(user_id=target_user_id).first()
            
            test_event = SecurityEvent(
                user_id=target_user_id,
                device_id=device.id if device else None,
                event_type='test_alert',
                severity='medium',
                title='Test Security Alert',
                description='This is a test security alert to verify email functionality.',
                rule_triggered='test_rule'
            )
            
            db.session.add(test_event)
            db.session.commit()
            
            success = send_security_alert_email(target_user_id, device.id if device else None, test_event.id)
        else:
            return jsonify({'error': 'Invalid email type'}), 400
        
        if success:
            return jsonify({'message': f'Test {email_type} email sent successfully'}), 200
        else:
            return jsonify({'error': 'Failed to send test email'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to send test email: {str(e)}'}), 500

@email_bp.route('/email-settings', methods=['GET'])
def get_email_settings():
    """Get email notification settings"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get email settings
        email_enabled = SystemSettings.query.filter_by(key='email_notifications_enabled').first()
        support_email = SystemSettings.query.filter_by(key='support_email').first()
        
        settings = {
            'email_notifications_enabled': email_enabled.value.lower() == 'true' if email_enabled else True,
            'support_email': support_email.value if support_email else 'support@yalla-hack.net'
        }
        
        return jsonify({'settings': settings}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get email settings: {str(e)}'}), 500

@email_bp.route('/email-settings', methods=['PUT'])
def update_email_settings():
    """Update email notification settings (admin only)"""
    try:
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        
        if not user_id or not is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        
        # Update email notifications enabled setting
        if 'email_notifications_enabled' in data:
            setting = SystemSettings.query.filter_by(key='email_notifications_enabled').first()
            if setting:
                setting.value = 'true' if data['email_notifications_enabled'] else 'false'
                setting.updated_at = datetime.utcnow()
            else:
                setting = SystemSettings(
                    key='email_notifications_enabled',
                    value='true' if data['email_notifications_enabled'] else 'false',
                    description='Enable email notifications for security events'
                )
                db.session.add(setting)
        
        # Update support email setting
        if 'support_email' in data:
            setting = SystemSettings.query.filter_by(key='support_email').first()
            if setting:
                setting.value = data['support_email']
                setting.updated_at = datetime.utcnow()
            else:
                setting = SystemSettings(
                    key='support_email',
                    value=data['support_email'],
                    description='Support email address'
                )
                db.session.add(setting)
        
        db.session.commit()
        
        # Log admin action
        log_activity(
            user_id,
            'email_settings_updated',
            'Admin updated email notification settings',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({'message': 'Email settings updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update email settings: {str(e)}'}), 500

