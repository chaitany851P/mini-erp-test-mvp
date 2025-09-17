# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a Mini ERP System hackathon MVP built with Django 5.2.6 and Firebase Firestore. It's an educational management system with admissions, fee management, hostel allocation, and admin dashboard functionality.

## Development Commands

### Environment Setup
```powershell
# Create and activate virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Database Operations
```powershell
# Apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Development Server
```powershell
# Run development server
python manage.py runserver

# Access application at http://127.0.0.1:8000
```

### Testing
```powershell
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test admissions
python manage.py test fees
python manage.py test hostel
python manage.py test dashboard

# Run specific test method
python manage.py test admissions.tests.AdmissionTestCase.test_student_creation
```

### Static Files and Media
```powershell
# Collect static files for production
python manage.py collectstatic

# Clear media/receipts directory for testing
Remove-Item -Recurse -Force media\receipts\*
```

## Architecture Overview

### Hybrid Data Storage Pattern
The system uses a unique **dual storage architecture** with both Firestore (cloud) and SQLite (local) databases:

- **Primary**: Firebase Firestore for cloud storage and real-time capabilities
- **Fallback**: Local SQLite database for offline functionality
- **Firebase Utils**: `mini_erp/firebase_utils.py` provides abstraction layer
- **Graceful Degradation**: System works without Firebase credentials using SQLite

### Core Module Structure

#### 1. Admissions Module (`admissions/`)
- **Model**: `Admission` with student lifecycle (pending → approved/rejected)
- **Firestore Collection**: `admissions/{student_id}`
- **Key Feature**: Auto-generated unique student IDs

#### 2. Fees Module (`fees/`)
- **Model**: `FeePayment` with multiple payment modes
- **Firestore Collection**: `fees/{transaction_id}`
- **Key Feature**: PDF receipt generation using ReportLab (`pdf_generator.py`)

#### 3. Hostel Module (`hostel/`)
- **Models**: `HostelRequest`, `HostelAllocation`, `HostelCapacity`
- **Firestore Collections**: `hostel_requests/`, `hostel_allocation/`
- **Key Feature**: Capacity management with occupancy tracking

#### 4. Dashboard Module (`dashboard/`)
- **Purpose**: Real-time statistics aggregation
- **Data Sources**: Combines Firestore and local database counts
- **Strategy**: Takes maximum value between cloud and local data

### Firebase Integration Pattern

All models follow this pattern for dual storage:
1. Save to local SQLite database (Django ORM)
2. Optionally sync to Firestore using `firebase_utils.py`
3. Dashboard aggregates data from both sources
4. System degrades gracefully if Firestore unavailable

### URL Structure
```
/                     # Home page
/admissions/          # Student application forms
/fees/                # Fee payment processing
/hostel/              # Room requests and allocations
/dashboard/           # Admin statistics dashboard
/admin/               # Django admin interface
```

## Firebase Configuration

### Required Files
- `firebase-admin-sdk.json` in project root (for production)
- `.env` file with Firebase credentials (optional)

### Firestore Schema
Collections follow predictable structure:
- `admissions/{student_id}` - Student applications
- `fees/{transaction_id}` - Fee payments
- `hostel_requests/{request_id}` - Room requests
- `hostel_allocation/{allocation_id}` - Room allocations

## Key Development Patterns

### Error Handling
- Comprehensive logging throughout application
- Firebase operations wrapped in try-catch blocks
- Fallback to local database when Firestore fails
- User-friendly error messages in forms

### PDF Generation
- Uses ReportLab for professional receipts
- Template in `fees/pdf_generator.py`
- Saves to `media/receipts/` directory
- Branded with institution information

### Form Processing
- Django forms with CSRF protection
- Validation in both frontend and backend
- Real-time status updates
- Bootstrap 5 for responsive design

### Unique ID Generation
- Student ID: Auto-generated in admission forms
- Transaction ID: `TXN{10-digit-number}` format
- Hostel Request ID: `HST{8-digit-number}` format  
- Allocation ID: `ALLOC{8-digit-number}` format

## Testing Strategy

When writing tests:
- Mock Firebase operations using `unittest.mock`
- Test both successful and failed Firebase connections
- Verify PDF generation functionality
- Test unique ID generation and collision handling
- Test form validation and error handling

## Development Notes

### Working with Firebase
- Always check if `firebase_utils.get_firestore_client()` returns None
- Log Firebase errors but don't crash the application
- Test both online and offline scenarios

### PDF Receipts
- PDFs are generated in memory and returned as HTTP responses
- Receipt templates are in `fees/pdf_generator.py`
- ReportLab styling uses custom paragraph styles

### Static Files
- Bootstrap 5 included in base template
- Custom CSS in `static/` directory
- Media files served during development only

### Database Migrations
- Models use UUIDs for primary keys in some cases
- DateTime fields use `timezone.now()` for consistency
- Choice fields defined as constants in models

This system prioritizes reliability through redundant storage and graceful degradation, making it suitable for educational environments where uptime is critical.