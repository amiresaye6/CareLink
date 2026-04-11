from django.urls import path

from appointments.api.views import doctor_appointment_details, book_appointment, doctor_patch_appointment



urlpatterns = [
    path('doctor/<int:id>', doctor_appointment_details, name='appointments.api.doctor_appointment_details'),
    path('book/<int:doctor_id>', book_appointment, name='appointments.api.book_appointment'),
    path('<int:appointment_id>/', doctor_patch_appointment, name='appointments.api.doctor_patch_appointment'),
]