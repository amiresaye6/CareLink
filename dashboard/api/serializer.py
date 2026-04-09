from rest_framework import serializers
from accounts.models import User, PatientProfile, DoctorProfile, ReceptionistProfile

class PatientProfileSerializer(serializers.ModelSerializer):
    """Serializer for PatientProfile model"""

    class Meta:
        model = PatientProfile
        fields = [
            'id', 
            'date_of_birth',
            'phone_number',
            'medical_history'
        ]


class DoctorProfileSerializer(serializers.ModelSerializer):
    """Serializer for DoctorProfile model"""
    
    specialty_display = serializers.CharField(
        source='get_specialty_display',
        read_only=True
    )

    session_duration_display = serializers.CharField(
        source='get_session_duration_display',
        read_only=True
    )
    
    class Meta:
        model = DoctorProfile
        fields = [
            'id',
            'specialty',
            'specialty_display',
            'session_duration',
            'session_duration_display',
            'buffer_time',
        ]


class ReceptionistProfileSerializer(serializers.ModelSerializer):
    """Serializer for ReceptionistProfile"""
    
    doctor = DoctorProfileSerializer(read_only=True)
    doctor_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = ReceptionistProfile
        fields = [
            'id',
            'doctor',
            'doctor_id'
        ]


class UserDetailsSerializer(serializers.ModelSerializer):
    """Main serializer for the user details, will have only one account type active"""
    
    role_display = serializers.CharField(
        source='get_role_display',
        read_only=True
    )

    patient_profile = PatientProfileSerializer(read_only=True)
    doctor_profile = DoctorProfileSerializer(read_only=True)
    receptionist_profile = ReceptionistProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'role_display',
            'is_active',
            'date_joined',
            'patient_profile',
            'doctor_profile',
            'receptionist_profile'
        ]
        read_only_fields = ['id', 'date_joined']


class UserListSerializer(serializers.ModelSerializer):
    """simplified version for listing all users"""
    
    role_display = serializers.CharField(
        source='get_role_display',
        read_only=True
    )
    
    full_name = serializers.SerializerMethodField(method_name='get_full_name')
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'role_display',
            'is_active',
            'date_joined',
        ]
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"