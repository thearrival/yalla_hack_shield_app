# Yalla-Hack Shield 

## 🛡️ Advanced Cybersecurity Platform

Yalla-Hack Shield Enhanced is a comprehensive cybersecurity platform designed to provide enterprise-grade endpoint protection, device management, and automated threat detection capabilities. Built with modern web technologies and inspired by industry-leading solutions, this platform offers scalable subscription tiers, automated email notifications, and seamless PayPal integration.

![Yalla-Hack Shield](src/static/YallaHacklogo.png)

## ✨ Key Features

### 🔐 Multi-Tier Subscription Model
- **Free Plan**: 1 device monitoring with basic security scans
- **Personal Plan ($9.99/month)**: Up to 3 devices with advanced features
- **Pro Plan ($29.99/month)**: Up to 25 devices with enterprise capabilities
- **Enterprise Plan ($99.99/month)**: Unlimited devices with full security suite

### 📱 Comprehensive Device Management
- Real-time device status monitoring (online/offline/compromised)
- Support for multiple device types (desktop, laptop, mobile, server, tablet)
- Cross-platform compatibility (Windows, macOS, Linux, iOS, Android)
- Automated security scanning and vulnerability assessment

### 🚨 Advanced Threat Detection
- Rule-based detection engine with customizable security policies
- Behavioral analysis for anomaly detection
- Real-time security event monitoring and alerting
- Comprehensive threat severity classification

### 📧 Automated Email Notifications
- Professional HTML email templates for security alerts
- Welcome emails for new user onboarding
- Customizable notification preferences
- Asynchronous email processing for optimal performance

### 💳 Seamless PayPal Integration
- Secure subscription management and billing
- One-click plan upgrades and downgrades
- Comprehensive payment history tracking
- Automated subscription lifecycle management

### 🎨 Modern User Interface
- Responsive design optimized for all devices
- Intuitive dashboard with real-time metrics
- Professional Yalla-Hack branding and visual identity
- Accessibility-compliant design principles

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or later
- pip (Python package installer)
- Virtual environment support

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd yalla_hack_shield_enhanced
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python src/main.py
   ```
   The application will automatically create the database and default admin user.

5. **Access the application**
   Open your browser and navigate to `http://localhost:5001`

### Default Admin Credentials
- **Username**: admin
- **Password**: YallaHack2025!

## 🏗️ Architecture

### Backend Technologies
- **Flask 3.1.1**: Web framework and RESTful API
- **SQLAlchemy**: Object-relational mapping (ORM)
- **SQLite**: Database (development) / PostgreSQL (production)
- **Flask-CORS**: Cross-origin resource sharing
- **Python 3.11**: Core programming language

### Frontend Technologies
- **HTML5**: Semantic markup with modern standards
- **CSS3**: Advanced styling with responsive design
- **JavaScript ES6+**: Dynamic user interactions
- **Font Awesome 6.4.0**: Comprehensive icon library

### Service Architecture
```
├── Authentication Service    # User registration, login, session management
├── Device Management        # Device CRUD, monitoring, scanning
├── Subscription Service     # PayPal integration, plan management
├── Email Automation        # Notification templates, delivery management
├── Admin Panel             # System configuration, user management
└── Security Events        # Threat detection, alert processing
```

## 📊 Database Schema

### Core Entities
- **Users**: User profiles, subscription status, authentication
- **Devices**: Device registration, status, configuration
- **Security Events**: Threat detection, severity classification
- **Activity Logs**: Audit trails, user actions
- **System Settings**: Configuration, email/PayPal settings

## 🔧 Configuration

### Environment Variables
```bash
# Database Configuration
DATABASE_URL=sqlite:///app.db

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# PayPal Configuration
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret
PAYPAL_MODE=sandbox  # or 'live' for production
```

### System Settings (Admin Panel)
- Email notifications enable/disable
- PayPal payment link configuration
- Support email address
- Company branding settings

## 🔌 API Reference

### Authentication Endpoints
```
POST /api/auth/register     # User registration
POST /api/auth/login        # User login
GET  /api/auth/session      # Session validation
POST /api/auth/logout       # User logout
```

