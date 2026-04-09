from dashboard.api.doctor.views import (
    get_doctor_by_id,
    update_doctor_by_id,
)
from django.urls import path


urlpatterns = [
    path('<int:id>', get_doctor_by_id, name='dashboard.api.doctor.get_doctor_by_id'),
    path('update/<int:id>', update_doctor_by_id, name='dashboard.api.doctor.update_doctor_by_id'),


]

