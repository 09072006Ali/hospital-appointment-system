"""
Hospital Appointment System - Database Population Script

This Django management command populates the database with sample data
including departments, doctors, patients, and appointments.

Usage: python manage.py populate_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from appointments.models import Department, Doctor, Patient, Appointment, MedicalRecord
from datetime import date, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Populates the database with sample data for Hospital Appointment System'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting database population...'))
        
        # Create Admin User
        self.create_admin()
        
        # Create Departments
        departments = self.create_departments()
        
        # Create Doctors
        doctors = self.create_doctors(departments)
        
        # Create Patients
        patients = self.create_patients()
        
        # Create Appointments
        self.create_appointments(doctors, patients)
        
        self.stdout.write(self.style.SUCCESS('Database populated successfully!'))
        self.stdout.write(self.style.SUCCESS('\n=== Login Credentials ==='))
        self.stdout.write('Admin: admin / admin123')
        self.stdout.write('Doctor: dr_smith / doctor123')
        self.stdout.write('Patient: patient1 / patient123')

    def create_admin(self):
        """Create admin superuser."""
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@medicare.com',
                password='admin123',
                first_name='Hospital',
                last_name='Admin'
            )
            self.stdout.write(f'  ✓ Created admin user: {admin.username}')
        else:
            self.stdout.write('  - Admin user already exists')

    def create_departments(self):
        """Create hospital departments."""
        departments_data = [
            {
                'name': 'Cardiology',
                'description': 'Specialized in heart and cardiovascular system care. Our cardiologists diagnose and treat conditions like coronary artery disease, heart rhythm disorders, and heart failure.',
                'icon': 'heart-pulse'
            },
            {
                'name': 'Neurology',
                'description': 'Expert care for brain, spinal cord, and nervous system disorders. Treating conditions including epilepsy, stroke, Parkinson\'s disease, and migraines.',
                'icon': 'lightning'
            },
            {
                'name': 'Pediatrics',
                'description': 'Comprehensive healthcare for infants, children, and adolescents. Our pediatricians provide preventive care, treat illnesses, and monitor development.',
                'icon': 'emoji-smile'
            },
            {
                'name': 'Orthopedics',
                'description': 'Treatment for musculoskeletal system including bones, joints, ligaments, and muscles. Specializing in fractures, sports injuries, and joint replacements.',
                'icon': 'bandaid'
            },
            {
                'name': 'Dermatology',
                'description': 'Complete skin, hair, and nail care. Treating conditions like acne, eczema, psoriasis, skin cancer, and cosmetic dermatology procedures.',
                'icon': 'moisture'
            },
        ]
        
        departments = []
        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                name=dept_data['name'],
                defaults={
                    'description': dept_data['description'],
                    'icon': dept_data['icon']
                }
            )
            departments.append(dept)
            status = '✓ Created' if created else '- Exists'
            self.stdout.write(f'  {status} department: {dept.name}')
        
        return departments

    def create_doctors(self, departments):
        """Create doctor users and profiles."""
        doctors_data = [
            # Cardiology (2 doctors)
            {'first': 'John', 'last': 'Smith', 'spec': 'Interventional Cardiology', 'dept': 0, 'exp': 15, 'fee': 150},
            {'first': 'Sarah', 'last': 'Johnson', 'spec': 'Heart Failure Specialist', 'dept': 0, 'exp': 12, 'fee': 140},
            # Neurology (2 doctors)
            {'first': 'Michael', 'last': 'Williams', 'spec': 'Stroke & Vascular Neurology', 'dept': 1, 'exp': 18, 'fee': 160},
            {'first': 'Emily', 'last': 'Brown', 'spec': 'Pediatric Neurology', 'dept': 1, 'exp': 10, 'fee': 130},
            # Pediatrics (2 doctors)
            {'first': 'David', 'last': 'Davis', 'spec': 'General Pediatrics', 'dept': 2, 'exp': 8, 'fee': 100},
            {'first': 'Jennifer', 'last': 'Miller', 'spec': 'Neonatal Care', 'dept': 2, 'exp': 14, 'fee': 120},
            # Orthopedics (2 doctors)
            {'first': 'Robert', 'last': 'Wilson', 'spec': 'Sports Medicine', 'dept': 3, 'exp': 20, 'fee': 170},
            {'first': 'Amanda', 'last': 'Taylor', 'spec': 'Joint Replacement', 'dept': 3, 'exp': 11, 'fee': 155},
            # Dermatology (2 doctors)
            {'first': 'James', 'last': 'Anderson', 'spec': 'Cosmetic Dermatology', 'dept': 4, 'exp': 9, 'fee': 125},
            {'first': 'Lisa', 'last': 'Thomas', 'spec': 'Pediatric Dermatology', 'dept': 4, 'exp': 7, 'fee': 110},
        ]
        
        doctors = []
        for i, doc_data in enumerate(doctors_data):
            username = f"dr_{doc_data['last'].lower()}"
            
            # Create User
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f"{username}@medicare.com",
                    'first_name': doc_data['first'],
                    'last_name': doc_data['last'],
                    'is_doctor': True
                }
            )
            if user_created:
                user.set_password('doctor123')
                user.save()
            
            # Create Doctor Profile
            doctor, doc_created = Doctor.objects.get_or_create(
                user=user,
                defaults={
                    'department': departments[doc_data['dept']],
                    'specialization': doc_data['spec'],
                    'experience_years': doc_data['exp'],
                    'consultation_fee': doc_data['fee'],
                    'bio': f"Dr. {doc_data['first']} {doc_data['last']} is a highly skilled {doc_data['spec']} specialist with {doc_data['exp']} years of experience.",
                    'is_available': True
                }
            )
            doctors.append(doctor)
            status = '✓ Created' if doc_created else '- Exists'
            self.stdout.write(f'  {status} doctor: Dr. {doc_data["first"]} {doc_data["last"]}')
        
        return doctors

    def create_patients(self):
        """Create patient users and profiles."""
        patients_data = [
            {'first': 'Alice', 'last': 'Cooper', 'dob': date(1990, 5, 15), 'blood': 'A+'},
            {'first': 'Bob', 'last': 'Martin', 'dob': date(1985, 8, 22), 'blood': 'B+'},
            {'first': 'Carol', 'last': 'White', 'dob': date(1992, 3, 10), 'blood': 'O+'},
            {'first': 'Daniel', 'last': 'Harris', 'dob': date(1978, 11, 5), 'blood': 'AB+'},
            {'first': 'Eva', 'last': 'Clark', 'dob': date(1995, 7, 28), 'blood': 'A-'},
        ]
        
        patients = []
        for i, pat_data in enumerate(patients_data):
            username = f"patient{i+1}"
            
            # Create User
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f"{pat_data['first'].lower()}.{pat_data['last'].lower()}@email.com",
                    'first_name': pat_data['first'],
                    'last_name': pat_data['last'],
                    'is_patient': True
                }
            )
            if user_created:
                user.set_password('patient123')
                user.save()
            
            # Create Patient Profile
            patient, pat_created = Patient.objects.get_or_create(
                user=user,
                defaults={
                    'date_of_birth': pat_data['dob'],
                    'blood_type': pat_data['blood'],
                    'address': f"{random.randint(100, 999)} Main Street, Medical City",
                    'emergency_contact': f"{pat_data['first']}'s Emergency Contact",
                    'emergency_phone': f"+1 555-{random.randint(1000, 9999)}"
                }
            )
            patients.append(patient)
            status = '✓ Created' if pat_created else '- Exists'
            self.stdout.write(f'  {status} patient: {pat_data["first"]} {pat_data["last"]}')
        
        return patients

    def create_appointments(self, doctors, patients):
        """Create sample appointments."""
        time_slots = ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']
        statuses = ['pending', 'confirmed', 'completed']
        descriptions = [
            'Regular checkup',
            'Follow-up consultation',
            'New symptoms evaluation',
            'Annual health screening',
            'Specialist referral',
            'Post-treatment review',
        ]
        
        today = date.today()
        appointments_created = 0
        
        # Past appointments (completed)
        for i in range(5):
            past_date = today - timedelta(days=random.randint(1, 30))
            doctor = random.choice(doctors)
            patient = random.choice(patients)
            time = random.choice(time_slots)
            
            apt, created = Appointment.objects.get_or_create(
                doctor=doctor,
                date=past_date,
                time=time,
                defaults={
                    'patient': patient,
                    'status': 'completed',
                    'description': random.choice(descriptions)
                }
            )
            if created:
                appointments_created += 1
                # Add medical record for completed appointments
                MedicalRecord.objects.create(
                    appointment=apt,
                    diagnosis='Patient examined. ' + random.choice([
                        'Mild condition, prescribed medication.',
                        'Routine checkup completed, all normal.',
                        'Minor issue detected, treatment provided.',
                        'Follow-up recommended in 2 weeks.',
                    ]),
                    symptoms='Patient reported: ' + random.choice([
                        'mild headache and fatigue',
                        'joint pain and stiffness',
                        'general wellness check',
                        'seasonal allergies',
                    ]),
                    medicines=random.choice([
                        'Paracetamol 500mg\nVitamin D 1000IU',
                        'Ibuprofen 400mg\nOmeprazole 20mg',
                        'Multivitamins daily\nOmega-3 supplements',
                        'Antihistamine tablets\nNasal spray',
                    ]),
                    instructions='Take medications as prescribed. Rest well. Return if symptoms persist.'
                )
        
        # Today's appointments
        for i in range(3):
            doctor = random.choice(doctors)
            patient = random.choice(patients)
            time = time_slots[i % len(time_slots)]
            
            apt, created = Appointment.objects.get_or_create(
                doctor=doctor,
                date=today,
                time=time,
                defaults={
                    'patient': patient,
                    'status': random.choice(['pending', 'confirmed']),
                    'description': random.choice(descriptions)
                }
            )
            if created:
                appointments_created += 1
        
        # Future appointments
        for i in range(7):
            future_date = today + timedelta(days=random.randint(1, 14))
            doctor = random.choice(doctors)
            patient = random.choice(patients)
            time = random.choice(time_slots)
            
            apt, created = Appointment.objects.get_or_create(
                doctor=doctor,
                date=future_date,
                time=time,
                defaults={
                    'patient': patient,
                    'status': random.choice(['pending', 'confirmed']),
                    'description': random.choice(descriptions)
                }
            )
            if created:
                appointments_created += 1
        
        self.stdout.write(f'  ✓ Created {appointments_created} appointments')
