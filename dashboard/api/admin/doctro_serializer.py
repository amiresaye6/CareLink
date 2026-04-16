from rest_framework import serializers
from accounts.models import DoctorProfile

class DoctorPublicSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    specialty_display = serializers.CharField(source='get_specialty_display', read_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 
            'specialty', 'specialty_display', 'session_duration', 
            'buffer_time', 'session_price', 'profile_picture', 'profile_picture_url'
        ]