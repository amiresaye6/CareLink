from django.urls import path

from dashboard.api.doctor.views import (
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
]
