from django.urls import path
from . import views

app_name = 'hostel'

urlpatterns = [
    path('', views.hostel_requests, name='requests'),
    path('request/', views.hostel_request, name='request'),
    path('allocations/', views.hostel_allocations, name='allocations'),
]