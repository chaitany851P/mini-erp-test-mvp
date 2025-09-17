Mini ERP System (Hackathon MVP) 🎯

A comprehensive educational management system built with Django and Firebase Firestore, featuring real-time admissions, fee management, and hostel allocation.

🔹 Features
Core Modules

Admissions 🎓

Student application form with validation

Real-time application tracking

Admin approval workflow

Firestore cloud storage integration

Fees 💰

Fee payment processing

Multiple payment modes (Cash, Card, UPI, etc.)

Automated PDF receipt generation

Payment history tracking

Hostel 🏠

Room request submission

Capacity management

Allocation tracking

Occupancy statistics

Admin Dashboard 📊

Real-time statistics

Total admissions count

Fees collected summary

Hostel occupancy with progress bars

Responsive Bootstrap interface

🔹 Tech Stack

Backend: Django 5.2.6

Database: Firestore (Cloud) + SQLite (Local backup)

PDF Generation: ReportLab

Frontend: HTML/CSS/JS with Bootstrap 5

Cloud: Firebase Admin SDK

Environment: Python virtual environment

🔹 Firestore Structure
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

🚀 Setup Instructions
Prerequisites

Python 3.8 or higher

Git

1. Clone the Repository
git clone <repository-url>
cd mini-erp-hackathon

2. Create Virtual Environment
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

3. Install Dependencies
pip install -r requirements.txt

4. Configure Firebase (Optional)

Go to Firebase Console

Create a new project or use an existing one

Generate a service account key:

Project Settings → Service accounts → Generate new private key

Save as firebase-admin-sdk.json in the project root

Copy .env.example to .env and fill in Firebase credentials

Note: The system works without Firebase credentials using local SQLite database as a fallback.

5. Run Database Migrations
python manage.py makemigrations
python manage.py migrate

6. Create Superuser (Optional)
python manage.py createsuperuser

7. Run Development Server
python manage.py runserver


Visit http://127.0.0.1:8000 to access the application.

🎯 Usage Guide
For Students

Apply for Admission

Admissions → Apply Now

Fill out the application form

Receive unique Student ID

Track application status

Pay Fees

Fees → Pay Fees

Enter student details and payment information

Download PDF receipt automatically

Request Hostel

Hostel → Request Room

Submit room preferences

Check allocation status

For Administrators

View Dashboard

Monitor real-time statistics

Track system performance

Manage Applications

Review and approve/reject student applications

Track application workflow

Monitor Finances

View fee collection statistics

Download payment reports

Track revenue

📁 Project Structure
mini-erp-hackathon/
├── mini_erp/                 # Main Django project
│   ├── settings.py
│   ├── urls.py
│   ├── firebase_utils.py
│   └── wsgi.py
├── admissions/               # Admissions app
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   └── urls.py
├── fees/                     # Fees app
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── pdf_generator.py
│   └── urls.py
├── hostel/                   # Hostel app
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   └── urls.py
├── dashboard/                # Dashboard app
│   ├── views.py
│   └── urls.py
├── templates/                # HTML templates
├── static/                   # Static files (CSS, JS)
├── media/                    # Upload directory
├── requirements.txt
├── .env.example
└── README.md

🔹 Key Features Implemented

Real-time Data Sync: Firestore cloud storage with SQLite fallback

PDF Generation: Professional receipts via ReportLab

Responsive Design: Mobile-first Bootstrap 5 UI

Error Handling: Logging system and graceful user feedback

Security: CSRF protection, input validation, and sanitization

🎯 Future Enhancements

Email/SMS notifications for fees and admission status

Role-based access control for students, admins, and wardens

Exam management module with grade and result generation

Advanced reporting with charts and analytics

🐛 Troubleshooting

Common Issues:

Firebase Connection: Ensure JSON key is present and project config is correct

PDF Errors: Verify ReportLab installation, media directory permissions, and fonts

Database Issues: Apply migrations, check SQLite permissions, and activate virtual environment

📄 License

This project is for educational purposes (hackathon MVP). Free to use and modify.

🤝 Contributing

Fork the repository

Create a feature branch

Commit changes

Push to the branch

Create a Pull Request

Built with ❤️ for educational management