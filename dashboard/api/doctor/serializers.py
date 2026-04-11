from django.utils import timezone
from rest_framework import serializers

from accounts.models import DoctorProfile, PatientProfile
from appointments.models import WeeklySchedule, ScheduleException, Appointment
from medical.models import ConsultationRecord, PrescriptionItem, TestRequest


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


class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = ['id', 'drug_name', 'dose', 'duration_days']


class TestRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestRequest
        fields = ['id', 'test_name']


class ConsultationForDoctorPatientSerializer(serializers.ModelSerializer):
    prescriptions = PrescriptionItemSerializer(many=True, read_only=True)
    tests = TestRequestSerializer(many=True, read_only=True)

    class Meta:
        model = ConsultationRecord
        fields = ['id', 'diagnosis', 'clinical_notes', 'created_at', 'prescriptions', 'tests']


class DoctorPatientAppointmentSerializer(serializers.ModelSerializer):
    consultation = ConsultationForDoctorPatientSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'scheduled_datetime',
            'status',
            'is_telemedicine',
            'meeting_link',
            'check_in_time',
            'consultation',
        ]


class DoctorPatientListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    appointments_count = serializers.SerializerMethodField()
    last_appointment_at = serializers.SerializerMethodField()
    next_appointment_at = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = [
            'id',
            'username',
            'email',
            'date_of_birth',
            'phone_number',
            'appointments_count',
            'last_appointment_at',
            'next_appointment_at',
        ]

    def _doctor_qs(self, obj):
        doctor = self.context.get('doctor')
        if not doctor:
            return obj.appointments.none()
        return obj.appointments.filter(doctor=doctor)

    def get_appointments_count(self, obj):
        return self._doctor_qs(obj).count()

    def get_last_appointment_at(self, obj):
        now = timezone.now()
        ap = (
            self._doctor_qs(obj)
            .filter(scheduled_datetime__lt=now)
            .order_by('-scheduled_datetime')
            .first()
        )
        return ap.scheduled_datetime if ap else None

    def get_next_appointment_at(self, obj):
        now = timezone.now()
        ap = (
            self._doctor_qs(obj)
            .filter(scheduled_datetime__gte=now)
            .exclude(status='CANCELLED')
            .order_by('scheduled_datetime')
            .first()
        )
        return ap.scheduled_datetime if ap else None


class DoctorPatientDetailSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)
    last_appointment_at = serializers.SerializerMethodField()
    next_appointment_at = serializers.SerializerMethodField()
    appointments = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = [
            'id',
            'username',
            'email',
            'role',
            'date_of_birth',
            'phone_number',
            'medical_history',
            'last_appointment_at',
            'next_appointment_at',
            'appointments',
        ]

    def _doctor_appt_qs(self, obj):
        doctor = self.context.get('doctor')
        if not doctor:
            return obj.appointments.none()
        return obj.appointments.filter(doctor=doctor)

    def get_last_appointment_at(self, obj):
        now = timezone.now()
        ap = (
            self._doctor_appt_qs(obj)
            .filter(scheduled_datetime__lt=now)
            .order_by('-scheduled_datetime')
            .first()
        )
        return ap.scheduled_datetime if ap else None

    def get_next_appointment_at(self, obj):
        now = timezone.now()
        ap = (
            self._doctor_appt_qs(obj)
            .filter(scheduled_datetime__gte=now)
            .exclude(status='CANCELLED')
            .order_by('scheduled_datetime')
            .first()
        )
        return ap.scheduled_datetime if ap else None

    def get_appointments(self, obj):
        doctor = self.context.get('doctor')
        if not doctor:
            return []
        qs = (
            obj.appointments.filter(doctor=doctor)
            .select_related('consultation')
            .prefetch_related('consultation__prescriptions', 'consultation__tests')
            .order_by('-scheduled_datetime')
        )
        return DoctorPatientAppointmentSerializer(qs, many=True).data


class DoctorAppointmentListSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(source='patient.id', read_only=True)
    patient_username = serializers.CharField(source='patient.user.username', read_only=True)
    patient_email = serializers.EmailField(source='patient.user.email', read_only=True)
    patient_phone = serializers.CharField(source='patient.phone_number', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'scheduled_datetime',
            'status',
            'is_telemedicine',
            'meeting_link',
            'check_in_time',
            'patient_id',
            'patient_username',
            'patient_email',
            'patient_phone',
        ]


class DoctorAppointmentPatientSummarySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = PatientProfile
        fields = [
            'id',
            'username',
            'email',
            'role',
            'date_of_birth',
            'phone_number',
            'medical_history',
        ]


class DoctorAppointmentDetailSerializer(serializers.ModelSerializer):
    patient = DoctorAppointmentPatientSummarySerializer(read_only=True)
    consultation = ConsultationForDoctorPatientSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient',
            'scheduled_datetime',
            'status',
            'check_in_time',
            'is_telemedicine',
            'meeting_link',
            'consultation',
        ]
