from rest_framework import serializers
from accounts.models import User, PatientProfile, DoctorProfile, ReceptionistProfile
from django.contrib.auth.models import Group



class SignUpDoctorSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True, max_length=254)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    #specialty = serializers.CharField(required=True,write_only=True)
    specialty = serializers.ChoiceField(choices=DoctorProfile.SPECIALTY_CHOICES, required=True, write_only=True)
    session_duration = serializers.ChoiceField(choices=DoctorProfile.SESSION_CHOICES, required=True, write_only=True)
    buffer_time = serializers.IntegerField(required=True,write_only=True)
    session_price = serializers.IntegerField(required=True,write_only=True)

    def create(self, validated_data):
        user = User.objects.create_user(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role="DOCTOR",
            is_active=False
        )

        group, created = Group.objects.get_or_create(name='Doctors')
        user.groups.add(group)

        CreatedUser = DoctorProfile.objects.create(
            user = user,
            specialty = validated_data['specialty'],
            session_duration = validated_data['session_duration'],
            buffer_time = validated_data['buffer_time'],
            session_price = validated_data['session_price']
        )
        return user



class SignUpPatientSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True, max_length=254)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    date_of_birth = serializers.DateField(required=True, input_formats=['%Y-%m-%d'], write_only=True)
    phone_number = serializers.CharField(required=True, write_only=True)
    medical_history = serializers.CharField(required=False, write_only=True)

    def create(self, validated_data):
        user = User.objects.create_user(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role="PATIENT",
            is_active=False
        )

        group, created = Group.objects.get_or_create(name='Patients')
        user.groups.add(group)

        CreatedUser = PatientProfile.objects.create(
            user = user,
            date_of_birth = validated_data['date_of_birth'],
            phone_number = validated_data['phone_number'],
            medical_history = validated_data['medical_history']
        )
        return user



class SignUpReceptionistSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True, max_length=254)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    doctor_id = serializers.IntegerField(required=True, write_only=True)

    def create(self, validated_data):
        try:
            doctor = DoctorProfile.objects.get(id=validated_data['doctor_id'])
        except DoctorProfile.DoesNotExist:
            raise serializers.ValidationError({"doctor_id": "Doctor not found."})

        user = User.objects.create_user(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role='RECEPTIONIST',
            is_active=False
        )

        group, created = Group.objects.get_or_create(name='Receptionists')
        user.groups.add(group)

        CreatedUser=ReceptionistProfile.objects.create(
            user=user,
            doctor=doctor
        )
        return user



class SignUpAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        CreatedUser = User.objects.create_user(
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role='ADMIN',
            is_active=False
        )
        
        group, created = Group.objects.get_or_create(name='Admins')
        CreatedUser.groups.add(group)

        return CreatedUser
        


class SignUpUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True, max_length=254)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=True)

    def create(self, validated_data):
        CreatedUser = User.objects.create_user(**validated_data)
        return CreatedUser
        

###############################################################
###############################################################
###############################################################


class DoctorProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'role', 'specialty', 'session_duration', 'buffer_time','session_price']



class PatientProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = PatientProfile
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'role', 'date_of_birth', 'phone_number', 'medical_history']



class ReceptionistProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.username', read_only=True)

    class Meta:
        model = ReceptionistProfile
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'role', 'doctor', 'doctor_name']



class AdminProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'role']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'role','is_active', 'date_joined']