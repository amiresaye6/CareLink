from django.urls import  path
from accounts import views
from .views import changePassword, list_ActiveReceptionists,list_ActivePatients, list_ActiveDoctorsBySpeciality,list_ActiveDoctors, list_InActiveUsers,list_ActiveUsers, signup , profile , logout , list_users
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path('signup/', signup, name='signup'),
    path('profile/', profile, name='profile'),
    path('login/', obtain_auth_token, name='login'),
    path('logout/', logout, name='logout'),
    path('users/', list_users, name='users'),
    path('activeUsers/',list_ActiveUsers, name='activeUsers'),
    path('inactiveUsers/', list_InActiveUsers, name='InactiveUsers'),
    path('activedoctors/', list_ActiveDoctors,name='activedoctors'),
    path('listspicialists/' , list_ActiveDoctorsBySpeciality , name="listSpicialists"),
    path('patients/',list_ActivePatients, name="listpatiens"),
    path('receptionists/',list_ActiveReceptionists, name="listreceptionists"),
    path('change-password/', changePassword, name='change_password'),
    ]