# from time import timezone
# from django.shortcuts import render, get_object_or_404, redirect
# from django.http import HttpResponse
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.response import Response
# from rest_framework import status ,permissions
# from medical.api.serializers import ConsultationRecordSerializer, PrescriptionItemSerializer, TestRequestSerializer
# from medical.models import ConsultationRecord, PrescriptionItem, TestRequest
# from appointments.models import Appointment
# from rest_framework.permissions import AllowAny, IsAuthenticated,BasePermission
# from accounts.apis.permissions  import IsDoctor, IsPatient 
# from django.db import transaction
# from django.utils import timezone
# from appointments.api.serializers import BookAppointmentSerializer
# # Create your views here.
# @api_view(['POST'])
# #@permission_classes([IsDoctor])
# @permission_classes([IsAuthenticated])
# def save_consultation(request, appointment_id):
#     appointment = get_object_or_404(Appointment, pk=appointment_id)
#     if appointment.doctor != request.user.doctor_profile:
#         return Response(
#             {'error': 'You are not the doctor for this appointment'},
#             status=status.HTTP_403_FORBIDDEN
#         )

#     if appointment.status != 'CHECKED_IN':
#         return Response(
#             {'error': 'Consultation can only be filled for CHECKED_IN appointments'},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     if ConsultationRecord.objects.filter(appointment=appointment).exists():
#         return Response(
#             {'error': 'Consultation already exists for this appointment'},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     with transaction.atomic():
#         consultation = ConsultationRecord.objects.create(
#             appointment=appointment,
#             diagnosis=request.data.get('diagnosis', ''),
#             clinical_notes=request.data.get('clinical_notes', '')
#         )

#         for rx in request.data.get('prescriptions', []):
#             PrescriptionItem.objects.create(
#                 consultation=consultation,
#                 drug_name=rx.get('drug_name', ''),
#                 dose=rx.get('dose', ''),
#                 duration_days=rx.get('duration_days', 1)
#             )

#         for test in request.data.get('tests', []):
#             TestRequest.objects.create(
#                 consultation=consultation,
#                 test_name=test.get('test_name', '')
#             )

#         appointment.status = 'COMPLETED'
#         appointment.save()

#     return Response(
#         ConsultationRecordSerializer(consultation).data,
#         status=status.HTTP_201_CREATED
#     )

# @api_view(['GET'])
# #@permission_classes([IsPatient])
# @permission_classes([IsAuthenticated])
# def patient_consultation_summary(request, appointment_id):
#     appointment = get_object_or_404(Appointment, pk=appointment_id)

#     if appointment.patient != request.user.patient_profile:
#         return Response(
#             {'error': 'You are not authorized to view this consultation'},
#             status=status.HTTP_403_FORBIDDEN
#         )

#     if appointment.status != 'COMPLETED':
#         return Response(
#             {'error': 'Consultation not completed yet'},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     consultation = get_object_or_404(ConsultationRecord, appointment=appointment)
#     return Response(ConsultationRecordSerializer(consultation).data)


# @api_view(['GET'])
# @permission_classes([IsDoctor])
# def get_consultation(request, appointment_id):
#     appointment = get_object_or_404(Appointment, pk=appointment_id)
#     if appointment.doctor != request.user.doctor_profile:
#         return Response(
#             {'error': 'You are not the doctor for this appointment'},
#             status=status.HTTP_403_FORBIDDEN
#         )

#     consultation = get_object_or_404(ConsultationRecord, appointment=appointment)
#     return Response(ConsultationRecordSerializer(consultation).data)

# @api_view(['GET'])
# @permission_classes([IsDoctor])
# def doctor_queue(request):
#     today = timezone.now().date()
#     appointments = Appointment.objects.filter(
#         doctor=request.user.doctor_profile,
#         scheduled_datetime__date=today,
#         status='CHECKED_IN'
#     ).order_by('check_in_time')
    
