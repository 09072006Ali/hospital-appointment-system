"""
Hospital Appointment System - Views

Handles all HTTP requests and renders appropriate responses.
Includes authentication, dashboards, booking logic, and medical records.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta
import uuid
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import (
    CustomUser, Department, Doctor, Patient, 
    Appointment, MedicalRecord, Payment
)
from .forms import (
    PatientRegistrationForm, AppointmentBookingForm, 
    MedicalRecordForm, DoctorSearchForm
)


# ============================================
# Email Helper
# ============================================

def send_appointment_notification(appointment, subject, intro_message):
    """
    Sends an email notification to the patient for an appointment.
    """
    if not appointment.patient.user.email:
        return  # Cannot send email if patient has no email address

    context = {
        'subject': subject,
        'introductory_message': intro_message,
        'patient_name': appointment.patient.user.get_full_name(),
        'doctor_name': appointment.doctor.user.get_full_name(),
        'department_name': appointment.doctor.department.name,
        'appointment_date': appointment.date.strftime('%B %d, %Y'),
        'appointment_time': appointment.get_time_display(),
        'appointment_status': appointment.get_status_display(),
    }

    # Render HTML and text parts
    html_content = render_to_string('email/appointment_notification.html', context)
    text_content = render_to_string('email/appointment_notification.txt', context)

    # Create the email
    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [appointment.patient.user.email]
    )
    email.attach_alternative(html_content, "text/html")

    try:
        email.send()
    except Exception as e:
        # In a real app, you'd log this error
        print(f"Error sending email: {e}")


# ============================================
# Authentication Views
# ============================================

class CustomLoginView(LoginView):
    """Custom login view with Bootstrap styling."""
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return '/dashboard/'


def register_patient(request):
    """Handle patient registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PatientRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


# ============================================
# Dashboard Views
# ============================================

@login_required
def dashboard(request):
    """
    Main dashboard - redirects based on user role.
    """
    user = request.user
    
    if user.is_superuser or (not user.is_doctor and not user.is_patient):
        return redirect('admin_dashboard')
    elif user.is_doctor:
        return redirect('doctor_dashboard')
    elif user.is_patient:
        return redirect('patient_dashboard')
    
    return redirect('home')


@login_required
def admin_dashboard(request):
    """
    Admin/Manager dashboard - overview of all hospital data.
    """
    today = timezone.now().date()
    
    context = {
        'total_departments': Department.objects.count(),
        'total_doctors': Doctor.objects.count(),
        'total_patients': Patient.objects.count(),
        'total_appointments': Appointment.objects.count(),
        'today_appointments': Appointment.objects.filter(date=today).count(),
        'pending_appointments': Appointment.objects.filter(status='pending').count(),
        'recent_appointments': Appointment.objects.select_related(
            'doctor__user', 'patient__user'
        ).order_by('-created_at')[:10],
        'departments': Department.objects.annotate(
            doc_count=Count('doctors')
        ).order_by('name'),
    }
    return render(request, 'appointments/admin_dashboard.html', context)


@login_required
def doctor_dashboard(request):
    """
    Doctor dashboard - shows today's patients and schedule.
    """
    if not request.user.is_doctor:
        messages.error(request, 'Access denied. Doctor account required.')
        return redirect('dashboard')
    
    try:
        doctor = request.user.doctor_profile
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('home')
    
    today = timezone.now().date()
    
    context = {
        'doctor': doctor,
        'today_appointments': Appointment.objects.filter(
            doctor=doctor, date=today
        ).exclude(status='cancelled').select_related('patient__user').order_by('time'),
        'upcoming_appointments': Appointment.objects.filter(
            doctor=doctor, date__gt=today
        ).exclude(status='cancelled').select_related('patient__user').order_by('date', 'time')[:10],
        'pending_appointments': Appointment.objects.filter(
            doctor=doctor, status='pending'
        ).select_related('patient__user').order_by('date', 'time'),
        'completed_today': Appointment.objects.filter(
            doctor=doctor, date=today, status='completed'
        ).count(),
        'total_patients': Appointment.objects.filter(
            doctor=doctor
        ).values('patient').distinct().count(),
    }
    return render(request, 'appointments/doctor_dashboard.html', context)


