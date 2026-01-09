"""
Hospital Appointment System - Forms

Django forms for user registration, appointments, and medical records.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, Patient, Appointment, MedicalRecord, Doctor


class PatientRegistrationForm(UserCreationForm):
    """
    Registration form for new patients.
    Creates both User and Patient profile.
    """
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    phone = forms.CharField(
        max_length=15, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    blood_type = forms.ChoiceField(
        choices=[('', 'Select Blood Type')] + list(Patient.BLOOD_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Address'})
    )
    
    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            if field_name == 'username':
                field.widget.attrs['placeholder'] = 'Username'
            elif field_name == 'password1':
                field.widget.attrs['placeholder'] = 'Password'
            elif field_name == 'password2':
                field.widget.attrs['placeholder'] = 'Confirm Password'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_patient = True
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
            # Create patient profile
            Patient.objects.create(
                user=user,
                date_of_birth=self.cleaned_data.get('date_of_birth'),
                blood_type=self.cleaned_data.get('blood_type', ''),
                address=self.cleaned_data.get('address', '')
            )
        return user


class AppointmentBookingForm(forms.ModelForm):
    """
    Form for booking new appointments.
    """
    class Meta:
        model = Appointment
        fields = ('date', 'time', 'is_video_consultation', 'description')
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'min': ''  # Will be set dynamically
            }),
            'time': forms.Select(attrs={'class': 'form-control'}),
            'is_video_consultation': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Describe your symptoms or reason for visit...'
            }),
        }
    
    def __init__(self, *args, doctor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.doctor = doctor
        # Set minimum date to today
        from django.utils import timezone
        self.fields['date'].widget.attrs['min'] = timezone.now().date().isoformat()
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')
        
        if date and time and self.doctor:
            # Check if slot is already booked
            existing = Appointment.objects.filter(
                doctor=self.doctor,
                date=date,
                time=time
            ).exclude(status='cancelled')
            if existing.exists():
                raise ValidationError("This time slot is already booked. Please select another.")
        
        return cleaned_data


class MedicalRecordForm(forms.ModelForm):
    """
    Form for doctors to add prescriptions/medical records.
    """
    class Meta:
        model = MedicalRecord
        fields = ('symptoms', 'diagnosis', 'medicines', 'instructions', 'follow_up_date')
        widgets = {
            'symptoms': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2,
                'placeholder': 'Patient symptoms...'
            }),
            'diagnosis': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Diagnosis...'
            }),
            'medicines': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Enter medicines (one per line)...'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2,
                'placeholder': 'Additional instructions...'
            }),
            'follow_up_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
        }


class DoctorSearchForm(forms.Form):
    """
    Form for searching/filtering doctors.
    """
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by doctor name or specialization...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        from .models import Department
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.all()
