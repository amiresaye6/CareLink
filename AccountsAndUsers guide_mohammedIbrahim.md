Mohammed Ibrahim
I was responsible for accounts , permissions and profiles for all user in both backend and frontend.
I made apis for these functionalities:
A)Apis for users to create and treat with their accounts and profiles
1- signup with different roles
2- signIn
3- logout
4- show their profile data
5- edit their profile data
6- change password
7- reset password
B)Apis to help some users depending on their role
8- lsit all users (help admin to fetch all users)
9- list only active users (help admin to fetch active users to inactive anyone of them)
10- list only inactive users (help admin to active new users)
11- list active doctors (help patients)
11- list active specialist doctors (help patients)
12 – list all active  patients (help admin to fetch all patiens)
13 – list all active receptionists (help admin to fetch all receptionists)


Imports:
from rest_framework.permissions import BasePermission
from rest_framework import serializers
from django.contrib.auth.models import Group
from rest_framework.decorators import api_view ,permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail

Backend endpoints with examples:
1- signUp  http://127.0.0.1:8000/api/accounts/signup/     (POST)
body depends on role

sign up as doctor : 
{
“username” : “Essam”, 	//unique
“email” : “Essam @gmail.com” , //unique
“password” : “pass123456789”,	//min length 8 chars
“first_name”:” Essam”,		//max length 150 chars
“last_name” : “ibrahim”,		//max length 150 chars
“role” : “DOCTOR”,		//choices {“PATIENT”,”DOCTOR”,”RECEPTIONIST”,”ADMIN”}, DOCTOR for now
“speciality” : “CARDIOLOGY”,	//choices{“CARDIOLOGY”,”DERMATOLOGY”,”NEUROLOGY”,”PEDIATRICS”,”ORTHOPEDICS”,”GENERAL”}
“session_duration” : 15,	//choices{15,30}
“buffer_time” : 3,		//integerfield
“profile_picture”: image,	//imagefield
“session_price”:300	//integerfield
}

signup as patient :
{
“username” : “moahmed2”, 	//unique
“email” : “Mohamed2@gmail.com” , //unique
“password” : “pass123456789”,	//min length 8 chars
“first_name”:”moahmed”,		//max length 150 chars
“last_name” : “ibrahim”,		//max length 150 chars
“role” : “PATIENT”,			//choices {“PATIENT”,”DOCTOR”,”RECEPTIONIST”,”ADMIN”}, PATIENT for now
 "date_of_birth": "1998-05-21", //Date
“phone_number”: “01234567890”,
“medical_history”: “Lumbar desk L2-L3”
}

sign up as receptionist : 
{
“username” : “ahmed”, 	//unique
“email” : “ahmed @gmail.com” , 	//unique
“password” : “pass123456789”,	//min length 8 chars
“first_name”:”ahmed”,		//max length 150 chars
“last_name” : “osama”,		//max length 150 chars
“role” : “RECEPTIONIST”,	//choices {“PATIENT”,”DOCTOR”,”RECEPTIONIST”,”ADMIN”}, RECEPTIONIST for now
“doctor_id”, 		//must be real doctor id belong to doctor group
}

sign up as admin :
{
“username” : “moahmed6269”, 	//unique
“email” : “Mohamed6269@gmail.com” , 	//unique
“password” : “pass123456789”,	//min length 8 chars
“first_name”:”moahmed”,		//max length 150 chars
“last_name” : “ibrahim”,		//max length 150 chars
“role” : “ADMIN”,		//choices {“PATIENT”,”DOCTOR”,”RECEPTIONIST”,”ADMIN”}, ADMIN for now
}

after creation any user , you will not be able to login by the account until it is activated by admin or at least from the database 

2- Login  
POST
http://localhost:8000/api/accounts/login/
{"username": " moahmed6269",
"password": " pass123456789”
}

3- Logout 
POST
http://127.0.0.1:8000/api/accounts/logout/
NO BODY (you should only be authenticated,and your token will be deleted)

4- get profile data
GET
http://127.0.0.1:8000/api/accounts/profile/
NO BODY (you should only be authenticated)

5- edit profile data
PATCH
http://127.0.0.1:8000/api/accounts/profile/
{
“first_name”:”moahmed18”, //OR any other field
}

6- list all users
GET
http://127.0.0.1:8000/api/accounts/users/
NO BODY (you should only be authenticated) restricted to role ADMIN

7- list active users
GET
http://127.0.0.1:8000/api/accounts/activeUsers/
NO BODY (you should only be authenticated) restricted to role ADMIN

8- list inactive users
GET
http://127.0.0.1:1234/api/accounts/inactiveUsers/
NO BODY (you should only be authenticated) restricted to role ADMIN

9- list active doctors
GET 
http://127.0.0.1:8000/api/accounts/activedoctors/
NO BODY (you should only be authenticated)

10-list active specialist doctors
GET
http://127.0.0.1:8000/api/accounts/listspicialists?speciality=CARDIOLOGY   //or any other speciality that determined before
NO BODY (you should only be authenticated)

11- list active patients
GET
http://127.0.0.1:8000/api/accounts/patients/
NO BODY (you should only be authenticated) restricted to role ADMIN

12-list active receptionists
GET
http://127.0.0.1:8000/api/accounts/receptionists/
NO BODY (you should only be authenticated) restricted to role ADMIN

13- change password
POST
http://localhost:8000/api/accounts/change-password/
{
"oldPassword":"Mohammed8",
"newPassword":"Mohammed888",
"repeatNewPssword":"Mohammed888"
}

14-reset password
POST  http://localhost:8000/api/accounts/reset-password/
{"email":mohamadelazzazy@gmail.com //it will send you verification mail}


