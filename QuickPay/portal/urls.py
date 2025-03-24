from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('payment', views.portal, name='portal'),
    path('process/', views.process_payment, name='process_payment'),
    path('create-profile/', views.create_customer_profile, name='create_customer_profile'),
    path('add-payment-method/', views.add_payment_method, name='add_payment_method'),
    path('get-profile/', views.get_customer_profile, name='get_customer_profile'),
    path('process-profile-payment/', views.process_profile_payment, name='process_profile_payment'),
]