from django.urls import path
from . import views

urlpatterns = [
    path('api/consultations/', views.consultation_list, name='api.consultation.list'),
    path('api/consultations/<int:id>', views.consultation_detail, name='api.consultation.detail'),

    path('api/prescriptions/', views.prescription_list, name='api.prescription.list'),
    path('api/prescriptions/<int:id>', views.prescription_detail, name='api.prescription.detail'),

    path('api/tests/', views.test_list, name='api.test.list'),
    path('api/tests/<int:id>', views.test_detail, name='api.test.detail'),
]
 