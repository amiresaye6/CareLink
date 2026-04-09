from django.contrib import admin
from .models import ReceptionistProfile, User, PatientProfile, DoctorProfile

admin.site.register(User)
admin.site.register(PatientProfile)
admin.site.register(DoctorProfile)
admin.site.register(ReceptionistProfile)