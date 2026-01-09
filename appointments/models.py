"""
Hospital Appointment System - Database Models

This module defines all database models following the MVT architecture:
- CustomUser: Extended user model with role flags
- Department: Hospital departments
- Doctor: Medical staff profiles
- Patient: Patient profiles
- Appointment: Booking records with conflict prevention
- MedicalRecord: Prescriptions and diagnoses
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone


class CustomUser(AbstractUser):
    """
    Extended User model with role-based flags.
    Inherits from AbstractUser for full authentication support.
    """
    is_doctor = models.BooleanField(default=False, help_text="Designates whether the user is a doctor.")
    is_patient = models.BooleanField(default=False, help_text="Designates whether the user is a patient.")
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.get_full_name() or self.username}"
    
    @property
    def role(self):
        """Returns the user's role as a string."""
        if self.is_superuser:
            return 'Admin'
        elif self.is_doctor:
            return 'Doctor'
        elif self.is_patient:
            return 'Patient'
        return 'Staff'


class Department(models.Model):
    """
    Hospital departments (e.g., Cardiology, Neurology).
    Each department can have multiple doctors.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fa-hospital', help_text="FontAwesome icon class")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
    
    def __str__(self):
        return self.name
    
    @property
    def doctor_count(self):
        return self.doctors.count()


class Doctor(models.Model):
    """
    Doctor profile linked to a User account.
    Each doctor belongs to one department.
    """
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='doctor_profile'
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='doctors'
    )
    specialization = models.CharField(max_length=200)
    profile_pic = models.ImageField(
        upload_to='profile_pics/doctors/', 
        blank=True, 
        null=True,
        default='profile_pics/default_doctor.png'
    )
    experience_years = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True, help_text="Short biography")
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    is_available = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['user__first_name', 'user__last_name']
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        # Ensure the linked user has is_doctor flag set
        if not self.user.is_doctor:
            self.user.is_doctor = True
            self.user.save()
        super().save(*args, **kwargs)


class Patient(models.Model):
    """
    Patient profile linked to a User account.
    Stores medical information like blood type.
    """
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='patient_profile'
    )
    date_of_birth = models.DateField(null=True, blank=True)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=15, blank=True)
    medical_notes = models.TextField(blank=True, help_text="Allergies, chronic conditions, etc.")
    
    class Meta:
        ordering = ['user__first_name', 'user__last_name']
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
    
    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
    def save(self, *args, **kwargs):
        # Ensure the linked user has is_patient flag set
        if not self.user.is_patient:
            self.user.is_patient = True
            self.user.save()
        super().save(*args, **kwargs)
    
    @property
    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None


class Appointment(models.Model):
    """
    Appointment booking between a doctor and patient.
    Includes validation to prevent double-booking.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    TIME_SLOT_CHOICES = [
        ('09:00', '09:00 AM'),
        ('09:30', '09:30 AM'),
        ('10:00', '10:00 AM'),
        ('10:30', '10:30 AM'),
        ('11:00', '11:00 AM'),
        ('11:30', '11:30 AM'),
        ('12:00', '12:00 PM'),
        ('14:00', '02:00 PM'),
        ('14:30', '02:30 PM'),
        ('15:00', '03:00 PM'),
        ('15:30', '03:30 PM'),
        ('16:00', '04:00 PM'),
        ('16:30', '04:30 PM'),
        ('17:00', '05:00 PM'),
    ]
    
    doctor = models.ForeignKey(
        Doctor, 
        on_delete=models.CASCADE, 
        related_name='appointments'
    )
    patient = models.ForeignKey(
        Patient, 
        on_delete=models.CASCADE, 
        related_name='appointments'
    )
    date = models.DateField()
    time = models.CharField(max_length=5, choices=TIME_SLOT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True, help_text="Reason for visit")
    is_video_consultation = models.BooleanField(default=False, help_text="Whether this is a video consultation")
    payment_status = models.CharField(max_length=20, default='pending', help_text="Payment status: pending, paid, refunded")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-time']
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        # Database constraint removed to handle cancelled appointments logic in clean() method
    
    def __str__(self):
        return f"{self.patient} with {self.doctor} on {self.date} at {self.time}"
    
    def clean(self):
        """Validate appointment doesn't conflict with existing ones."""
        # Only validate if doctor, date, and time are all set
        if not hasattr(self, 'doctor') or self.doctor is None:
            return  # Skip validation if doctor not yet assigned
        if not self.date or not self.time:
            return  # Skip validation if date or time not set
            
        if self.pk is None:  # Only check for new appointments
            existing = Appointment.objects.filter(
                doctor=self.doctor,
                date=self.date,
                time=self.time
            ).exclude(status='cancelled')
            if existing.exists():
                raise ValidationError("This time slot is already booked.")
    
    @property
    def is_past(self):
        """Check if appointment date has passed."""
        return self.date < timezone.now().date()
    
    @property
    def time_display(self):
        """Return formatted time display."""
        for code, display in self.TIME_SLOT_CHOICES:
            if code == self.time:
                return display
        return self.time
    
    @property
    def video_room_id(self):
        """Generate unique video room ID for Jitsi Meet."""
        if self.is_video_consultation and self.pk:
            return f"medicare-appointment-{self.pk}-{self.date.strftime('%Y%m%d')}"
        return None


class MedicalRecord(models.Model):
    """
    Medical record/prescription linked to an appointment.
    Created by doctors after completing consultations.
    """
    appointment = models.ForeignKey(
        Appointment, 
        on_delete=models.CASCADE, 
        related_name='medical_records'
    )
    diagnosis = models.TextField(help_text="Doctor's diagnosis")
    symptoms = models.TextField(blank=True, help_text="Patient's symptoms")
    medicines = models.TextField(help_text="Prescribed medicines, one per line")
    instructions = models.TextField(blank=True, help_text="Additional instructions")
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Medical Record'
        verbose_name_plural = 'Medical Records'
    
    def __str__(self):
        return f"Record for {self.appointment.patient} - {self.created_at.strftime('%Y-%m-%d')}"
    
    @property
    def medicine_list(self):
        """Return medicines as a list."""
        return [m.strip() for m in self.medicines.split('\n') if m.strip()]


class Payment(models.Model):
    """
    Payment record for an appointment.
    Tracks payment status, amount, and transaction details.
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('cash', 'Cash (At Hospital)'),
    ]
    
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='card')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    card_last_four = models.CharField(max_length=4, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self):
        return f"Payment #{self.id} - {self.appointment.patient} - ${self.amount} ({self.status})"
    
    def process_refund(self):
        """Process refund for cancelled appointment."""
        if self.status == 'completed':
            self.status = 'refunded'
            self.save()
            return True
        return False

