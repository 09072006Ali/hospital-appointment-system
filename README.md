# 🏥 Hospital Appointment System

A web-based hospital appointment management system built with Django and MySQL. This system allows patients to book appointments with doctors, and doctors to manage their schedules and add prescriptions.

## 👥 Team Members

| Name | Role | Contribution |
|------|------|--------------|
| **Mert** | Developer | Initial setup, MySQL configuration, core functionality |
| *Team Member 2* | Developer | (To be added) |
| *Team Member 3* | Developer | (To be added) |

## ✨ Features

### For Patients
- 📅 Book appointments with doctors
- 👁️ View appointment details
- ❌ Cancel pending appointments
- 📋 View medical history and prescriptions
- 🏥 Browse departments and doctors

### For Doctors
- 📊 Dashboard with today's patients
- ✅ Mark appointments as completed
- 💊 Add prescriptions and diagnoses
- 📈 View upcoming appointments

### For Admins
- 👥 Manage all users (patients, doctors)
- 🏢 Manage departments
- 📊 View system statistics
- 📝 Manage all appointments

## 🛠️ Technologies Used

- **Backend:** Python 3, Django 5.x
- **Database:** MySQL (XAMPP)
- **Frontend:** HTML5, CSS3, Bootstrap 5
- **Icons:** Bootstrap Icons

## 📦 Installation

### Prerequisites
- Python 3.8+
- XAMPP (with MySQL)
- Git

### Steps

1. **Clone the repository**
```bash
git clone https://github.com/merturl4576/hospital-appointment-system.git
cd hospital-appointment-system
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Start XAMPP MySQL**
- Open XAMPP Control Panel
- Start Apache and MySQL

5. **Create database**
- Open phpMyAdmin (http://localhost/phpmyadmin)
- Create database named `hospital_db`

6. **Run migrations**
```bash
cd hospital_system
python manage.py migrate
```

7. **Load sample data (optional)**
```bash
python manage.py loaddata sample_data.json
```

8. **Run the server**
```bash
python manage.py runserver
```

9. **Open in browser**
- Navigate to: http://127.0.0.1:8000

## 🔑 Demo Accounts

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Doctor | dr_smith | doctor123 |
| Patient | patient1 | patient123 |

## 📁 Project Structure

```
hospital_system/
├── appointments/          # Main app
│   ├── models.py         # Database models
│   ├── views.py          # View functions
│   ├── urls.py           # URL routing
│   └── admin.py          # Admin configuration
├── hospital_project/      # Project settings
│   ├── settings.py       # Django settings
│   └── urls.py           # Main URL config
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   └── appointments/     # App templates
├── static/               # CSS, JS, images
└── manage.py             # Django CLI
```

## 🖼️ Screenshots

### Home Page
Modern landing page with department and doctor information.

### Patient Dashboard
Patients can view their appointments and medical history.

### Doctor Dashboard
Doctors can manage their appointments and add prescriptions.

## 🚀 Future Improvements

- [ ] Email notifications for appointments
- [ ] Online payment integration
- [ ] Video consultation feature
- [ ] Mobile app version
- [ ] Multi-language support

## 📄 License

This project is for educational purposes.

## 🤝 Contributing

This is a team project. Each team member should:

1. Create a new branch for your feature
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit
```bash
git add .
git commit -m "Add: your feature description"
```

3. Push to GitHub
```bash
git push origin feature/your-feature-name
```

4. Create a Pull Request on GitHub

---

**Made with ❤️ by the Team**
