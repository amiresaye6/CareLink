from rest_framework import serializers
from accounts.models import User, PatientProfile, DoctorProfile, ReceptionistProfile



class SignUpDoctorSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True, max_length=254)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    #specialty = serializers.CharField(required=True,write_only=True)
    specialty = serializers.ChoiceField(choices=DoctorProfile.SPECIALTY_CHOICES, required=True, write_only=True)
    session_duration = serializers.ChoiceField(choices=DoctorProfile.SESSION_CHOICES, required=True, write_only=True)
    buffer_time = serializers.IntegerField(required=True,write_only=True)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role="DOCTOR",
        )
        CreatedUser = DoctorProfile.objects.create(
            user = user,
            specialty = validated_data['specialty'],
            session_duration = validated_data['session_duration'],
            buffer_time = validated_data['buffer_time']
        )
        return user



class SignUpPatientSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True, max_length=254)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    date_of_birth = serializers.DateField(required=True, input_formats=['%Y-%m-%d'], write_only=True)
    phone_number = serializers.CharField(required=True, write_only=True)
    medical_history = serializers.CharField(required=False, write_only=True)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role="PATIENT",
        )
        CreatedUser = PatientProfile.objects.create(
            user = user,
            date_of_birth = validated_data['date_of_birth'],
            phone_number = validated_data['phone_number'],
            medical_history = validated_data['medical_history']
        )
        return user



class SignUpReceptionistSerializer(serializers.Serializer):
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
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role='RECEPTIONIST'
        )
        CreatedUser=ReceptionistProfile.objects.create(
            user=user,
            doctor=doctor
        )
        return user



class SignUpAdminSerializer(serializers.Serializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        CreatedUser = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role='TO_BE_ADMIN'
        )
        return CreatedUser
        


class SignUpUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

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
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ['id', 'username', 'email', 'role', 'specialty', 'session_duration', 'buffer_time']



class PatientProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = PatientProfile
        fields = ['id', 'username', 'email', 'role', 'date_of_birth', 'phone_number', 'medical_history']



class ReceptionistProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.username', read_only=True)

    class Meta:
        model = ReceptionistProfile
        fields = ['id', 'username', 'email', 'role', 'doctor', 'doctor_name']



class AdminProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']