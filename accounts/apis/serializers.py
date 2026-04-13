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

    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'role',
                  'specialty', 'session_duration', 'buffer_time', 'session_price']

    def get_first_name(self, obj):
        return obj.user.first_name

    def get_last_name(self, obj):
        return obj.user.last_name

    def get_username(self, obj):
        return obj.user.username

    def get_email(self, obj):
        return obj.user.email

    def get_role(self, obj):
        return obj.user.role

    def update(self, instance, validated_data):
        user = instance.user
        data = self.context['request'].data
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.save()
        instance.specialty = validated_data.get('specialty', instance.specialty)
        instance.session_duration = validated_data.get('session_duration', instance.session_duration)
        instance.buffer_time = validated_data.get('buffer_time', instance.buffer_time)
        instance.session_price = validated_data.get('session_price', instance.session_price)
        instance.save()
        return instance 


class PatientProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'role',
                  'date_of_birth', 'phone_number', 'medical_history']

    def get_first_name(self, obj):
        return obj.user.first_name

    def get_last_name(self, obj):
        return obj.user.last_name

    def get_username(self, obj):
        return obj.user.username

    def get_email(self, obj):
        return obj.user.email

    def get_role(self, obj):
        return obj.user.role

    def update(self, instance, validated_data):
        user = instance.user
        data = self.context['request'].data
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.save()
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.medical_history = validated_data.get('medical_history', instance.medical_history)
        instance.save()
        return instance


class ReceptionistProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = ReceptionistProfile
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'role',
                  'doctor', 'doctor_name']

    def get_first_name(self, obj):
        return obj.user.first_name

    def get_last_name(self, obj):
        return obj.user.last_name

    def get_username(self, obj):
        return obj.user.username

    def get_email(self, obj):
        return obj.user.email

    def get_role(self, obj):
        return obj.user.role

    def get_doctor_name(self, obj):
        return obj.doctor.user.username

    def update(self, instance, validated_data):
        user = instance.user
        data = self.context['request'].data
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.save()
        instance.doctor = validated_data.get('doctor', instance.doctor)
        instance.save()
        instance.refresh_from_db()
        return instance
    

class AdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'role']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'role','is_active', 'date_joined']


####################################################
####################################################
####################################################


class changePasswordSerializer(serializers.Serializer):
    oldPassword = serializers.CharField(required=True)
    newPassword = serializers.CharField(required=True,min_length=8)
    repeatNewPssword = serializers.CharField(required=True,min_length=8)



class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()



class ResetPasswordConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField()