### Device Management
```
GET    /api/devices              # List user devices
POST   /api/devices              # Register new device
GET    /api/devices/{id}         # Get device details
PUT    /api/devices/{id}         # Update device
DELETE /api/devices/{id}         # Remove device
POST   /api/devices/{id}/scan    # Initiate security scan
GET    /api/devices/summary      # Device statistics
```

### Subscription Management
```
GET  /api/paypal/plans              # Available subscription plans
GET  /api/paypal/current            # Current subscription status
POST /api/paypal/initiate-payment   # Start payment process
POST /api/paypal/confirm-payment    # Confirm subscription
POST /api/paypal/cancel-subscription # Cancel subscription
GET  /api/paypal/payment-history    # Payment transaction history
```

### Email Services
```
POST /api/email/test-email        # Test email functionality (admin)
GET  /api/email/email-settings    # Get email configuration
PUT  /api/email/email-settings    # Update email settings (admin)
```

## 🧪 Testing

### Running Tests
```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# All tests with coverage
python -m pytest --cov=src tests/
```

### Test Categories
- **Unit Tests**: Individual component functionality
- **Integration Tests**: Service interaction validation
- **API Tests**: Endpoint behavior and response validation
- **Security Tests**: Authentication and authorization
- **Performance Tests**: Load and stress testing

## 🚀 Deployment

### Development Deployment
```bash
python src/main.py
```
Access at `http://localhost:5001`

### Production Deployment

#### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 src.main:app
```

#### Using Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5001
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "src.main:app"]
```

#### Cloud Deployment
The application is compatible with:
- **Heroku**: Direct deployment with Procfile
- **AWS**: EC2, Elastic Beanstalk, or ECS
- **Google Cloud**: App Engine or Compute Engine
- **Azure**: App Service or Container Instances

## 📈 Monitoring and Maintenance

### Health Checks
```bash
# Application health
curl http://localhost:5001/api/auth/session

# Database connectivity
python -c "from src.models.user import db; print('DB OK' if db else 'DB Error')"
```

### Log Management
- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Security events: Database audit trail

### Backup Procedures
```bash
# Database backup
sqlite3 src/database/app.db ".backup backup_$(date +%Y%m%d).db"

# Full application backup
tar -czf yalla_hack_backup_$(date +%Y%m%d).tar.gz .
```

## 🔒 Security Considerations

### Authentication Security
- Secure password hashing with salt
- Session-based authentication with timeout
- Protection against brute force attacks
- Comprehensive audit logging

### Data Protection
- Input validation and sanitization
- SQL injection prevention through ORM
- XSS protection in frontend
- CSRF protection for state-changing operations

### Infrastructure Security
- HTTPS/TLS encryption for all communications
- Secure database configuration
- Regular security updates and patches
- Firewall and access control configuration

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make changes and add tests
4. Run test suite: `pytest`
5. Commit changes: `git commit -m "Add new feature"`
6. Push to branch: `git push origin feature/new-feature`
7. Submit a pull request

### Code Standards
- Follow PEP 8 Python style guidelines
- Maintain test coverage above 80%
- Include docstrings for all functions and classes
- Use type hints where appropriate

### Documentation
- Update README for new features
- Add API documentation for new endpoints
- Include inline code comments for complex logic
- Update user guides for UI changes

## 📞 Support

### Getting Help
- **Documentation**: Comprehensive guides and API reference
- **Email Support**: support@yalla-hack.net
- **Issue Tracker**: GitHub Issues for bug reports and feature requests

### Enterprise Support
- **Pro Plan**: Priority email support
- **Enterprise Plan**: 24/7 phone support and SLA guarantees
- **Custom Solutions**: Tailored implementations and integrations

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Flask Community**: Excellent web framework and ecosystem
- **Font Awesome**: Comprehensive icon library
- **PayPal**: Secure payment processing integration
- **SQLAlchemy**: Powerful and flexible ORM

---

**Yalla-Hack Shield Enhanced** - Protecting your digital world, one endpoint at a time.

For more information, visit [yalla-hack.net](https://yalla-hack.net) or contact our support team at support@yalla-hack.net.

