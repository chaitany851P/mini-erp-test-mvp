from django.urls import path
from . import views

app_name = 'fees'

urlpatterns = [
    path('', views.fee_list, name='list'),
    path('payment/', views.fee_payment, name='payment'),
    path('receipt/<str:transaction_id>/', views.download_receipt, name='receipt'),
]