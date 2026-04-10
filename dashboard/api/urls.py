from django.urls import path, include

urlpatterns = [
    path('admin/', include('dashboard.api.admin.urls')),
    path('doctor/', include('dashboard.api.doctor.urls')),
]
