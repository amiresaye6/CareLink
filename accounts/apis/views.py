from rest_framework.decorators import APIView, api_view ,permission_classes
from rest_framework.response import Response
from accounts.apis.permissions import IsAdmin , IsDoctor , IsPatient ,IsReceptionist
from accounts.models import DoctorProfile, User , ReceptionistProfile ,PatientProfile
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
import environ
from .serializers import ResetPasswordRequestSerializer, ResetPasswordConfirmSerializer, changePasswordSerializer 
from .serializers import SignUpAdminSerializer, SignUpDoctorSerializer , SignUpPatientSerializer, SignUpReceptionistSerializer, SignUpUserSerializer, UserSerializer
from .serializers import DoctorProfileSerializer, PatientProfileSerializer, ReceptionistProfileSerializer, AdminProfileSerializer



@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    data = request.data
    role = data.get('role')
    email = data.get('email')
    username = data.get('username')
    if User.objects.filter(email=email).exists():
        return Response({'message': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
    if(User.objects.filter(username=username).exists()):
        return Response({'message': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
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
        token,created = Token.objects.get_or_create(user=CreatedUser)
        return Response({'message': 'User created successfully',"user":serializer.data, "token": token.key}, status=status.HTTP_201_CREATED)
    return Response({'errors': serializer.errors , "message": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)
  

@api_view(['GET','PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user
    role = user.role
    
    if role == 'DOCTOR':
        instance = user.doctor_profile
        serializer_class = DoctorProfileSerializer
    elif role == 'PATIENT':
        instance = user.patient_profile
        serializer_class = PatientProfileSerializer
    elif role == 'RECEPTIONIST':
        instance = user.receptionist_profile
        serializer_class = ReceptionistProfileSerializer
    elif role == 'ADMIN':
        instance = user 
        serializer_class = AdminProfileSerializer
    else:
        return Response({'message': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        serializer = serializer_class(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PATCH':
        context={'request': request}
        serializer = serializer_class(instance, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    request.user.auth_token.delete()
    return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def changePassword(request):
    user = request.user
    serializer = changePasswordSerializer(data=request.data)
    if serializer.is_valid():
        if not user.check_password(serializer.validated_data['oldPassword']):
            return Response({"message": "Wrong old password."}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.validated_data['oldPassword'] == serializer.validated_data['newPassword']:
            return Response({"message": "New password cannot be the same as the old one."}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.validated_data['repeatNewPssword'] != serializer.validated_data['newPassword']:
            return Response({"message": "New password doesn't match repeat Password."}, status=status.HTTP_400_BAD_REQUEST)       
        user.set_password(serializer.validated_data['newPassword'])
        user.save()
        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_request(request):

    serializer = ResetPasswordRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    email = serializer.validated_data['email']

    if not User.objects.filter(email=email):
        return Response({'message': 'Email not found'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.get(email=email)
    token= default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_link = f"http://localhost:4200/auth/reset-password?uid={uid}&token={token}"
    send_mail(
        subject='Reset Your Password',
        message=f'Click the link to reset your password: {reset_link}',
        from_email='mohamadelazzazy@gmail.com',
        recipient_list=[email],
    )
    return Response({'message': 'Reset link sent to your email'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_confirm(request):
    serializer = ResetPasswordConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    token = serializer.validated_data['token']
    new_password = serializer.validated_data['new_password']
    uid = request.data.get('uid')
    user_id = force_str(urlsafe_base64_decode(uid))
    user = User.objects.get(pk=user_id)
    if not default_token_generator.check_token(user, token):
        return Response({'message': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
    user.set_password(new_password)
    user.save()
    return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAdmin])
def list_users(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdmin])
def list_ActiveUsers(request):
    users = User.objects.filter(is_active=1)
    serializer = UserSerializer(users , many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdmin])
def list_InActiveUsers(request):
    users = User.objects.filter(is_active=0)
    serializer = UserSerializer(users , many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdmin])
def list_ActivePatients(request):
    users = PatientProfile.objects.filter(user__is_active=1)
    serializer = PatientProfileSerializer(users , many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdmin])
def list_ActiveReceptionists(request):
    users = ReceptionistProfile.objects.filter(user__is_active=1)
    serializer = ReceptionistProfileSerializer(users , many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_ActiveDoctors(request):
    users = DoctorProfile.objects.filter(user__is_active=1)
    serializer = DoctorProfileSerializer(users , many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_ActiveDoctorsBySpeciality(request):
    doc_speciality = request.query_params.get('speciality')
    users = DoctorProfile.objects.filter( user__is_active=1 , specialty=doc_speciality)
    serializer = DoctorProfileSerializer(users , many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)




