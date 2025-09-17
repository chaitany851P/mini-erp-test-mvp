# Mini ERP System (Hackathon MVP) 🎯

A comprehensive educational management system built with Django and Firebase Firestore, featuring real-time admissions, fee management, and hostel allocation.

## 🔹 Features

### Core Modules

1. **Admissions** 🎓
   - Student application form with validation
   - Real-time application tracking
   - Admin approval workflow
   - Firestore cloud storage integration

2. **Fees** 💰
   - Fee payment processing
   - Multiple payment modes (Cash, Card, UPI, etc.)
   - Automated PDF receipt generation
   - Payment history tracking

3. **Hostel** 🏠
   - Room request submission
   - Capacity management
   - Allocation tracking
   - Occupancy statistics

4. **Admin Dashboard** 📊
   - Real-time statistics
   - Total admissions count
   - Fees collected summary
   - Hostel occupancy with progress bars
   - Responsive Bootstrap interface

## 🔹 Tech Stack

- **Backend**: Django 5.2.6
- **Database**: Firestore (Cloud) + SQLite (Local backup)
- **PDF Generation**: ReportLab
- **Frontend**: HTML/CSS/JS with Bootstrap 5
- **Cloud**: Firebase Admin SDK
- **Environment**: Python virtual environment

## 🔹 Firestore Structure

```
admissions/{student_id}
├── student_id: string
├── first_name: string
├── last_name: string
├── email: string
├── phone: string
├── date_of_birth: string (ISO format)
├── gender: string
├── address: string
├── course: string
├── status: string (pending/approved/rejected)
├── created_at: string (ISO format)
└── updated_at: string (ISO format)

fees/{transaction_id}
├── transaction_id: string
├── student_id: string
├── student_name: string
├── student_email: string
├── amount: string
├── payment_mode: string
├── fee_type: string
├── status: string
├── notes: string
└── created_at: string (ISO format)

hostel_requests/{request_id}
├── request_id: string
├── student_id: string
├── student_name: string
├── student_email: string
├── student_phone: string
├── room_type: string
├── preferences: string
├── status: string
├── created_at: string (ISO format)
└── processed_at: string (ISO format)

hostel_allocation/{allocation_id}
├── allocation_id: string
├── student_id: string
├── student_name: string
├── room_number: string
├── room_type: string
├── allocated_at: string (ISO format)
├── check_in_date: string (ISO format)
├── check_out_date: string (ISO format)
└── is_active: boolean
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd mini-erp-hackathon
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Firebase (Optional)

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create a new project or use existing one
3. Generate a service account key:
   - Go to Project Settings → Service accounts
   - Generate new private key
   - Save as `firebase-admin-sdk.json` in the project root

4. Copy `.env.example` to `.env` and fill in your Firebase credentials (if using environment variables)

> **Note**: The system works without Firebase credentials using local SQLite database as fallback.

### 5. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to access the application.

## 🎯 Usage Guide

### For Students

1. **Apply for Admission**
   - Navigate to Admissions → Apply Now
   - Fill out the application form
   - Receive unique Student ID
   - Track application status

2. **Pay Fees**
   - Navigate to Fees → Pay Fees
   - Enter student details and payment information
   - Download PDF receipt automatically

3. **Request Hostel**
   - Navigate to Hostel → Request Room
   - Submit room preference
   - Check allocation status

### For Administrators

1. **View Dashboard**
   - Access comprehensive statistics
   - Monitor real-time data
   - Track system performance

2. **Manage Applications**
   - Review student applications
   - Approve/reject admissions
   - Track application flow

3. **Monitor Finances**
   - View fee collection statistics
   - Download payment reports
   - Track revenue

## 📁 Project Structure

```
mini-erp-hackathon/
├── mini_erp/                 # Main Django project
│   ├── settings.py           # Django settings
│   ├── urls.py              # Main URL configuration
│   ├── firebase_utils.py    # Firestore utility functions
│   └── wsgi.py              # WSGI configuration
├── admissions/              # Admissions app
│   ├── models.py            # Admission model
│   ├── forms.py             # Application forms
│   ├── views.py             # Business logic
│   └── urls.py              # URL patterns
├── fees/                    # Fees app
│   ├── models.py            # FeePayment model
│   ├── forms.py             # Payment forms
│   ├── views.py             # Payment processing
│   ├── pdf_generator.py     # PDF receipt generation
│   └── urls.py              # URL patterns
├── hostel/                  # Hostel app
│   ├── models.py            # Hostel models
│   ├── forms.py             # Request forms
│   ├── views.py             # Hostel management
│   └── urls.py              # URL patterns
├── dashboard/               # Dashboard app
│   ├── views.py             # Statistics and analytics
│   └── urls.py              # URL patterns
├── templates/               # HTML templates
│   ├── base.html            # Base template with Bootstrap
│   └── home.html            # Landing page
├── static/                  # Static files (CSS, JS)
├── media/                   # Upload directory
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## 🔹 Key Features Implemented

### ✅ Real-time Data Sync
- Firestore integration for cloud storage
- Local SQLite fallback for offline functionality
- Automatic data synchronization

### ✅ PDF Generation
- Professional receipt generation using ReportLab
- Downloadable PDF receipts for fee payments
- Branded templates with school information

### ✅ Responsive Design
- Bootstrap 5 for mobile-first design
- Professional UI with consistent styling
- Interactive dashboard with progress bars

### ✅ Error Handling
- Comprehensive logging system
- Graceful error handling and user feedback
- Fallback mechanisms for service interruptions

### ✅ Security
- Django's built-in security features
- CSRF protection on all forms
- Input validation and sanitization

## 🎯 Future Enhancements

### Stretch Goals (Not Yet Implemented)

1. **Email/SMS Notifications**
   - Fee payment confirmations
   - Application status updates
   - Automated reminders

2. **Role-based Access Control**
   - Student login portal
   - Admin dashboard access control
   - Warden permissions for hostel management

3. **Exam Management Module**
   - Marks entry system
   - PDF result card generation
   - Grade calculations

4. **Advanced Reporting**
   - Financial reports with charts
   - Admission analytics
   - Occupancy trends

## 🐛 Troubleshooting

### Common Issues

1. **Firebase Connection Issues**
   - Ensure `firebase-admin-sdk.json` is in the project root
   - Check internet connectivity
   - Verify Firebase project configuration

2. **PDF Generation Errors**
   - Ensure ReportLab is properly installed
   - Check media directory permissions
   - Verify font availability

3. **Database Issues**
   - Run `python manage.py migrate` to apply migrations
   - Check SQLite file permissions
   - Ensure virtual environment is activated

### Getting Help

1. Check the Django debug output for detailed error messages
2. Review the application logs for Firebase connection issues
3. Ensure all dependencies are installed correctly

## 📄 License

This project is created for educational purposes as part of a hackathon MVP. Feel free to use and modify as needed.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

**Built with ❤️ for educational management**