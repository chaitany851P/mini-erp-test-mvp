from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.admin_dashboard, name='admin'),
    # Predictive dashboard UI and data
    path('predictive/', views.predictive_dashboard, name='predictive'),
    path('data/students/', views.students_data_json, name='students_data'),
    path('data/alerts/', views.alerts_json, name='alerts_data'),
    # Self-only view
    path('my/', views.my_dashboard, name='my'),
    path('data/my/', views.my_summary_json, name='my_summary'),
    # Existing realtime JSON/SSE endpoints
    path('at-risk/', views.at_risk_json, name='at_risk_json'),
    path('at-risk/stream/', views.at_risk_stream, name='at_risk_stream'),
    path('analytics/', views.analytics_json, name='analytics_json'),
    path('analytics/stream/', views.analytics_stream, name='analytics_stream'),
]
