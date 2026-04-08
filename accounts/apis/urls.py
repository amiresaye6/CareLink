from django.urls import include, path
from accounts import views
from .views import signup , profile
from rest_framework.authtoken.views import obtain_auth_token

#api/accounts/
urlpatterns = [
    path('signup/', signup, name='signup'),
    path('profile/', profile, name='profile'),
    path('login/', obtain_auth_token, name='login'),
    ]