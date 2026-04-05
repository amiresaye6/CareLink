from django.db import models
from accounts.models import User, DoctorProfile, PatientProfile

class WeeklySchedule(models.Model):
    DAY_CHOICES = (
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    )
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='weekly_schedules')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

class ScheduleException(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='schedule_exceptions')
    date = models.DateField()
    is_day_off = models.BooleanField(default=False)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('REQUESTED', 'Requested'), ('CONFIRMED', 'Confirmed'),
        ('CHECKED_IN', 'Checked In'), ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'), ('NO_SHOW', 'No Show'),
    )
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='appointments')
    scheduled_datetime = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    check_in_time = models.DateTimeField(null=True, blank=True)
    is_telemedicine = models.BooleanField(default=False)
    meeting_link = models.URLField(max_length=255, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['doctor', 'scheduled_datetime'], name='unique_doctor_slot')
        ]

class AppointmentAuditTrail(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='audit_trails')
    old_datetime = models.DateTimeField()
    new_datetime = models.DateTimeField()
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    reason = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)