# CareLink - Clinic Appointment System

## 🚀 Getting Started (Team Setup Guide)

Follow these steps to get the Django project running on your local machine.

### 1. Clone the Repository
```bash
git clone https://github.com/amiresaye6/CareLink
cd CareLink
```

### 2. Set Up the Virtual Environment
*⚠️ Note: Ensure you use the correct activation command for your specific terminal to avoid errors.*

**If using Windows PowerShell:**
```powershell
python -m venv care_link_venv
.\care_link_venv\Scripts\Activate.ps1
```

**If using Git Bash (Windows):**
```bash
python -m venv care_link_venv
source care_link_venv/Scripts/activate
```

**If using Mac / Linux:**
```bash
python3 -m venv care_link_venv
source care_link_venv/bin/activate
```

### 3. Install Dependencies
Once your environment is active (you should see `(care_link_venv)` in your terminal prompt), install the required packages:
```bash
pip install django djangorestframework mysqlclient
```
*(Note: If we add more packages later, we will use `pip install -r requirements.txt`)*

### 4. Database Configuration
1. Open MySQL Workbench (or your preferred SQL client).
2. Create the empty database:
```sql
CREATE DATABASE care_link_db;
```
3. Check `settings.py` and ensure the `DATABASES` configuration matches your local MySQL `USER` and `PASSWORD`.

### 5. Run Migrations & Create Admin
Let Django build the tables mapping to our Custom User Model and architecture:
```bash
python manage.py makemigrations
python manage.py migrate
```
Create your local admin account so you can log into the backend:
```bash
python manage.py createsuperuser
```

### 6. Run the Server
Start the development server:
```bash
python manage.py runserver
```
The app should now be running at `http://127.0.0.1:8000/`. Happy coding!