@login_required
def patient_dashboard(request):
    """
    Patient dashboard - book appointments and view history.
    """
    if not request.user.is_patient:
        messages.error(request, 'Access denied. Patient account required.')
        return redirect('dashboard')
    
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('home')
    
    today = timezone.now().date()
    
    # Sync payment status for all patient appointments
    # If a Payment record exists (card completed OR cash selected), mark as paid
    appointments_to_sync = Appointment.objects.filter(patient=patient).exclude(payment_status='paid')
    for apt in appointments_to_sync:
        try:
            if hasattr(apt, 'payment') and apt.payment:
                # Payment record exists - either card completed or cash selected
                apt.payment_status = 'paid'
                apt.save(update_fields=['payment_status'])
        except:
            pass
    
    context = {
        'patient': patient,
        'upcoming_appointments': Appointment.objects.filter(
            patient=patient, date__gte=today
        ).exclude(status='cancelled').select_related(
            'doctor__user', 'doctor__department'
        ).order_by('date', 'time'),
        'past_appointments': Appointment.objects.filter(
            patient=patient, date__lt=today
        ).select_related(
            'doctor__user', 'doctor__department'
        ).order_by('-date', '-time')[:10],
        'medical_records': MedicalRecord.objects.filter(
            appointment__patient=patient
        ).select_related('appointment__doctor__user').order_by('-created_at')[:5],
        'departments': Department.objects.all(),
    }
    return render(request, 'appointments/patient_dashboard.html', context)


# ============================================
# Booking Views
# ============================================

def home(request):
    """Home page - landing page for the hospital."""
    departments = Department.objects.annotate(doc_count=Count('doctors'))[:6]
    featured_doctors = Doctor.objects.filter(is_available=True).select_related(
        'user', 'department'
    )[:4]
    
    context = {
        'departments': departments,
        'featured_doctors': featured_doctors,
        'total_doctors': Doctor.objects.filter(is_available=True).count(),
        'total_departments': Department.objects.count(),
    }
    return render(request, 'appointments/home.html', context)


def department_list(request):
    """List all departments."""
    departments = Department.objects.annotate(
        doc_count=Count('doctors')
    ).order_by('name')
    
    return render(request, 'appointments/department_list.html', {
        'departments': departments
    })


def doctor_list(request, department_id=None):
    """List doctors, optionally filtered by department."""
    form = DoctorSearchForm(request.GET)
    doctors = Doctor.objects.filter(is_available=True).select_related('user', 'department')
    
    # Filter by department from URL
    department = None
    if department_id:
        department = get_object_or_404(Department, pk=department_id)
        doctors = doctors.filter(department=department)
    
    # Filter by form
    if form.is_valid():
        if form.cleaned_data.get('department'):
            doctors = doctors.filter(department=form.cleaned_data['department'])
        if form.cleaned_data.get('search'):
            search = form.cleaned_data['search']
            doctors = doctors.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(specialization__icontains=search)
            )
    
    return render(request, 'appointments/doctor_list.html', {
        'doctors': doctors,
        'form': form,
        'department': department,
    })


@login_required
def book_appointment(request, doctor_id):
    """Book an appointment with a specific doctor."""
    if not request.user.is_patient:
        messages.error(request, 'Only patients can book appointments.')
        return redirect('doctor_list')
    
    doctor = get_object_or_404(Doctor, pk=doctor_id, is_available=True)
    patient = request.user.patient_profile
    
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST, doctor=doctor)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.doctor = doctor
            appointment.patient = patient
            
            try:
                appointment.save()

                # Send confirmation email
                send_appointment_notification(
                    appointment,
                    subject="Your appointment has been booked!",
                    intro_message="Your appointment has been successfully booked. Please find the details below."
                )

                messages.success(
                    request, 
                    f'Appointment booked with {doctor} on {appointment.date} at {appointment.time_display}! Please complete payment.'
                )
                return redirect('payment_process', appointment_id=appointment.id)
            except Exception as e:
                # Handle duplicate booking error
                messages.error(request, 'This time slot has just been booked by another patient. Please select a different time.')
                form = AppointmentBookingForm(doctor=doctor)
    else:
        form = AppointmentBookingForm(doctor=doctor)
    
    # Get booked slots for the next 30 days
    today = timezone.now().date()
    booked_slots = {}
    appointments = Appointment.objects.filter(
        doctor=doctor,
        date__gte=today,
        date__lte=today + timedelta(days=30)
    ).exclude(status='cancelled').values('date', 'time')
    
    for apt in appointments:
        date_str = apt['date'].isoformat()
        if date_str not in booked_slots:
            booked_slots[date_str] = []
        booked_slots[date_str].append(apt['time'])
    
    return render(request, 'appointments/book_appointment.html', {
        'doctor': doctor,
        'form': form,
        'booked_slots': booked_slots,
    })


