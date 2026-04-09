from rest_framework import serializers
from accounts.models import DoctorProfile
from appointments.models import WeeklySchedule, ScheduleException


class DoctorProfileModelSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ['id', 'username', 'email', 'role', 'specialty', 'session_duration', 'buffer_time']
        read_only_fields = ('id',)

    def create(self, validated_data):
        doctor = DoctorProfile.objects.create(**validated_data)
        return doctor

    def update(self, instance, validated_data):
        instance.specialty = validated_data.get('specialty', instance.specialty)
        instance.session_duration = validated_data.get('session_duration', instance.session_duration)
        instance.buffer_time = validated_data.get('buffer_time', instance.buffer_time)
        instance.save()
        return instance

    def delete(self, instance):
        instance.delete()
        return instance




