from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Device, SecurityEvent, ActivityLog
from datetime import datetime, timedelta
import random

device_bp = Blueprint('device', __name__)

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

@device_bp.route('/devices', methods=['GET'])
def get_user_devices():
    """Get all devices for the current user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        devices = Device.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'devices': [device.to_dict() for device in devices],
            'total_devices': len(devices)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get devices: {str(e)}'}), 500

@device_bp.route('/devices', methods=['POST'])
def add_device():
    """Add a new device for the current user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['device_name', 'device_type', 'operating_system']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check device limits based on subscription tier
        current_device_count = Device.query.filter_by(user_id=user_id).count()
        device_limits = {
            'free': 1,
            'personal': 3,
            'pro': 25,
            'enterprise': float('inf')
        }
        
        limit = device_limits.get(user.subscription_tier, 1)
        if current_device_count >= limit:
            return jsonify({
                'error': f'Device limit reached for {user.subscription_tier} plan. Current limit: {limit}'
            }), 400
        
        # Check if device with same name already exists for this user
        existing_device = Device.query.filter_by(
            user_id=user_id,
            device_name=data['device_name']
        ).first()
        
        if existing_device:
            return jsonify({'error': 'Device with this name already exists'}), 400
        
        # Create new device
        device = Device(
            user_id=user_id,
            device_name=data['device_name'],
            device_type=data['device_type'],
            operating_system=data['operating_system'],
            ip_address=data.get('ip_address'),
            mac_address=data.get('mac_address'),
            agent_version=data.get('agent_version', '1.0.0')
        )
        
        db.session.add(device)
        db.session.commit()
        
        # Log device addition
        log_activity(
            user_id,
            'device_added',
            f'Added device: {device.device_name} ({device.device_type})',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Device added successfully',
            'device': device.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to add device: {str(e)}'}), 500

@device_bp.route('/devices/<int:device_id>', methods=['GET'])
def get_device_details(device_id):
    """Get detailed information about a specific device"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        device = Device.query.filter_by(id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Get recent security events for this device
        security_events = SecurityEvent.query.filter_by(device_id=device_id).order_by(
            SecurityEvent.created_at.desc()
        ).limit(10).all()
        
        return jsonify({
            'device': device.to_dict(),
            'security_events': [event.to_dict() for event in security_events]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get device details: {str(e)}'}), 500

@device_bp.route('/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    """Update device information"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        device = Device.query.filter_by(id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        allowed_fields = ['device_name', 'device_type', 'operating_system', 'ip_address', 'mac_address']
        for field in allowed_fields:
            if field in data:
                setattr(device, field, data[field])
        
        # Check for duplicate device name
        if 'device_name' in data:
            existing_device = Device.query.filter(
                Device.user_id == user_id,
                Device.device_name == data['device_name'],
                Device.id != device_id
            ).first()
            
            if existing_device:
                return jsonify({'error': 'Device with this name already exists'}), 400
        
        device.last_seen = datetime.utcnow()
        db.session.commit()
        
        # Log device update
        log_activity(
            user_id,
            'device_updated',
            f'Updated device: {device.device_name}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Device updated successfully',
            'device': device.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update device: {str(e)}'}), 500

@device_bp.route('/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Delete a device"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        device = Device.query.filter_by(id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        device_name = device.device_name
        
        # Delete the device (cascade will handle related security events)
        db.session.delete(device)
        db.session.commit()
        
        # Log device deletion
        log_activity(
            user_id,
            'device_deleted',
            f'Deleted device: {device_name}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({'message': 'Device deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete device: {str(e)}'}), 500

@device_bp.route('/devices/<int:device_id>/scan', methods=['POST'])
def initiate_device_scan():
    """Initiate a security scan for a specific device"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        device = Device.query.filter_by(id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Check scan limits based on subscription tier
        scan_limits = {
            'free': 1,
            'personal': 4,
            'pro': 30,
            'enterprise': float('inf')
        }
        
        # For demo purposes, we'll simulate scan results
        # In a real implementation, this would trigger actual security scanning
        
        scan_results = {
            'scan_id': f"scan_{device_id}_{int(datetime.utcnow().timestamp())}",
            'device_id': device_id,
            'device_name': device.device_name,
            'scan_type': 'vulnerability_scan',
            'status': 'completed',
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
            'findings': {
                'critical': random.randint(0, 2),
                'high': random.randint(0, 5),
                'medium': random.randint(2, 10),
                'low': random.randint(5, 15),
                'info': random.randint(10, 25)
            },
            'summary': 'Vulnerability scan completed successfully'
        }
        
        # Create a security event if critical or high vulnerabilities found
        if scan_results['findings']['critical'] > 0 or scan_results['findings']['high'] > 0:
            severity = 'critical' if scan_results['findings']['critical'] > 0 else 'high'
            
            event = SecurityEvent(
                user_id=user_id,
                device_id=device_id,
                event_type='vulnerability_detected',
                severity=severity,
                title=f'Vulnerabilities detected on {device.device_name}',
                description=f'Scan found {scan_results["findings"]["critical"]} critical and {scan_results["findings"]["high"]} high severity vulnerabilities',
                rule_triggered='vulnerability_scan_alert'
            )
            
            db.session.add(event)
            db.session.commit()
        
        # Update device last seen
        device.last_seen = datetime.utcnow()
        db.session.commit()
        
        # Log scan initiation
        log_activity(
            user_id,
            'device_scan_initiated',
            f'Initiated security scan for device: {device.device_name}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Security scan completed',
            'scan_results': scan_results
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to initiate device scan: {str(e)}'}), 500

@device_bp.route('/devices/<int:device_id>/status', methods=['PUT'])
def update_device_status(device_id):
    """Update device status (online/offline/compromised)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        device = Device.query.filter_by(id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        data = request.get_json()
        
        if not data.get('status'):
            return jsonify({'error': 'Status is required'}), 400
        
        valid_statuses = ['online', 'offline', 'compromised']
        if data['status'] not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400
        
        old_status = device.status
        device.status = data['status']
        device.last_seen = datetime.utcnow()
        
        # If device is marked as compromised, create a security event
        if data['status'] == 'compromised' and old_status != 'compromised':
            event = SecurityEvent(
                user_id=user_id,
                device_id=device_id,
                event_type='device_compromised',
                severity='critical',
                title=f'Device {device.device_name} marked as compromised',
                description=f'Device {device.device_name} has been marked as compromised and requires immediate attention',
                rule_triggered='device_compromise_alert'
            )
            
            db.session.add(event)
        
        db.session.commit()
        
        # Log status update
        log_activity(
            user_id,
            'device_status_updated',
            f'Updated device {device.device_name} status from {old_status} to {data["status"]}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Device status updated successfully',
            'device': device.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update device status: {str(e)}'}), 500

@device_bp.route('/devices/summary', methods=['GET'])
def get_devices_summary():
    """Get summary statistics for user's devices"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        devices = Device.query.filter_by(user_id=user_id).all()
        
        summary = {
            'total_devices': len(devices),
            'online_devices': len([d for d in devices if d.status == 'online']),
            'offline_devices': len([d for d in devices if d.status == 'offline']),
            'compromised_devices': len([d for d in devices if d.status == 'compromised']),
            'device_types': {},
            'operating_systems': {}
        }
        
        # Count by device type and OS
        for device in devices:
            # Device types
            if device.device_type in summary['device_types']:
                summary['device_types'][device.device_type] += 1
            else:
                summary['device_types'][device.device_type] = 1
            
            # Operating systems
            if device.operating_system in summary['operating_systems']:
                summary['operating_systems'][device.operating_system] += 1
            else:
                summary['operating_systems'][device.operating_system] = 1
        
        return jsonify({'summary': summary}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get devices summary: {str(e)}'}), 500

