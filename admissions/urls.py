from django.urls import path
from . import views

app_name = 'admissions'

urlpatterns = [
    path('', views.admission_list, name='list'),
    path('apply/', views.admission_apply, name='apply'),
    path('<str:student_id>/', views.admission_detail, name='detail'),
]