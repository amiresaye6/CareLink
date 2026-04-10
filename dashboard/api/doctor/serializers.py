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



WEEKLY_DAYS_EXCEPT_FRIDAY = (0, 1, 2, 3, 5, 6)


class WeeklyScheduleBulkSetSerializer(serializers.Serializer):

    start_time = serializers.TimeField()
    end_time = serializers.TimeField()


class WeeklyScheduleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklySchedule
        fields = '__all__'
        read_only_fields = ('id', 'doctor')

    def create(self, validated_data):
        schedule = WeeklySchedule.objects.create(**validated_data)
        return schedule

    def update(self, instance, validated_data):
        instance.day_of_week = validated_data.get('day_of_week', instance.day_of_week)
        instance.start_time = validated_data.get('start_time', instance.start_time)
        instance.end_time = validated_data.get('end_time', instance.end_time)
        instance.save()
        return instance

    def delete(self, instance):
        instance.delete()
        return instance





class ScheduleExceptionModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleException
        fields = '__all__'
        read_only_fields = ('id', 'doctor')

    def create(self, validated_data):
        return ScheduleException.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.date = validated_data.get('date', instance.date)
        instance.is_day_off = validated_data.get('is_day_off', instance.is_day_off)
        instance.start_time = validated_data.get('start_time', instance.start_time)
        instance.end_time = validated_data.get('end_time', instance.end_time)
        instance.save()
        return instance
