from django.urls import path
from appointments.api.views import (
    doctor_appointment_details,
    book_appointment,
    doctor_patch_appointment,
    today_queue,
    appointment_list,
    update_appointment_status,
    request_reschedule,
    respond_to_reschedule,
    admin_audit_table,
    pending_reschedule_requests
)

urlpatterns = [
    path('doctor/<int:id>', doctor_appointment_details, name='appointments.api.doctor_appointment_details'),
    path('book/<int:doctor_id>', book_appointment, name='appointments.api.book_appointment'),
    path('<int:appointment_id>/', doctor_patch_appointment, name='appointments.api.doctor_patch_appointment'),
    path('reception/queue/', today_queue, name='appointments.api.today_queue'),
    path('reception/appointments/', appointment_list, name='appointments.api.appointment_list'),
    path('reception/appointment/<int:appointment_id>/status/', update_appointment_status, name='appointments.api.update_appointment_status'),
    path('appointment/<int:appointment_id>/reschedule/request/', request_reschedule, name='appointments.api.request_reschedule'),
    path('reschedule-request/<int:request_id>/respond/', respond_to_reschedule, name='appointments.api.respond_to_reschedule'),
    path('admin/audit-logs/', admin_audit_table, name='appointments.api.admin_audit_table'),
    path('reception/reschedule-requests/pending/', pending_reschedule_requests, name='appointments.api.pending_reschedules'),
]