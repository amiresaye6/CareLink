from django.urls import path
from . import views

urlpatterns = [
    path('doctor/queue/', views.doctor_queue, name='doctor.queue'),
    path('doctor/consultation/<int:appointment_id>/save/', views.save_consultation, name='doctor.consultation.save'),
    path('doctor/consultation/<int:appointment_id>/edit/', views.edit_consultation, name='doctor.consultation.edit'),
    path('doctor/consultation/<int:appointment_id>/', views.get_consultation, name='doctor.consultation'),
    path('patient/history/<int:appointment_id>/', views.patient_consultation_summary, name='patient.summary'),
    path('doctor/prescriptions/', views.doctor_prescriptions, name='doctor.prescriptions'),
    path('doctor/tests/', views.doctor_tests, name='doctor.tests'),
    
]