@login_required
def get_available_slots(request, doctor_id):
    """AJAX endpoint to get available time slots for a date."""
    doctor = get_object_or_404(Doctor, pk=doctor_id)
    date_str = request.GET.get('date')
    
    if not date_str:
        return JsonResponse({'error': 'Date required'}, status=400)
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Get booked times for this date
    booked_times = Appointment.objects.filter(
        doctor=doctor,
        date=date
    ).exclude(status='cancelled').values_list('time', flat=True)
    
    # Return available slots
    all_slots = [choice[0] for choice in Appointment.TIME_SLOT_CHOICES]
    available_slots = [
        {'value': slot, 'display': dict(Appointment.TIME_SLOT_CHOICES)[slot]}
        for slot in all_slots if slot not in booked_times
    ]
    
    return JsonResponse({'available_slots': available_slots})


@login_required
def cancel_appointment(request, appointment_id):
    """Cancel an appointment."""
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    # Check permission
    if request.user.is_patient and appointment.patient.user != request.user:
        messages.error(request, 'You cannot cancel this appointment.')
        return redirect('patient_dashboard')
    
    if appointment.status == 'cancelled':
        messages.warning(request, 'This appointment is already cancelled.')
    elif appointment.status == 'completed':
        messages.error(request, 'Cannot cancel a completed appointment.')
    else:
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')

        # Send cancellation email
        send_appointment_notification(
            appointment,
            subject="Your appointment has been cancelled",
            intro_message="This is a confirmation that your appointment has been cancelled. Details are below."
        )

    if request.user.is_doctor:
        return redirect('doctor_dashboard')
    return redirect('patient_dashboard')


@login_required
def appointment_detail(request, appointment_id):
    """View appointment details."""
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    # Check permission
    user = request.user
    if not (user.is_superuser or 
            (user.is_doctor and appointment.doctor.user == user) or
            (user.is_patient and appointment.patient.user == user)):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    medical_records = appointment.medical_records.all()
    
    return render(request, 'appointments/appointment_detail.html', {
        'appointment': appointment,
        'medical_records': medical_records,
    })


# ============================================
# Medical Records Views
# ============================================

@login_required
def add_prescription(request, appointment_id):
    """Doctor adds prescription/medical record to an appointment."""
    if not request.user.is_doctor:
        messages.error(request, 'Only doctors can add prescriptions.')
        return redirect('dashboard')
    
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    # Verify this doctor owns the appointment
    if appointment.doctor.user != request.user:
        messages.error(request, 'Access denied.')
        return redirect('doctor_dashboard')
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.appointment = appointment
            record.save()
            
            # Mark appointment as completed
            appointment.status = 'completed'
            appointment.save()
            
            messages.success(request, 'Medical record added successfully.')
            return redirect('doctor_dashboard')
    else:
        form = MedicalRecordForm()
    
    return render(request, 'appointments/add_prescription.html', {
        'form': form,
        'appointment': appointment,
    })


@login_required
def medical_history(request):
    """Patient views their complete medical history."""
    if not request.user.is_patient:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    patient = request.user.patient_profile
    records = MedicalRecord.objects.filter(
        appointment__patient=patient
    ).select_related(
        'appointment__doctor__user',
        'appointment__doctor__department'
    ).order_by('-created_at')
    
    return render(request, 'appointments/medical_history.html', {
        'patient': patient,
        'records': records,
    })


@login_required
def complete_appointment(request, appointment_id):
    """Mark appointment as completed (quick action)."""
    if not request.user.is_doctor:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    if appointment.doctor.user != request.user:
        messages.error(request, 'Access denied.')
        return redirect('doctor_dashboard')
    
    appointment.status = 'completed'
    appointment.save()
    messages.success(request, 'Appointment marked as completed.')
    
    return redirect('doctor_dashboard')


