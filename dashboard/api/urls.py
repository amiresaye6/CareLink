from django.urls import path, include



urlpatterns = [
    path('doctor/', include('dashboard.api.doctor.urls')),
]

