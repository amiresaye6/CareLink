from dashboard.api.doctor.views import (
    get_doctor_by_id,
    update_doctor_by_id,
    get_logged_in_doctor,
    update_logged_in_doctor,
)
from django.urls import path


urlpatterns = [
    path('me', get_logged_in_doctor, name='dashboard.api.doctor.get_logged_in_doctor'),
    path('me/update', update_logged_in_doctor, name='dashboard.api.doctor.update_logged_in_doctor'),
    path('<int:id>', get_doctor_by_id, name='dashboard.api.doctor.get_doctor_by_id'),
    path('update/<int:id>', update_doctor_by_id, name='dashboard.api.doctor.update_doctor_by_id'),


]