@login_required  
def confirm_appointment(request, appointment_id):
    """Confirm a pending appointment."""
    if not request.user.is_doctor:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    if appointment.doctor.user != request.user:
        messages.error(request, 'Access denied.')
        return redirect('doctor_dashboard')
    
    appointment.status = 'confirmed'
    appointment.save()
    messages.success(request, 'Appointment confirmed.')

    # Send confirmation email
    send_appointment_notification(
        appointment,
        subject="Your appointment has been confirmed!",
        intro_message="A doctor has confirmed your appointment. Details are below."
    )
    return redirect('doctor_dashboard')


# ============================================
# Payment Views
# ============================================

@login_required
def payment_process(request, appointment_id):
    """Process payment for an appointment."""
    if not request.user.is_patient:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    # Check permission
    if appointment.patient.user != request.user:
        messages.error(request, 'Access denied.')
        return redirect('patient_dashboard')
    
    # Check if already paid - check both Payment model and Appointment field
    if appointment.payment_status == 'paid':
        messages.info(request, 'Bu randevu için ödeme zaten tamamlandı.')
        return redirect('patient_dashboard')
    
    # Check if Payment record exists (either card or cash was selected)
    try:
        if hasattr(appointment, 'payment') and appointment.payment:
            # Payment record exists - sync status and redirect
            appointment.payment_status = 'paid'
            appointment.save()
            messages.info(request, 'Bu randevu için ödeme işlemi zaten yapılmış.')
            return redirect('patient_dashboard')
    except:
        pass
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'card')
        
        # Create or update payment
        payment, created = Payment.objects.get_or_create(
            appointment=appointment,
            defaults={
                'amount': appointment.doctor.consultation_fee,
                'payment_method': payment_method,
                'transaction_id': f"PENDING-{uuid.uuid4().hex[:8].upper()}",
                'card_last_four': '0000',  # Default for cash payments
            }
        )
        
        if payment_method == 'card':
            # Demo payment processing
            card_number = request.POST.get('card_number', '').replace(' ', '')
            
            # Basic validation
            if len(card_number) >= 13:
                payment.status = 'completed'
                payment.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
                payment.card_last_four = card_number[-4:]
                payment.save()
                
                # Update appointment status
                appointment.payment_status = 'paid'
                appointment.save()
                
                messages.success(request, 'Payment successful!')
                return redirect('payment_success', appointment_id=appointment.id)
            else:
                messages.error(request, 'Invalid card number. Please try again.')
        else:
            # Cash payment - just mark as pending
            payment.payment_method = 'cash'
            payment.status = 'pending'
            payment.transaction_id = f"CASH-{uuid.uuid4().hex[:8].upper()}"
            payment.save()
            
            appointment.payment_status = 'pending'
            appointment.save()
            
            messages.success(request, 'Appointment confirmed! Please pay at the hospital reception.')
            return redirect('payment_success', appointment_id=appointment.id)
    
    return render(request, 'appointments/payment.html', {
        'appointment': appointment,
    })


@login_required
def payment_success(request, appointment_id):
    """Payment success page."""
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    # Check permission
    if request.user.is_patient and appointment.patient.user != request.user:
        messages.error(request, 'Access denied.')
        return redirect('patient_dashboard')
    
    payment = getattr(appointment, 'payment', None)
    
    return render(request, 'appointments/payment_success.html', {
        'appointment': appointment,
        'payment': payment,
    })


# ============================================
# Video Consultation Views
# ============================================

@login_required
def video_consultation(request, appointment_id):
    """Video consultation room."""
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    # Check permission - only doctor or patient of this appointment
    user = request.user
    if not (user.is_superuser or 
            (user.is_doctor and appointment.doctor.user == user) or
            (user.is_patient and appointment.patient.user == user)):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Check if video consultation
    if not appointment.is_video_consultation:
        messages.error(request, 'This is not a video consultation appointment.')
        return redirect('appointment_detail', appointment_id=appointment.id)
    
    return render(request, 'appointments/video_consultation.html', {
        'appointment': appointment,
    })

