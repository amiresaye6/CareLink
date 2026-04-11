from time import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status ,permissions
from medical.api.serializers import ConsultationRecordSerializer, PrescriptionItemSerializer, TestRequestSerializer
from medical.models import ConsultationRecord, PrescriptionItem, TestRequest
from appointments.models import Appointment
from rest_framework.permissions import AllowAny, IsAuthenticated,BasePermission
from accounts.apis.permissions  import IsDoctor, IsPatient 
from django.db import transaction
from django.utils import timezone
from appointments.api.serializers import BookAppointmentSerializer
# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_consultation(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    if appointment.doctor != request.user.doctor_profile:
        return Response(
            {'error': 'You are not the doctor for this appointment'},
            status=status.HTTP_403_FORBIDDEN
        )

    if appointment.status != 'CHECKED_IN':
        return Response(
            {'error': 'Consultation can only be filled for CHECKED_IN appointments'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if ConsultationRecord.objects.filter(appointment=appointment).exists():
        return Response(
            {'error': 'Consultation already exists for this appointment'},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        consultation = ConsultationRecord.objects.create(
            appointment=appointment,
            diagnosis=request.data.get('diagnosis', ''),
            clinical_notes=request.data.get('clinical_notes', '')
        )

        for rx in request.data.get('prescriptions', []):
            PrescriptionItem.objects.create(
                consultation=consultation,
                drug_name=rx.get('drug_name', ''),
                dose=rx.get('dose', ''),
                duration_days=rx.get('duration_days', 1)
            )

        for test in request.data.get('tests', []):
            TestRequest.objects.create(
                consultation=consultation,
                test_name=test.get('test_name', '')
            )

        appointment.status = 'COMPLETED'
        appointment.save()

    return Response(
        ConsultationRecordSerializer(consultation).data,
        status=status.HTTP_201_CREATED
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_consultation_summary(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)

    if appointment.patient != request.user.patient_profile:
        return Response(
            {'error': 'You are not authorized to view this consultation'},
            status=status.HTTP_403_FORBIDDEN
        )

    if appointment.status != 'COMPLETED':
        return Response(
            {'error': 'Consultation not completed yet'},
            status=status.HTTP_400_BAD_REQUEST
        )

    consultation = get_object_or_404(ConsultationRecord, appointment=appointment)
    return Response(ConsultationRecordSerializer(consultation).data)


@api_view(['GET'])
@permission_classes([IsDoctor])
def get_consultation(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    if appointment.doctor != request.user.doctor_profile:
        return Response(
            {'error': 'You are not the doctor for this appointment'},
            status=status.HTTP_403_FORBIDDEN
        )

    consultation = get_object_or_404(ConsultationRecord, appointment=appointment)
    return Response(ConsultationRecordSerializer(consultation).data)

@api_view(['GET'])
@permission_classes([IsDoctor])
def doctor_queue(request):
    today = timezone.now().date()
    appointments = Appointment.objects.filter(
        doctor=request.user.doctor_profile,
        scheduled_datetime__date=today,
        status='CHECKED_IN'
    ).order_by('check_in_time')
    
    from appointments.api.serializers import AppointmentSerializer
    serializer = AppointmentSerializer(appointments, many=True)
    return Response(serializer.data)