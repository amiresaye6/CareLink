from django.contrib import admin
from .models import ConsultationRecord, PrescriptionItem, TestRequest

admin.site.register(ConsultationRecord)
admin.site.register(PrescriptionItem)
admin.site.register(TestRequest)