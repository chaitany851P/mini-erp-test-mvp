from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    # Local Django model-based endpoints (fallback for Firebase issues)
    path('leaves/', views.leaves_collection_local, name='leaves_local'),
    path('hostel/', views.hostel_applications_collection_local, name='hostel_local'),
]