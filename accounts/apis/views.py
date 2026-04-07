from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from accounts.models import User
from django.contrib.auth import hashers
from rest_framework import status
from .serializers import SignUpAdminSerializer, SignUpDoctorSerializer , SignUpPatientSerializer, SignUpReceptionistSerializer, SignUpUserSerializer

@api_view(['POST'])
def signup(request):
    data = request.data
    role = data.get('role')
    email = data.get('email')
    if User.objects.filter(email=email).exists():
        return Response({'message': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = None
    if role == 'DOCTOR':
        serializer = SignUpDoctorSerializer(data=data)
    elif role == 'PATIENT':
        serializer = SignUpPatientSerializer(data=data)
    elif role == 'RECEPTIONIST':
        serializer = SignUpReceptionistSerializer(data=data)
    elif role == 'ADMIN':
        serializer = SignUpAdminSerializer(data=data)  
    else:
        return Response({'message': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)
    
    if(serializer is None):
        return Response({'message': 'Serializer not found for the given role'}, status=status.HTTP_400_BAD_REQUEST)
    if serializer.is_valid():
        CreatedUser = serializer.save()
        return Response({'message': 'User created successfully',"user":serializer.data}, status=status.HTTP_201_CREATED)
    return Response({'errors': serializer.errors , "message": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)
  

