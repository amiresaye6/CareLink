from django.contrib import admin
from .models import WeeklySchedule, ScheduleException, Appointment, AppointmentAuditTrail

admin.site.register(WeeklySchedule)
admin.site.register(ScheduleException)
admin.site.register(Appointment)
admin.site.register(AppointmentAuditTrail)