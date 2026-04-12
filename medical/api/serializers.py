from rest_framework import serializers
from ..models import ConsultationRecord, PrescriptionItem, TestRequest
from accounts.models import PatientProfile, DoctorProfile, User
from appointments.models import Appointment

class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = '__all__'

class TestRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestRequest
        fields = '__all__'

class ConsultationRecordSerializer(serializers.ModelSerializer):
    prescriptions = PrescriptionItemSerializer(many=True, read_only=True)
    tests = TestRequestSerializer(many=True, read_only=True)

    class Meta:
        model = ConsultationRecord
        fields = '__all__'




class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username']


class PatientBasicSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = PatientProfile
        fields = ['id', 'user', 'phone_number']


class AppointmentSerializer(serializers.ModelSerializer):
    patient = PatientBasicSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'scheduled_datetime',
            'status', 'check_in_time',
            'is_telemedicine', 'meeting_link',
        ]

