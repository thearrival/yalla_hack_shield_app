from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Device, SecurityEvent, ActivityLog, SystemSettings
from datetime import datetime, timedelta
from sqlalchemy import func, desc

admin_bp = Blueprint('admin', __name__)

def require_admin():
    """Decorator to require admin authentication"""
    user_id = session.get('user_id')
    is_admin = session.get('is_admin')
    
    if not user_id or not is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get(user_id)
    if not user or not user.is_admin or not user.is_active:
        return jsonify({'error': 'Admin access required'}), 403
    
    return None

@admin_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        # Get basic statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_devices = Device.query.count()
        online_devices = Device.query.filter_by(status='online').count()
        
        # Get subscription statistics
        subscription_stats = db.session.query(
            User.subscription_tier,
            func.count(User.id).label('count')
        ).group_by(User.subscription_tier).all()
        
        subscription_data = {tier: count for tier, count in subscription_stats}
        
        # Calculate monthly revenue (simplified calculation)
        pricing = {'free': 0, 'personal': 19, 'pro': 79, 'enterprise': 199}
        monthly_revenue = sum(subscription_data.get(tier, 0) * price for tier, price in pricing.items())
        
        # Get recent security events
        recent_events = SecurityEvent.query.filter(
            SecurityEvent.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        # Get critical events
        critical_events = SecurityEvent.query.filter_by(
            severity='critical',
            status='open'
        ).count()
        
        # Get new users this month
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_users_this_month = User.query.filter(
            User.created_at >= start_of_month
        ).count()
        
        return jsonify({
            'total_users': total_users,
            'active_users': active_users,
            'total_devices': total_devices,
            'online_devices': online_devices,
            'subscription_stats': subscription_data,
            'monthly_revenue': monthly_revenue,
            'recent_events': recent_events,
            'critical_events': critical_events,
            'new_users_this_month': new_users_this_month
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get dashboard stats: {str(e)}'}), 500

@admin_bp.route('/users', methods=['GET'])
def get_users():
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        
        query = User.query
        
        if search:
            query = query.filter(
                (User.username.contains(search)) |
                (User.email.contains(search)) |
                (User.company_name.contains(search))
            )
        
        users = query.order_by(desc(User.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get users: {str(e)}'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_details(user_id):
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's devices
        devices = Device.query.filter_by(user_id=user_id).all()
        
        # Get user's recent security events
        security_events = SecurityEvent.query.filter_by(user_id=user_id).order_by(
            desc(SecurityEvent.created_at)
        ).limit(10).all()
        
        # Get user's recent activity logs
        activity_logs = ActivityLog.query.filter_by(user_id=user_id).order_by(
            desc(ActivityLog.created_at)
        ).limit(10).all()
        
        return jsonify({
            'user': user.to_dict(),
            'devices': [device.to_dict() for device in devices],
            'security_events': [event.to_dict() for event in security_events],
            'activity_logs': [log.to_dict() for log in activity_logs]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get user details: {str(e)}'}), 500

@admin_bp.route('/users/<int:user_id>/subscription', methods=['PUT'])
def update_user_subscription(user_id):
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if 'subscription_tier' in data:
            valid_tiers = ['free', 'personal', 'pro', 'enterprise']
            if data['subscription_tier'] not in valid_tiers:
                return jsonify({'error': 'Invalid subscription tier'}), 400
            
            old_tier = user.subscription_tier
            user.subscription_tier = data['subscription_tier']
            
            # Update subscription dates if upgrading from free
            if old_tier == 'free' and data['subscription_tier'] != 'free':
                user.subscription_start_date = datetime.utcnow()
                user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
        
        if 'subscription_status' in data:
            valid_statuses = ['active', 'inactive', 'pending']
            if data['subscription_status'] not in valid_statuses:
                return jsonify({'error': 'Invalid subscription status'}), 400
            
            user.subscription_status = data['subscription_status']
        
        db.session.commit()
        
        # Log admin action
        admin_user_id = session.get('user_id')
        activity = ActivityLog(
            user_id=admin_user_id,
            action='admin_subscription_update',
            description=f'Admin updated subscription for user {user.username}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update subscription: {str(e)}'}), 500

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Don't allow deactivating admin users
        if user.is_admin:
            return jsonify({'error': 'Cannot deactivate admin users'}), 400
        
        user.is_active = not user.is_active
        db.session.commit()
        
        # Log admin action
        admin_user_id = session.get('user_id')
        action = 'user_activated' if user.is_active else 'user_deactivated'
        activity = ActivityLog(
            user_id=admin_user_id,
            action=f'admin_{action}',
            description=f'Admin {action.replace("_", " ")} user {user.username}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'message': f'User {"activated" if user.is_active else "deactivated"} successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to toggle user status: {str(e)}'}), 500

@admin_bp.route('/security-events', methods=['GET'])
def get_security_events():
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        severity = request.args.get('severity', '')
        status = request.args.get('status', '')
        
        query = SecurityEvent.query
        
        if severity:
            query = query.filter_by(severity=severity)
        
        if status:
            query = query.filter_by(status=status)
        
        events = query.order_by(desc(SecurityEvent.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'events': [event.to_dict() for event in events.items],
            'total': events.total,
            'pages': events.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get security events: {str(e)}'}), 500

@admin_bp.route('/security-events', methods=['POST'])
def create_security_event():
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        data = request.get_json()
        
        required_fields = ['user_id', 'event_type', 'severity', 'title', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate user exists
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Validate device if provided
        device = None
        if data.get('device_id'):
            device = Device.query.get(data['device_id'])
            if not device or device.user_id != data['user_id']:
                return jsonify({'error': 'Invalid device'}), 400
        
        event = SecurityEvent(
            user_id=data['user_id'],
            device_id=data.get('device_id'),
            event_type=data['event_type'],
            severity=data['severity'],
            title=data['title'],
            description=data['description'],
            rule_triggered=data.get('rule_triggered'),
            source_ip=data.get('source_ip'),
            destination_ip=data.get('destination_ip'),
            file_path=data.get('file_path'),
            process_name=data.get('process_name')
        )
        
        db.session.add(event)
        db.session.commit()
        
        # Log admin action
        admin_user_id = session.get('user_id')
        activity = ActivityLog(
            user_id=admin_user_id,
            action='admin_security_event_created',
            description=f'Admin created security event: {event.title}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'message': 'Security event created successfully',
            'event': event.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create security event: {str(e)}'}), 500

@admin_bp.route('/activity-logs', methods=['GET'])
def get_activity_logs():
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        user_id = request.args.get('user_id', type=int)
        action = request.args.get('action', '')
        
        query = ActivityLog.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if action:
            query = query.filter(ActivityLog.action.contains(action))
        
        logs = query.order_by(desc(ActivityLog.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'logs': [log.to_dict() for log in logs.items],
            'total': logs.total,
            'pages': logs.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get activity logs: {str(e)}'}), 500

@admin_bp.route('/system-settings', methods=['GET'])
def get_system_settings():
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        settings = SystemSettings.query.all()
        return jsonify({
            'settings': [setting.to_dict() for setting in settings]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get system settings: {str(e)}'}), 500

@admin_bp.route('/system-settings/<key>', methods=['PUT'])
def update_system_setting(key):
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        data = request.get_json()
        
        if not data.get('value'):
            return jsonify({'error': 'Value is required'}), 400
        
        setting = SystemSettings.query.filter_by(key=key).first()
        
        if setting:
            setting.value = data['value']
            if 'description' in data:
                setting.description = data['description']
            setting.updated_at = datetime.utcnow()
        else:
            setting = SystemSettings(
                key=key,
                value=data['value'],
                description=data.get('description', '')
            )
            db.session.add(setting)
        
        db.session.commit()
        
        # Log admin action
        admin_user_id = session.get('user_id')
        activity = ActivityLog(
            user_id=admin_user_id,
            action='admin_system_setting_updated',
            description=f'Admin updated system setting: {key}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'message': 'System setting updated successfully',
            'setting': setting.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update system setting: {str(e)}'}), 500

