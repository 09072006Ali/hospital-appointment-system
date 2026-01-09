"""
Hospital Appointment System - Admin Configuration

Registers all models with Django Admin for management.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department, Doctor, Patient, Appointment, MedicalRecord


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Custom User Admin with role flags."""
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_doctor', 'is_patient', 'is_staff')
    list_filter = ('is_doctor', 'is_patient', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Role Flags', {'fields': ('is_doctor', 'is_patient', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Flags', {'fields': ('is_doctor', 'is_patient')}),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Department Admin."""
    list_display = ('name', 'doctor_count', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    """Doctor Admin."""
    list_display = ('__str__', 'department', 'specialization', 'experience_years', 'is_available')
    list_filter = ('department', 'is_available')
    search_fields = ('user__first_name', 'user__last_name', 'specialization')
    raw_id_fields = ('user',)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """Patient Admin."""
    list_display = ('__str__', 'date_of_birth', 'blood_type', 'age')
    list_filter = ('blood_type',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    raw_id_fields = ('user',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Appointment Admin."""
    list_display = ('patient', 'doctor', 'date', 'time', 'status', 'created_at')
    list_filter = ('status', 'date', 'doctor__department')
    search_fields = ('patient__user__first_name', 'doctor__user__first_name')
    date_hierarchy = 'date'
    raw_id_fields = ('doctor', 'patient')
    actions = ['mark_completed', 'mark_cancelled']
    
    @admin.action(description="Mark selected appointments as Completed")
    def mark_completed(self, request, queryset):
        queryset.update(status='completed')
    
    @admin.action(description="Mark selected appointments as Cancelled")
    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    """Medical Record Admin."""
    list_display = ('appointment', 'created_at', 'follow_up_date')
    list_filter = ('created_at',)
    search_fields = ('diagnosis', 'medicines')
    raw_id_fields = ('appointment',)
