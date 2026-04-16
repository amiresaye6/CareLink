from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from .analytics_views import AnalyticsViewSet
from .reports_views import ReportsViewset
from .doctro_views import DoctorListViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='admin-user')


doc_router = DefaultRouter()
router.register(r'doctors', DoctorListViewSet, basename='doctor-list')

analytics_router = DefaultRouter()
analytics_router.register(r'analytics', AnalyticsViewSet, basename='admin-analytics')

reports_router = DefaultRouter()
reports_router.register(r'reports', ReportsViewset , basename='admin-reports')


urlpatterns = [
    path('', include(router.urls)),
    path('', include(analytics_router.urls)),
    path('', include(reports_router.urls)),
    path('', include(doc_router.urls)),
]
