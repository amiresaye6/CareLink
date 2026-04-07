from django.urls import include, path
from accounts import views
from .views import signup

urlpatterns = [
    path('signup/', signup, name='signup'),
]