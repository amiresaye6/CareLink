from django.urls import path

from dashboard.api.doctor.views import (
    doctor_dashboard_stats,
    doctor_appointments_over_time,
    doctor_appointment_status_breakdown,
    doctor_queue_today,
    get_doctor_by_id,
    update_doctor_by_id,
    get_logged_in_doctor,
    update_logged_in_doctor,
    get_logged_in_weekly_schedules,
    create_logged_in_weekly_schedule,
    update_logged_in_weekly_schedule,
    delete_logged_in_weekly_schedule,
    bulk_set_logged_in_weekly_schedules,
    bulk_delete_logged_in_weekly_schedules,
    get_logged_in_schedule_exceptions,
    create_logged_in_schedule_exception,
    update_logged_in_schedule_exception,
    delete_logged_in_schedule_exception,
    get_logged_in_doctor_patients,
    get_logged_in_doctor_patient_detail,
    get_logged_in_doctor_appointments,
    get_logged_in_doctor_appointment_detail,
    update_logged_in_doctor_appointment_status,
    delete_logged_in_doctor_appointment,
)


urlpatterns = [
    path('me', get_logged_in_doctor, name='dashboard.api.doctor.get_logged_in_doctor'),
    path('me/update', update_logged_in_doctor, name='dashboard.api.doctor.update_logged_in_doctor'),
    path('<int:id>', get_doctor_by_id, name='dashboard.api.doctor.get_doctor_by_id'),
    path('update/<int:id>', update_doctor_by_id, name='dashboard.api.doctor.update_doctor_by_id'),

    path('weekly-schedules/bulk', bulk_set_logged_in_weekly_schedules, name='dashboard.api.doctor.bulk_set_logged_in_weekly_schedules'),
    path('weekly-schedules/bulk-delete', bulk_delete_logged_in_weekly_schedules, name='dashboard.api.doctor.bulk_delete_logged_in_weekly_schedules'),
    path('weekly-schedules', get_logged_in_weekly_schedules, name='dashboard.api.doctor.get_logged_in_weekly_schedules'),
    path('weekly-schedules/create', create_logged_in_weekly_schedule, name='dashboard.api.doctor.create_logged_in_weekly_schedule'),
    path('weekly-schedules/update/<int:id>', update_logged_in_weekly_schedule, name='dashboard.api.doctor.update_logged_in_weekly_schedule'),
    path('weekly-schedules/delete/<int:id>', delete_logged_in_weekly_schedule, name='dashboard.api.doctor.delete_logged_in_weekly_schedule'),


    path('schedule-exceptions', get_logged_in_schedule_exceptions, name='dashboard.api.doctor.get_logged_in_schedule_exceptions'),
    path('schedule-exceptions/create', create_logged_in_schedule_exception, name='dashboard.api.doctor.create_logged_in_schedule_exception'),
    path('schedule-exceptions/update/<int:id>', update_logged_in_schedule_exception, name='dashboard.api.doctor.update_logged_in_schedule_exception'),
    path('schedule-exceptions/delete/<int:id>', delete_logged_in_schedule_exception, name='dashboard.api.doctor.delete_logged_in_schedule_exception'),


    path('patients', get_logged_in_doctor_patients, name='dashboard.api.doctor.get_logged_in_doctor_patients'),
    path('patients/<int:patient_id>', get_logged_in_doctor_patient_detail, name='dashboard.api.doctor.get_logged_in_doctor_patient_detail'),




    path('appointments', get_logged_in_doctor_appointments, name='dashboard.api.doctor.get_logged_in_doctor_appointments'),
    path('appointments/<int:appointment_id>', get_logged_in_doctor_appointment_detail, name='dashboard.api.doctor.get_logged_in_doctor_appointment_detail'),
    path(
        'appointments/<int:appointment_id>/status',
        update_logged_in_doctor_appointment_status,
        name='dashboard.api.doctor.update_logged_in_doctor_appointment_status',
    ),
    path(
        'appointments/delete/<int:appointment_id>',
        delete_logged_in_doctor_appointment,
        name='dashboard.api.doctor.delete_logged_in_doctor_appointment',
    ),




    path('stats/', doctor_dashboard_stats, name='dashboard.api.doctor.doctor_dashboard_stats'),
    path('appointments-over-time/', doctor_appointments_over_time, name='dashboard.api.doctor.doctor_appointments_over_time'),
    path('status-breakdown/', doctor_appointment_status_breakdown, name='dashboard.api.doctor.doctor_appointment_status_breakdown'),
    path('queue-today/', doctor_queue_today, name='dashboard.api.doctor.doctor_queue_today'),
]