#     from appointments.api.serializers import AppointmentSerializer
#     serializer = AppointmentSerializer(appointments, many=True)
#     return Response(serializer.data)
# وووووووووووووووو
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.utils import timezone
from django.db.models import Exists, OuterRef
from appointments.models import Appointment
from medical.models import ConsultationRecord, PrescriptionItem, TestRequest
from medical.api.serializers import (
    ConsultationRecordSerializer,
    PrescriptionItemSerializer,
    TestRequestSerializer,
    AppointmentSerializer
)
from accounts.apis.permissions import IsDoctor, IsPatient
from rest_framework.permissions import IsAuthenticated
class MedicalPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([IsDoctor])
def doctor_queue(request):
    today = timezone.now().date()
    appointments = Appointment.objects.filter(
        doctor=request.user.doctor_profile,
        scheduled_datetime__date=today,
        status='CHECKED_IN'
    )

    search = request.query_params.get('search')
    if search:
        appointments = appointments.filter(
            patient__user__first_name__icontains=search
        ) | appointments.filter(
            patient__user__last_name__icontains=search
        ) | appointments.filter(
            id__icontains=search
        )

    status_filter = request.query_params.get('status')
    if status_filter:
        appointments = appointments.filter(status=status_filter)


    ordering = request.query_params.get('ordering', 'check_in_time')
    appointments = appointments.order_by(ordering)

    paginator = MedicalPagination()
    paginated = paginator.paginate_queryset(appointments, request)
    serializer = AppointmentSerializer(paginated, many=True)
    return paginator.get_paginated_response(serializer.data)


def _replace_consultation_children(consultation, prescriptions_data, tests_data):
    consultation.prescriptions.all().delete()
    consultation.tests.all().delete()
    for rx in prescriptions_data or []:
        PrescriptionItem.objects.create(
            consultation=consultation,
            drug_name=(rx.get('drug_name') or '')[:150],
            dose=(rx.get('dose') or '')[:100],
            duration_days=int(rx.get('duration_days') or 1),
        )
    for test in tests_data or []:
        TestRequest.objects.create(
            consultation=consultation,
            test_name=(test.get('test_name') or '')[:150],
        )


@api_view(['POST'])
@permission_classes([IsDoctor])
def save_consultation(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)

    if appointment.doctor != request.user.doctor_profile:
        return Response(
            {'error': 'You are not the doctor for this appointment'},
            status=status.HTTP_403_FORBIDDEN
        )

    if appointment.status not in ('CHECKED_IN', 'NO_SHOW'):
        return Response(
            {
                'error': (
                    'Consultation can only be saved when the appointment is Checked in or No-show. '
                    'Ask reception to check the patient in, or use the correct visit status first.'
                )
            },
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
            diagnosis=(request.data.get('diagnosis') or '')[:255],
            clinical_notes=request.data.get('clinical_notes') or '',
        )
        _replace_consultation_children(
            consultation,
            request.data.get('prescriptions'),
            request.data.get('tests'),
        )
        appointment.status = 'COMPLETED'
        appointment.save(update_fields=['status'])

    consultation = (
        ConsultationRecord.objects.select_related(
            'appointment',
            'appointment__patient',
            'appointment__patient__user',
            'appointment__doctor',
            'appointment__doctor__user',
        )
        .prefetch_related('prescriptions', 'tests')
        .get(pk=consultation.pk)
    )
    return Response(
        ConsultationRecordSerializer(consultation).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['PATCH', 'PUT'])
