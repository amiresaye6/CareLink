from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('PATIENT', 'Patient'),
        ('DOCTOR', 'Doctor'),
        ('RECEPTIONIST', 'Receptionist'),
        ('ADMIN', 'Admin'),
        ('TO_BE_ADMIN', 'To Be Admin')
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    medical_history = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Patient: {self.user.username}"

class DoctorProfile(models.Model):
    SESSION_CHOICES = ((15, '15 Minutes'), (30, '30 Minutes'))
    SPECIALTY_CHOICES = (
        ('CARDIOLOGY', 'Cardiology'),
        ('DERMATOLOGY', 'Dermatology'),
        ('NEUROLOGY', 'Neurology'),
        ('PEDIATRICS', 'Pediatrics'),
        ('ORTHOPEDICS', 'Orthopedics'),
        ('GENERAL', 'General Practice')
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty = models.CharField(max_length=100, choices=SPECIALTY_CHOICES)
    session_duration = models.IntegerField(choices=SESSION_CHOICES, default=30)
    buffer_time = models.IntegerField(default=5)

    def __str__(self):
        return f"Dr. {self.user.username} - {self.specialty}"


class ReceptionistProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='receptionist_profile')
    doctor = models.OneToOneField(DoctorProfile, on_delete=models.CASCADE, related_name='receptionist_profile')

    def __str__(self):
        return f"Receptionist: {self.user.username} for Dr. {self.doctor.user.username}"
