from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, SystemSettings, ActivityLog
from datetime import datetime, timedelta
import json
import uuid

paypal_bp = Blueprint('paypal', __name__)

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

def get_subscription_plans():
    """Get available subscription plans with pricing"""
    return {
        'free': {
            'name': 'Free Plan',
            'price': 0,
            'billing': 'monthly',
            'features': [
                '1 Device monitoring',
                'Basic security scans',
                'Email alerts',
                'Community support'
            ],
            'device_limit': 1,
            'scan_limit': 1
        },
        'personal': {
            'name': 'Personal Plan',
            'price': 9.99,
            'billing': 'monthly',
            'features': [
                'Up to 3 devices',
                'Advanced security scans',
                'Real-time monitoring',
                'Email & SMS alerts',
                'Priority support'
            ],
            'device_limit': 3,
            'scan_limit': 4
        },
        'pro': {
            'name': 'Pro Plan',
            'price': 29.99,
            'billing': 'monthly',
            'features': [
                'Up to 25 devices',
                'Enterprise security scans',
                'Advanced threat detection',
                'Custom alerts',
                'API access',
                'Dedicated support'
            ],
            'device_limit': 25,
            'scan_limit': 30
        },
        'enterprise': {
            'name': 'Enterprise Plan',
            'price': 99.99,
            'billing': 'monthly',
            'features': [
                'Unlimited devices',
                'Full security suite',
                'Custom integrations',
                'White-label options',
                'SLA guarantee',
                '24/7 phone support'
            ],
            'device_limit': float('inf'),
            'scan_limit': float('inf')
        }
    }

def generate_paypal_payment_url(plan_key, amount, billing_cycle='monthly'):
    """Generate PayPal payment URL (simulated for demo)"""
    try:
        # Get PayPal link from settings
        paypal_setting = SystemSettings.query.filter_by(key='paypal_link').first()
        base_paypal_url = paypal_setting.value if paypal_setting else 'https://paypal.me/yallahack'
        
        # In a real implementation, you would use PayPal SDK to create payment
        # For demo purposes, we'll create a simulated PayPal URL
        payment_id = str(uuid.uuid4())
        
        # Construct PayPal URL with amount
        paypal_url = f"{base_paypal_url}/{amount}"
        
        return {
            'payment_id': payment_id,
            'paypal_url': paypal_url,
            'amount': amount,
            'currency': 'USD',
            'plan': plan_key,
            'billing_cycle': billing_cycle
        }
        
    except Exception as e:
        print(f"Error generating PayPal URL: {e}")
        return None