@permission_classes([IsDoctor])
def edit_consultation(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)

    if appointment.doctor != request.user.doctor_profile:
        return Response(
            {'error': 'You are not the doctor for this appointment'},
            status=status.HTTP_403_FORBIDDEN,
        )

    consultation = ConsultationRecord.objects.filter(appointment=appointment).first()
    if not consultation:
        return Response(
            {'error': 'No consultation to edit. Add a consultation first.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if appointment.status not in ('CHECKED_IN', 'NO_SHOW', 'COMPLETED'):
        return Response(
            {'error': 'Consultation cannot be edited for this appointment status.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        locked = ConsultationRecord.objects.select_for_update().get(pk=consultation.pk)
        locked.diagnosis = (request.data.get('diagnosis') or '')[:255]
        locked.clinical_notes = request.data.get('clinical_notes') or ''
        locked.save(
            update_fields=['diagnosis', 'clinical_notes'],
        )
        _replace_consultation_children(
            locked,
            request.data.get('prescriptions'),
            request.data.get('tests'),
        )

    consultation.refresh_from_db()
    consultation = (
        ConsultationRecord.objects.select_related(
            'appointment',
            'appointment__patient',
            'appointment__patient__user',
            'appointment__doctor',
            'appointment__doctor__user',
        )
        .prefetch_related('prescriptions', 'tests')
        .get(pk=consultation.pk)
    )
    return Response(ConsultationRecordSerializer(consultation).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsDoctor])
def get_consultation(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)

    if appointment.doctor != request.user.doctor_profile:
        return Response(
            {'error': 'You are not the doctor for this appointment'},
            status=status.HTTP_403_FORBIDDEN
        )

    consultation = get_object_or_404(
        ConsultationRecord.objects.filter(appointment=appointment)
        .select_related(
            'appointment',
            'appointment__patient',
            'appointment__patient__user',
            'appointment__doctor',
            'appointment__doctor__user',
        )
        .prefetch_related(
            'prescriptions',
            'tests',
        ),
        appointment=appointment,
    )
    return Response(ConsultationRecordSerializer(consultation).data)


@api_view(['GET'])
@permission_classes([IsPatient])
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

    consultation = get_object_or_404(
        ConsultationRecord.objects.select_related(
            'appointment',
            'appointment__patient',
            'appointment__patient__user',
            'appointment__doctor',
            'appointment__doctor__user',
        ).prefetch_related('prescriptions', 'tests'),
        appointment=appointment,
    )
    return Response(ConsultationRecordSerializer(consultation).data)


@api_view(['GET'])
@permission_classes([IsDoctor])
def doctor_prescriptions(request):
    prescriptions = PrescriptionItem.objects.filter(
        consultation__appointment__doctor=request.user.doctor_profile
    )

    search = request.query_params.get('search')
    if search:
        prescriptions = prescriptions.filter(
            drug_name__icontains=search
        ) | prescriptions.filter(
            consultation__appointment__patient__user__first_name__icontains=search
        )

    drug = request.query_params.get('drug_name')
    if drug:
        prescriptions = prescriptions.filter(drug_name__icontains=drug)

    ordering = request.query_params.get('ordering', '-id')
    prescriptions = prescriptions.order_by(ordering)

    paginator = MedicalPagination()
    paginated = paginator.paginate_queryset(prescriptions, request)
    serializer = PrescriptionItemSerializer(paginated, many=True)
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
@permission_classes([IsDoctor])
def doctor_tests(request):
    tests = TestRequest.objects.filter(
        consultation__appointment__doctor=request.user.doctor_profile
    )

    search = request.query_params.get('search')
    if search:
        tests = tests.filter(
            test_name__icontains=search
        ) | tests.filter(
            consultation__appointment__patient__user__first_name__icontains=search
        )

    test_name = request.query_params.get('test_name')
    if test_name:
        tests = tests.filter(test_name__icontains=test_name)

    ordering = request.query_params.get('ordering', '-id')
    tests = tests.order_by(ordering)

    paginator = MedicalPagination()
    paginated = paginator.paginate_queryset(tests, request)
    serializer = TestRequestSerializer(paginated, many=True)
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
@permission_classes([IsPatient])
def patient_appointments(request):
    appointments = (
        Appointment.objects.filter(patient=request.user.patient_profile)
        .annotate(
            has_consultation=Exists(
                ConsultationRecord.objects.filter(appointment_id=OuterRef('pk'))
            )
        )
    )

    status_filter = request.query_params.get('status')
    if status_filter:
        appointments = appointments.filter(status=status_filter)

    ordering = request.query_params.get('ordering', '-scheduled_datetime')
    appointments = appointments.order_by(ordering)

    paginator = MedicalPagination()
    paginated = paginator.paginate_queryset(appointments, request)
    serializer = AppointmentSerializer(paginated, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsPatient])
def patient_cancel_appointment(request, appointment_id):
    appt = get_object_or_404(
        Appointment.objects.select_related('doctor', 'doctor__user', 'patient', 'patient__user'),
        pk=appointment_id,
    )
    if appt.patient != request.user.patient_profile:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    if appt.status not in ('REQUESTED', 'CONFIRMED'):
        return Response(
            {'message': 'not valid', 'errors': {'status': ['You can only cancel when status is REQUESTED or CONFIRMED']}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    appt.status = 'CANCELLED'
    appt.save(update_fields=['status'])
    return Response({'message': 'cancelled', 'appointment': AppointmentSerializer(appt).data}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsDoctor])
def doctor_consultation_history(request):
    consultations = ConsultationRecord.objects.filter(
        appointment__doctor=request.user.doctor_profile
    ).select_related(
        'appointment',
        'appointment__patient',
        'appointment__patient__user',
        'appointment__doctor',
        'appointment__doctor__user',
    )

    search = request.query_params.get('search')
    if search:
        consultations = consultations.filter(
            appointment__patient__user__first_name__icontains=search
        ) | consultations.filter(
            appointment__patient__user__last_name__icontains=search
        ) | consultations.filter(
            diagnosis__icontains=search
        )

    ordering = request.query_params.get('ordering', '-appointment__scheduled_datetime')
    consultations = consultations.order_by(ordering)

    paginator = MedicalPagination()
    paginated = paginator.paginate_queryset(consultations, request)
    serializer = ConsultationRecordSerializer(paginated, many=True)
    return paginator.get_paginated_response(serializer.data)