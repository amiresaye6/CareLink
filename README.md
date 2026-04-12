# CareLink - Clinic Appointment System: Setup Guide

This guide will take you from a fresh folder to a fully functioning development environment with a seeded MySQL database. Follow these steps carefully to ensure the **Multiple App Architecture** is correctly initialized.

---

### 1. Environment & Dependencies
First, we need to isolate our Python environment and install the engine that runs CareLink.

**Create and Activate Virtual Environment:**
```

powershell

# Windows PowerShell

python -m venv care_link_venv
.\care_link_venv\Scripts\Activate.ps1

# Git Bash / Mac / Linux

python -m venv care_link_venv
source care_link_venv/Scripts/activate
```

**Install Core Libraries:**
```bash
pip install -r Dependencies.txt
pip install django-cors-headers
```

---

### 2. Database Configuration

Before running any Django commands, we must prepare the MySQL backend.

1.  **Create the Schema:** Open MySQL Workbench and run:
    ```sql
    CREATE DATABASE care_link_db;
    ```
2.  **Verify Settings:** Open `carelink_project/.env` and ensure the `DATABASES` block matches your local credentials:
    ```python
    'DB_USER': 'yourUserName_here',
    'DB_PASSWORD': 'your_password_here',
    ```

---

### 3. The "First Run" Migrations

Since we are using a **Custom User Model** (`accounts.User`), you must apply migrations before creating any users or seeding data.

```bash

# 1. Generate the blueprints for all 4 apps (accounts, appointments, medical, dashboard)

python manage.py makemigrations

# 2. Build the physical tables in care_link_db

python manage.py migrate
```

---

### 4. Seeding the Database (The Team Shortcut)

To save the team from manually adding doctors and patients, run our custom seed script. This populates the clinic with realistic data, schedules, and appointments.

```bash
python manage.py seed
```

> **💡 Note for the Team:** > You can now log into the system using any of these accounts:
>
> - **Usernames:** `donia_doc`, `mohamed_doc`, `hager_rec`, `amir_maula`
> - **Password:** `password123`

---

### 5. Accessing the Backend (Superuser)

If you want to access the default Django Admin panel (`/admin`) to view the raw database tables, create your own master account:

```bash
python manage.py createsuperuser
```

---

### 6. Launching the System

Fire up the development server to verify everything is working.

```bash
python manage.py runserver 1234
```

- **Public Site:** `http://127.0.0.1:1234/`
- **Admin Dashboard:** `http://127.0.0.1:1234/admin/`

---



### 📂 App Responsibility Matrix

- **`accounts/`**: Authentication, Custom User, and Doctor/Patient Profiles.
- **`appointments/`**: Availability, Slot Booking, and the Receptionist Queue.
- **`medical/`**: EMR records, Consultation notes, and Prescriptions.
- **`dashboard/`**: (Your Work) Custom Analytics, Statistics, and Management Overviews.