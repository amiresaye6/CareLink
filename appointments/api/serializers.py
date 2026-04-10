from rest_framework import serializers

from dashboard.api.doctor.serializers import (
    DoctorProfileModelSerializer,
    WeeklyScheduleModelSerializer,
    ScheduleExceptionModelSerializer,
)


class DoctorAppointmentDetailsSerializer(serializers.Serializer):
    doctor = DoctorProfileModelSerializer(read_only=True)
    weekly_schedules = WeeklyScheduleModelSerializer(many=True, read_only=True)
    schedule_exceptions = ScheduleExceptionModelSerializer(many=True, read_only=True)
    range_start = serializers.DateTimeField(read_only=True)
    range_end = serializers.DateTimeField(read_only=True)
    selected_date = serializers.DateField(read_only=True)
    available_slots = serializers.ListField(child=serializers.DateTimeField(), read_only=True)
    session_duration = serializers.IntegerField(read_only=True)
    buffer_time = serializers.IntegerField(read_only=True)


class BookAppointmentSerializer(serializers.Serializer):
    scheduled_datetime = serializers.DateTimeField(required=True, write_only=True)
    is_telemedicine = serializers.BooleanField(required=False, default=False, write_only=True)
