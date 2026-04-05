from django.db import models
from appointments.models import Appointment

class ConsultationRecord(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='consultation')
    diagnosis = models.CharField(max_length=255)
    clinical_notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class PrescriptionItem(models.Model):
    consultation = models.ForeignKey(ConsultationRecord, on_delete=models.CASCADE, related_name='prescriptions')
    drug_name = models.CharField(max_length=150)
    dose = models.CharField(max_length=100)
    duration_days = models.IntegerField()

class TestRequest(models.Model):
    consultation = models.ForeignKey(ConsultationRecord, on_delete=models.CASCADE, related_name='tests')
    test_name = models.CharField(max_length=150)