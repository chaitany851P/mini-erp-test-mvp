from django.urls import path
from . import views

app_name = 'admissions'

urlpatterns = [
    path('apply/', views.admission_apply, name='apply'),
    path('', views.admission_list, name='list'),
    path('<str:student_id>/', views.admission_detail, name='detail'),
    path('<str:student_id>/approve/', views.approve_admission, name='approve'),
    path('<str:student_id>/reject/', views.reject_admission, name='reject'),
    # Lightweight API to fetch student info by student_id for form auto-fill
    path('api/student/<str:student_id>/', views.admission_lookup_api, name='lookup_api'),
]
