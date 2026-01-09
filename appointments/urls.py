"""
Hospital Appointment System - URL Configuration

Routes for all views in the appointments app.
"""

from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Authentication
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_patient, name='register'),
    
    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('dashboard/patient/', views.patient_dashboard, name='patient_dashboard'),
    
    # Departments & Doctors
    path('departments/', views.department_list, name='department_list'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('doctors/department/<int:department_id>/', views.doctor_list, name='doctors_by_department'),
    
    # Booking
    path('book/<int:doctor_id>/', views.book_appointment, name='book_appointment'),
    path('api/available-slots/<int:doctor_id>/', views.get_available_slots, name='get_available_slots'),
    
    # Appointments
    path('appointment/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointment/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('appointment/<int:appointment_id>/complete/', views.complete_appointment, name='complete_appointment'),
    path('appointment/<int:appointment_id>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('appointment/<int:appointment_id>/prescription/', views.add_prescription, name='add_prescription'),
    
    # Medical Records
    path('medical-history/', views.medical_history, name='medical_history'),
    
    # Payment
    path('appointment/<int:appointment_id>/payment/', views.payment_process, name='payment_process'),
    path('appointment/<int:appointment_id>/payment/success/', views.payment_success, name='payment_success'),
    
    # Video Consultation
    path('appointment/<int:appointment_id>/video/', views.video_consultation, name='video_consultation'),
]
