from django.urls import path
from . import views
from . import export_views

urlpatterns = [
    # Authentication
    path('login/', views.custom_login_view, name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    path('signup/', views.custom_signup_view, name='signup'),
    
    # Dashboards
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('faculty-dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    
    # Admin functions
    path('admin/add-student/', views.admin_add_student_view, name='admin_add_student'),
    path('admin/users/', views.users_list_view, name='users_list'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    
    # Excel Export URLs
    path('export/students/', export_views.export_students_excel, name='export_students'),
    path('export/attendance/', export_views.export_attendance_excel, name='export_attendance'),
    path('export/fees/', export_views.export_fees_excel, name='export_fees'),
    path('export/risk-analysis/', export_views.export_risk_analysis_excel, name='export_risk_analysis'),
    path('export/comprehensive/', export_views.export_comprehensive_report, name='export_comprehensive'),
]