@paypal_bp.route('/plans', methods=['GET'])
def get_plans():
    """Get available subscription plans"""
    try:
        plans = get_subscription_plans()
        return jsonify({'plans': plans}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get plans: {str(e)}'}), 500

@paypal_bp.route('/current', methods=['GET'])
def get_current_subscription():
    """Get current user subscription"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        subscription = {
            'tier': user.subscription_tier,
            'status': user.subscription_status,
            'start_date': user.subscription_start_date.isoformat() if user.subscription_start_date else None,
            'end_date': user.subscription_end_date.isoformat() if user.subscription_end_date else None,
            'auto_renew': True  # Simulated for demo
        }
        
        return jsonify({'subscription': subscription}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get subscription: {str(e)}'}), 500

@paypal_bp.route('/initiate-payment', methods=['POST'])
def initiate_payment():
    """Initiate PayPal payment for subscription"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        plan_key = data.get('plan')
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        if not plan_key:
            return jsonify({'error': 'Plan is required'}), 400
        
        plans = get_subscription_plans()
        if plan_key not in plans:
            return jsonify({'error': 'Invalid plan'}), 400
        
        plan = plans[plan_key]
        
        # Calculate amount based on billing cycle
        amount = plan['price']
        if billing_cycle == 'yearly':
            amount = amount * 10  # 2 months free for yearly billing
        
        # Generate PayPal payment URL
        payment_info = generate_paypal_payment_url(plan_key, amount, billing_cycle)
        
        if not payment_info:
            return jsonify({'error': 'Failed to generate payment URL'}), 500
        
        # Store pending payment info in session (in real app, use database)
        session['pending_payment'] = {
            'payment_id': payment_info['payment_id'],
            'plan': plan_key,
            'amount': amount,
            'billing_cycle': billing_cycle,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Log payment initiation
        log_activity(
            user_id,
            'payment_initiated',
            f'Payment initiated for {plan["name"]} - ${amount}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({
            'payment_id': payment_info['payment_id'],
            'paypal_url': payment_info['paypal_url'],
            'amount': amount,
            'plan': plan['name'],
            'billing_cycle': billing_cycle
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to initiate payment: {str(e)}'}), 500

@paypal_bp.route('/confirm-payment', methods=['POST'])
def confirm_payment():
    """Confirm PayPal payment and activate subscription"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get pending payment from session
        pending_payment = session.get('pending_payment')
        if not pending_payment:
            return jsonify({'error': 'No pending payment found'}), 400
        
        # In a real implementation, you would verify the payment with PayPal
        # For demo purposes, we'll simulate successful payment confirmation
        
        plan_key = pending_payment['plan']
        billing_cycle = pending_payment['billing_cycle']
        amount = pending_payment['amount']
        
        # Update user subscription
        user.subscription_tier = plan_key
        user.subscription_status = 'active'
        user.subscription_start_date = datetime.utcnow()
        
        # Calculate end date based on billing cycle
        if billing_cycle == 'monthly':
            user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
        elif billing_cycle == 'yearly':
            user.subscription_end_date = datetime.utcnow() + timedelta(days=365)
        
        db.session.commit()
        
        # Clear pending payment from session
        session.pop('pending_payment', None)
        
        # Update session with new subscription info
        session['subscription_tier'] = plan_key
        
        # Log successful payment
        log_activity(
            user_id,
            'payment_confirmed',
            f'Payment confirmed for {plan_key} plan - ${amount}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Payment confirmed and subscription activated',
            'subscription': {
                'tier': user.subscription_tier,
                'status': user.subscription_status,
                'start_date': user.subscription_start_date.isoformat(),
                'end_date': user.subscription_end_date.isoformat() if user.subscription_end_date else None
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to confirm payment: {str(e)}'}), 500

@paypal_bp.route('/cancel-subscription', methods=['POST'])
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
            return jsonify({'error': 'Cannot cancel free plan'}), 400
        
        # Set subscription to expire at the end of current billing period
        # For demo purposes, we'll set it to expire in 7 days
        user.subscription_status = 'cancelled'
        user.subscription_end_date = datetime.utcnow() + timedelta(days=7)
        
        db.session.commit()
        
        # Log cancellation
        log_activity(
            user_id,
            'subscription_cancelled',
            f'Subscription cancelled for {user.subscription_tier} plan',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Subscription cancelled successfully',
            'subscription': {
                'tier': user.subscription_tier,
                'status': user.subscription_status,
                'end_date': user.subscription_end_date.isoformat()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to cancel subscription: {str(e)}'}), 500

@paypal_bp.route('/payment-history', methods=['GET'])
def get_payment_history():
    """Get user payment history"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get payment-related activities from activity log
        activities = ActivityLog.query.filter(
            ActivityLog.user_id == user_id,
            ActivityLog.action.in_(['payment_initiated', 'payment_confirmed', 'subscription_cancelled'])
        ).order_by(ActivityLog.created_at.desc()).limit(20).all()
        
        payment_history = []
        for activity in activities:
            payment_history.append({
                'id': activity.id,
                'action': activity.action,
                'description': activity.description,
                'date': activity.created_at.isoformat(),
                'ip_address': activity.ip_address
            })
        
        return jsonify({'payment_history': payment_history}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get payment history: {str(e)}'}), 500

@paypal_bp.route('/webhook', methods=['POST'])
def paypal_webhook():
    """Handle PayPal webhook notifications"""
    try:
        # In a real implementation, you would verify the webhook signature
        # and process PayPal notifications for subscription events
        
        data = request.get_json()
        event_type = data.get('event_type')
        
        print(f"PayPal webhook received: {event_type}")
        
        # Handle different webhook events
        if event_type == 'BILLING.SUBSCRIPTION.ACTIVATED':
            # Handle subscription activation
            pass
        elif event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
            # Handle subscription cancellation
            pass
        elif event_type == 'PAYMENT.SALE.COMPLETED':
            # Handle successful payment
            pass
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"PayPal webhook error: {e}")
        return jsonify({'error': 'Webhook processing failed'}), 500

@paypal_bp.route('/settings', methods=['GET'])
def get_paypal_settings():
    """Get PayPal configuration settings (admin only)"""
    try:
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        
        if not user_id or not is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        paypal_link = SystemSettings.query.filter_by(key='paypal_link').first()
        
        settings = {
            'paypal_link': paypal_link.value if paypal_link else 'https://paypal.me/yallahack'
        }
        
        return jsonify({'settings': settings}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get PayPal settings: {str(e)}'}), 500

@paypal_bp.route('/settings', methods=['PUT'])
def update_paypal_settings():
    """Update PayPal configuration settings (admin only)"""
    try:
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        
        if not user_id or not is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        
        if 'paypal_link' in data:
            setting = SystemSettings.query.filter_by(key='paypal_link').first()
            if setting:
                setting.value = data['paypal_link']
                setting.updated_at = datetime.utcnow()
            else:
                setting = SystemSettings(
                    key='paypal_link',
                    value=data['paypal_link'],
                    description='PayPal payment link'
                )
                db.session.add(setting)
        
        db.session.commit()
        
        # Log admin action
        log_activity(
            user_id,
            'paypal_settings_updated',
            'Admin updated PayPal settings',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({'message': 'PayPal settings updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update PayPal settings: {str(e)}'}), 500

