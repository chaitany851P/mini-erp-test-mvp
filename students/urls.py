from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Attendance
    path('attendance/', views.attendance_collection, name='attendance_collection'),
    path('attendance/<str:doc_id>/', views.attendance_document, name='attendance_document'),

    # Fees (Firestore-backed API, separate from existing fees app)
    path('fees/', views.fees_collection, name='fees_collection'),
    path('fees/<str:doc_id>/', views.fees_document, name='fees_document'),

    # Exams
    path('exams/', views.exams_collection, name='exams_collection'),
    path('exams/<str:doc_id>/', views.exams_document, name='exams_document'),

    # Notifications
    path('notifications/', views.notifications_collection, name='notifications_collection'),
    path('notifications/<str:doc_id>/read/', views.notification_mark_read, name='notification_mark_read'),

    # Student profiles
    path('profiles/', views.profile_collection, name='profile_collection'),
    path('profiles/<str:student_id>/', views.profile_document, name='profile_document'),

    # Leaves
    path('leaves/', views.leaves_collection, name='leaves_collection'),
    path('leaves/<str:doc_id>/', views.leaves_document, name='leaves_document'),

    # Hostel applications
    path('hostel-applications/', views.hostel_applications_collection, name='hostel_applications_collection'),
    path('hostel-applications/<str:doc_id>/', views.hostel_applications_document, name='hostel_applications_document'),

    # Pages (HTML)
    path('me/profile/', views.profile_page, name='profile_page'),
    path('me/leaves/', views.leaves_page, name='leaves_page'),
    path('me/hostel/', views.hostel_applications_page, name='hostel_applications_page'),
    path('me/risk-summary/', views.student_risk_summary, name='student_risk_summary'),
    path('my/fees/', views.my_fees, name='my_fees'),

    # Admin/Counselor pages
    path('admin/leaves/', views.admin_leaves_page, name='admin_leaves_page'),
    path('admin/hostel/', views.admin_hostel_page, name='admin_hostel_page'),
]
