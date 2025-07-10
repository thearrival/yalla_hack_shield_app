from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, ActivityLog
from datetime import datetime, timedelta

subscription_bp = Blueprint('subscription', __name__)

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

@subscription_bp.route('/plans', methods=['GET'])
def get_subscription_plans():
    """Get available subscription plans"""
    try:
        plans = {
            'free': {
                'name': 'Free Shield',
                'price': 0,
                'billing': 'monthly',
                'features': [
                    'Basic vulnerability scanning (monthly)',
                    'Email alerts for critical threats',
                    'Community support',
                    'Up to 1 device',
                    'Basic security reports'
                ],
                'limits': {
                    'devices': 1,
                    'scans_per_month': 1,
                    'support_level': 'community'
                }
            },
            'personal': {
                'name': 'Personal Shield',
                'price': 19,
                'billing': 'monthly',
                'features': [
                    'Weekly vulnerability scanning',
                    'Real-time threat detection',
                    'Email & SMS alerts',
                    'Priority support',
                    'Up to 3 devices',
                    'Detailed security reports',
                    'Basic compliance monitoring'
                ],
                'limits': {
                    'devices': 3,
                    'scans_per_month': 4,
                    'support_level': 'priority'
                }
            },
            'pro': {
                'name': 'Pro Shield',
                'price': 79,
                'billing': 'monthly',
                'features': [
                    'Daily vulnerability scanning',
                    'Advanced threat detection with AI',
                    'Multi-channel alerts (Email, SMS, Slack)',
                    '24/7 support',
                    'Up to 25 devices',
                    'Advanced security reports',
                    'Compliance monitoring (SOC 2, ISO 27001)',
                    'Incident response support',
                    'Custom security policies'
                ],
                'limits': {
                    'devices': 25,
                    'scans_per_month': 30,
                    'support_level': '24/7'
                }
            },
            'enterprise': {
                'name': 'Enterprise Shield',
                'price': 199,
                'billing': 'monthly',
                'features': [
                    'Continuous vulnerability scanning',
                    'Enterprise-grade threat detection',
                    'Custom alert channels',
                    'Dedicated account manager',
                    'Unlimited devices',
                    'Executive security reports',
                    'Full compliance suite',
                    'Priority incident response',
                    'Custom integrations',
                    'On-site security consulting',
                    'Advanced analytics dashboard'
                ],
                'limits': {
                    'devices': 'unlimited',
                    'scans_per_month': 'unlimited',
                    'support_level': 'dedicated'
                }
            }
        }
        
        return jsonify({'plans': plans}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get subscription plans: {str(e)}'}), 500

@subscription_bp.route('/current', methods=['GET'])
def get_current_subscription():
    """Get current user's subscription details"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        subscription_info = {
            'tier': user.subscription_tier,
            'status': user.subscription_status,
            'start_date': user.subscription_start_date.isoformat() if user.subscription_start_date else None,
            'end_date': user.subscription_end_date.isoformat() if user.subscription_end_date else None,
            'days_remaining': None
        }
        
        # Calculate days remaining for paid subscriptions
        if user.subscription_end_date and user.subscription_tier != 'free':
            days_remaining = (user.subscription_end_date - datetime.utcnow()).days
            subscription_info['days_remaining'] = max(0, days_remaining)
        
        return jsonify({'subscription': subscription_info}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get current subscription: {str(e)}'}), 500

@subscription_bp.route('/initiate-payment', methods=['POST'])
def initiate_payment():
    """Initiate payment process for subscription upgrade"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data.get('plan'):
            return jsonify({'error': 'Plan is required'}), 400
        
        valid_plans = ['personal', 'pro', 'enterprise']
        if data['plan'] not in valid_plans:
            return jsonify({'error': 'Invalid plan'}), 400
        
        billing_cycle = data.get('billing_cycle', 'monthly')
        if billing_cycle not in ['monthly', 'annual']:
            return jsonify({'error': 'Invalid billing cycle'}), 400
        
        # Calculate pricing
        pricing = {
            'personal': {'monthly': 19, 'annual': 190},  # 2 months free
            'pro': {'monthly': 79, 'annual': 790},       # 2 months free
            'enterprise': {'monthly': 199, 'annual': 1990}  # 2 months free
        }
        
        amount = pricing[data['plan']][billing_cycle]
        
        # Create PayPal payment URL with amount
        paypal_url = f"https://paypal.me/yallahack/{amount}USD"
        
        # Store pending subscription info in session
        session['pending_subscription'] = {
            'plan': data['plan'],
            'billing_cycle': billing_cycle,
            'amount': amount,
            'initiated_at': datetime.utcnow().isoformat()
        }
        
        # Log payment initiation
        log_activity(
            user_id,
            'payment_initiated',
            f'User initiated payment for {data["plan"]} plan ({billing_cycle})',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Payment initiated successfully',
            'paypal_url': paypal_url,
            'amount': amount,
            'plan': data['plan'],
            'billing_cycle': billing_cycle
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to initiate payment: {str(e)}'}), 500

@subscription_bp.route('/confirm-payment', methods=['POST'])
def confirm_payment():
    """Confirm payment and activate subscription"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get pending subscription from session
        pending_subscription = session.get('pending_subscription')
        if not pending_subscription:
            return jsonify({'error': 'No pending subscription found'}), 400
        
        # Validate pending subscription is not too old (30 minutes)
        initiated_at = datetime.fromisoformat(pending_subscription['initiated_at'])
        if datetime.utcnow() - initiated_at > timedelta(minutes=30):
            session.pop('pending_subscription', None)
            return jsonify({'error': 'Payment session expired. Please try again.'}), 400
        
        # Update user subscription
        old_tier = user.subscription_tier
        user.subscription_tier = pending_subscription['plan']
        user.subscription_status = 'active'
        user.subscription_start_date = datetime.utcnow()
        
        # Set end date based on billing cycle
        if pending_subscription['billing_cycle'] == 'monthly':
            user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
        else:  # annual
            user.subscription_end_date = datetime.utcnow() + timedelta(days=365)
        
        db.session.commit()
        
        # Clear pending subscription from session
        session.pop('pending_subscription', None)
        
        # Log successful subscription activation
        log_activity(
            user_id,
            'subscription_activated',
            f'User upgraded from {old_tier} to {user.subscription_tier} plan',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Subscription activated successfully',
            'subscription': {
                'tier': user.subscription_tier,
                'status': user.subscription_status,
                'start_date': user.subscription_start_date.isoformat(),
                'end_date': user.subscription_end_date.isoformat()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to confirm payment: {str(e)}'}), 500

@subscription_bp.route('/cancel', methods=['POST'])
def cancel_subscription():
    """Cancel current subscription"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.subscription_tier == 'free':
            return jsonify({'error': 'No active subscription to cancel'}), 400
        
        # Set subscription to expire at the end of current billing period
        # Don't immediately downgrade to allow user to use paid features until expiration
        user.subscription_status = 'cancelled'
        
        db.session.commit()
        
        # Log subscription cancellation
        log_activity(
            user_id,
            'subscription_cancelled',
            f'User cancelled {user.subscription_tier} subscription',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Subscription cancelled successfully. You will retain access until the end of your billing period.',
            'subscription': {
                'tier': user.subscription_tier,
                'status': user.subscription_status,
                'end_date': user.subscription_end_date.isoformat() if user.subscription_end_date else None
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to cancel subscription: {str(e)}'}), 500

@subscription_bp.route('/upgrade', methods=['POST'])
def upgrade_subscription():
    """Upgrade to a higher tier subscription"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data.get('new_plan'):
            return jsonify({'error': 'New plan is required'}), 400
        
        # Define tier hierarchy
        tier_hierarchy = ['free', 'personal', 'pro', 'enterprise']
        current_tier_index = tier_hierarchy.index(user.subscription_tier)
        new_tier_index = tier_hierarchy.index(data['new_plan'])
        
        if new_tier_index <= current_tier_index:
            return jsonify({'error': 'Can only upgrade to a higher tier'}), 400
        
        # For upgrades, we'll use the same payment flow
        return initiate_payment()
        
    except ValueError:
        return jsonify({'error': 'Invalid plan'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to upgrade subscription: {str(e)}'}), 500

@subscription_bp.route('/usage', methods=['GET'])
def get_usage_stats():
    """Get current usage statistics for the user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get plan limits
        plan_limits = {
            'free': {'devices': 1, 'scans_per_month': 1},
            'personal': {'devices': 3, 'scans_per_month': 4},
            'pro': {'devices': 25, 'scans_per_month': 30},
            'enterprise': {'devices': 'unlimited', 'scans_per_month': 'unlimited'}
        }
        
        current_limits = plan_limits.get(user.subscription_tier, plan_limits['free'])
        
        # Count current usage
        device_count = len(user.devices)
        
        # For demo purposes, we'll simulate scan count
        # In a real implementation, you'd track actual scans
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        scan_count = min(device_count * 5, current_limits.get('scans_per_month', 0)) if current_limits.get('scans_per_month') != 'unlimited' else device_count * 10
        
        usage_stats = {
            'devices': {
                'current': device_count,
                'limit': current_limits['devices']
            },
            'scans_this_month': {
                'current': scan_count,
                'limit': current_limits['scans_per_month']
            },
            'subscription_tier': user.subscription_tier
        }
        
        return jsonify({'usage': usage_stats}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get usage stats: {str(e)}'}), 500

