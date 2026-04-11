from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from .analytics_views import AnalyticsViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='admin-user')

analytics_router = DefaultRouter()
analytics_router.register(r'analytics', AnalyticsViewSet, basename='admin-analytics')


urlpatterns = [
    path('', include(router.urls)),
    path('', include(analytics_router.urls)),
]
