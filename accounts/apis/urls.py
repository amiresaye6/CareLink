from django.urls import  path
from accounts import views
from .views import signup , profile , logout
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path('signup/', signup, name='signup'),
    path('profile/', profile, name='profile'),
    path('login/', obtain_auth_token, name='login'),
    path('logout/', logout, name='logout'),
    ]