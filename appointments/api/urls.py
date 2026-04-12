from django.urls import path


from appointments.api.views import (
    doctor_appointment_details,
    book_appointment,
    doctor_patch_appointment,
    today_queue,
    appointment_list,
    update_appointment_status,
)

urlpatterns = [
    path('doctor/<int:id>', doctor_appointment_details, name='appointments.api.doctor_appointment_details'),
    path('book/<int:doctor_id>', book_appointment, name='appointments.api.book_appointment'),
    path('<int:appointment_id>/', doctor_patch_appointment, name='appointments.api.doctor_patch_appointment'),
    path('reception/queue/', today_queue, name='appointments.api.today_queue'),
    path('reception/appointments/', appointment_list, name='appointments.api.appointment_list'),
    path('reception/appointment/<int:appointment_id>/status/', update_appointment_status, name='appointments.api.update_appointment_status'),
]