from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('cashfree/create-order/', views.cashfree_create_order, name='cashfree_create_order'),
    path('cashfree/webhook/', views.cashfree_webhook, name='cashfree_webhook'),
]
