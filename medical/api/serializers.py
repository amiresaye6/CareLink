from rest_framework import serializers
from ..models import ConsultationRecord, PrescriptionItem, TestRequest

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

