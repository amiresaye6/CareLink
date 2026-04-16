from rest_framework import serializers
from appointments.models import Appointment, AppointmentAuditTrail, RescheduleRequest
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
    patient_booking = serializers.JSONField(read_only=True, required=False, allow_null=True)


class BookAppointmentSerializer(serializers.Serializer):
    scheduled_datetime = serializers.DateTimeField(required=True, write_only=True)
    is_telemedicine = serializers.BooleanField(required=False, default=False, write_only=True)


from appointments.models import Appointment
from accounts.models import PatientProfile, DoctorProfile


class PatientInfoSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = ['id', 'full_name', 'phone_number']

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username


class DoctorInfoSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = ['id', 'full_name', 'specialty']

    def get_full_name(self, obj):
        first = obj.user.first_name
        last = obj.user.last_name
        if first or last:
            return f"Dr. {first} {last}".strip()
        return f"Dr. {obj.user.username}"

class QueueSerializer(serializers.ModelSerializer):
    patient = PatientInfoSerializer(read_only=True)
    doctor = DoctorInfoSerializer(read_only=True)
    waiting_time_minutes = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient',
            'doctor',
            'scheduled_datetime',
            'status',
            'check_in_time',
            'waiting_time_minutes',
        ]

    def get_waiting_time_minutes(self, obj):
        if obj.status == 'CHECKED_IN' and obj.check_in_time:
            from django.utils import timezone
            delta = timezone.now() - obj.check_in_time
            return int(delta.total_seconds() // 60)
        return None


class AppointmentListSerializer(serializers.ModelSerializer):
    patient = PatientInfoSerializer(read_only=True)
    doctor = DoctorInfoSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient',
            'doctor',
            'scheduled_datetime',
            'status',
            'check_in_time',
            'is_telemedicine',
        ]


class AppointmentStatusUpdateSerializer(serializers.ModelSerializer):

    ALLOWED_TRANSITIONS = {
        'REQUESTED':  ['CONFIRMED', 'CANCELLED'],
        'CONFIRMED':  ['CHECKED_IN', 'CANCELLED', 'NO_SHOW'],
        'CHECKED_IN': ['COMPLETED', 'NO_SHOW'],
        'COMPLETED':  [],
        'CANCELLED':  [],
        'NO_SHOW':    [],
    }

    class Meta:
        model = Appointment
        fields = ['status']

    def validate_status(self, new_status):
        current_status = self.instance.status
        allowed = self.ALLOWED_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise serializers.ValidationError(
                f"Cannot change from '{current_status}' to '{new_status}'. "
                f"Allowed transitions: {allowed}"
            )
        return new_status

class RescheduleRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RescheduleRequest
        fields = ['id', 'proposed_datetime', 'reason', 'status', 'response_note', 'created_at']
        read_only_fields = ['status', 'response_note', 'created_at']

class AdminAuditLogSerializer(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField()
    role = serializers.CharField(source='actor_role')
    appointment_id = serializers.IntegerField(source='appointment.id')

    class Meta:
        model = AppointmentAuditTrail
        fields = [
            'id', 'appointment_id', 'user_full_name', 'role', 
            'action_type', 'old_datetime', 'new_datetime', 
            'reason', 'timestamp'
        ]

    def get_user_full_name(self, obj):
        if obj.changed_by:
            return f"{obj.changed_by.first_name} {obj.changed_by.last_name}".strip() or obj.changed_by.username
        return "System"