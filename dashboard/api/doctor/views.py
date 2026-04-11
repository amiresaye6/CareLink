from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from accounts.apis.permissions import IsAdmin, IsDoctor
from datetime import datetime

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from accounts.models import DoctorProfile, PatientProfile
from appointments.models import WeeklySchedule, ScheduleException, Appointment
from dashboard.api.doctor.serializers import (
    DoctorProfileModelSerializer,
    WeeklyScheduleModelSerializer,
    WeeklyScheduleBulkSetSerializer,
    WEEKLY_DAYS_EXCEPT_FRIDAY,
    ScheduleExceptionModelSerializer,
    DoctorPatientListSerializer,
    DoctorPatientDetailSerializer,
)



def _get_logged_in_doctor(request):
    try:
        return request.user.doctor_profile
    except Exception:
        return None


def _parse_query_date(value):
    if not value or not str(value).strip():
        return None
    try:
        return datetime.strptime(str(value).strip(), '%Y-%m-%d').date()
    except Exception:
        return None


def _truthy_query_param(value):
    if value is None:
        return False
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


class DoctorPatientListPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                'count': self.page.paginator.count,
                'page': self.page.number,
                'total_pages': self.page.paginator.num_pages,
                'page_size': self.get_page_size(self.request),
                'patients': data,
            }
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated , IsAdmin])
def get_doctor_by_id(request, id):
    doctor = get_object_or_404(DoctorProfile, pk=id)
    doctor = DoctorProfileModelSerializer(doctor)
    return Response(doctor.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated , IsAdmin])
def update_doctor_by_id(request, id):
    doctor = get_object_or_404(DoctorProfile, pk=id)
    doctor = DoctorProfileModelSerializer(doctor, data=request.data, partial=True)
    if doctor.is_valid():
        doctor.save()
        return Response({'message': 'object updated!', 'doctor': doctor.data}, status=status.HTTP_200_OK)
    return Response({'message': 'not valid', 'errors': doctor.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated , IsDoctor])
def get_logged_in_doctor(request):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    doctor = DoctorProfileModelSerializer(doctor)
    return Response(doctor.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated , IsDoctor])
def update_logged_in_doctor(request):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    doctor = DoctorProfileModelSerializer(doctor, data=request.data, partial=True)
    if doctor.is_valid():
        doctor.save()
        return Response({'message': 'object updated!', 'doctor': doctor.data}, status=status.HTTP_200_OK)
    return Response({'message': 'not valid', 'errors': doctor.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated , IsDoctor])
def get_logged_in_weekly_schedules(request):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    schedules = WeeklySchedule.objects.filter(doctor=doctor).order_by('day_of_week', 'start_time')
    schedules = WeeklyScheduleModelSerializer(schedules, many=True)
    return Response(schedules.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated , IsDoctor])
def update_logged_in_weekly_schedule(request, id):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    schedule = get_object_or_404(WeeklySchedule, pk=id, doctor=doctor)
    schedule = WeeklyScheduleModelSerializer(schedule, data=request.data, partial=True)
    if schedule.is_valid():
        schedule.save()
        return Response({'message': 'object updated!', 'schedule': schedule.data}, status=status.HTTP_200_OK)
    return Response({'message': 'not valid', 'errors': schedule.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated , IsDoctor])
def delete_logged_in_weekly_schedule(request, id):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    schedule = get_object_or_404(WeeklySchedule, pk=id, doctor=doctor)
    schedule.delete()
    return Response({'message': 'object deleted!'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated , IsDoctor])
def create_logged_in_weekly_schedule(request):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    schedule = WeeklyScheduleModelSerializer(data=request.data)
    if not schedule.is_valid():
        return Response({'message': 'not valid', 'errors': schedule.errors}, status=status.HTTP_400_BAD_REQUEST)

    vd = schedule.validated_data
    existing = WeeklySchedule.objects.filter(
        doctor=doctor,
        day_of_week=vd['day_of_week'],
    ).first()

    if existing:
        existing.start_time = vd['start_time']
        existing.end_time = vd['end_time']
        existing.save()
        return Response(
            {'message': 'object updated!', 'schedule': WeeklyScheduleModelSerializer(existing).data},
            status=status.HTTP_200_OK,
        )

    schedule.save(doctor=doctor)
    return Response(
        {'message': 'object created!', 'schedule': schedule.data},
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST', 'PUT'])
@permission_classes([IsAuthenticated , IsDoctor])
def bulk_set_logged_in_weekly_schedules(request):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    ser = WeeklyScheduleBulkSetSerializer(data=request.data)
    if not ser.is_valid():
        return Response({'message': 'not valid', 'errors': ser.errors}, status=status.HTTP_400_BAD_REQUEST)

    start_time = ser.validated_data['start_time']
    end_time = ser.validated_data['end_time']
    saved = []
    for day in WEEKLY_DAYS_EXCEPT_FRIDAY:
        obj, _created = WeeklySchedule.objects.update_or_create(
            doctor=doctor,
            day_of_week=day,
            defaults={'start_time': start_time, 'end_time': end_time},
        )
        saved.append(obj)

    return Response(
        {
            'message': 'schedules saved',
            'days_set': list(WEEKLY_DAYS_EXCEPT_FRIDAY),
            'schedules': WeeklyScheduleModelSerializer(saved, many=True).data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated , IsDoctor])
def bulk_delete_logged_in_weekly_schedules(request):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    qs = WeeklySchedule.objects.filter(
        doctor=doctor,
        day_of_week__in=WEEKLY_DAYS_EXCEPT_FRIDAY,
    )
    deleted_count, _ = qs.delete()
    return Response(
        {'message': 'object deleted!', 'deleted_count': deleted_count},
        status=status.HTTP_200_OK,
    )





@api_view(['GET'])
@permission_classes([IsAuthenticated , IsDoctor])
def get_logged_in_schedule_exceptions(request):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    exc = ScheduleException.objects.filter(doctor=doctor).order_by('date')
    exc = ScheduleExceptionModelSerializer(exc, many=True)
    return Response(exc.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated , IsDoctor])
def create_logged_in_schedule_exception(request):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    exc = ScheduleExceptionModelSerializer(data=request.data)
    if not exc.is_valid():
        return Response({'message': 'not valid', 'errors': exc.errors}, status=status.HTTP_400_BAD_REQUEST)

    vd = exc.validated_data
    date_val = vd.get('date')
    if date_val is None:
        return Response(
            {'message': 'not valid', 'errors': {'date': ['This field is required.']}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    existing = ScheduleException.objects.filter(doctor=doctor, date=date_val).first()
    if existing:
        exc = ScheduleExceptionModelSerializer(existing, data=request.data, partial=True)
        if not exc.is_valid():
            return Response({'message': 'not valid', 'errors': exc.errors}, status=status.HTTP_400_BAD_REQUEST)
        exc.save()
        return Response({'message': 'object updated!', 'exception': exc.data}, status=status.HTTP_200_OK)

    exc.save(doctor=doctor)
    return Response({'message': 'object created!', 'exception': exc.data}, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_classes([IsAuthenticated , IsDoctor])
def update_logged_in_schedule_exception(request, id):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    exc = get_object_or_404(ScheduleException, pk=id, doctor=doctor)
    exc = ScheduleExceptionModelSerializer(exc, data=request.data, partial=True)
    if exc.is_valid():
        exc.save()
        return Response({'message': 'object updated!', 'exception': exc.data}, status=status.HTTP_200_OK)
    return Response({'message': 'not valid', 'errors': exc.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated , IsDoctor])
def delete_logged_in_schedule_exception(request, id):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    exc = get_object_or_404(ScheduleException, pk=id, doctor=doctor)
    exc.delete()
    return Response({'message': 'object deleted!'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_logged_in_doctor_patients(request):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    appts = Appointment.objects.filter(doctor=doctor)

    status_param = (request.query_params.get('appointment_status') or '').strip()
    if status_param:
        statuses = [s.strip() for s in status_param.split(',') if s.strip()]
        allowed = {c[0] for c in Appointment.STATUS_CHOICES}
        statuses = [s for s in statuses if s in allowed]
        if statuses:
            appts = appts.filter(status__in=statuses)

    if _truthy_query_param(request.query_params.get('upcoming')):
        appts = appts.filter(scheduled_datetime__gte=timezone.now()).exclude(status='CANCELLED')

    from_d = _parse_query_date(request.query_params.get('appointment_from'))
    to_d = _parse_query_date(request.query_params.get('appointment_to'))
    if from_d:
        appts = appts.filter(scheduled_datetime__date__gte=from_d)
    if to_d:
        appts = appts.filter(scheduled_datetime__date__lte=to_d)

    patient_ids = appts.values_list('patient_id', flat=True).distinct()
    patients = PatientProfile.objects.filter(id__in=patient_ids).select_related('user')

    search = (request.query_params.get('search') or request.query_params.get('q') or '').strip()
    if search:
        patients = patients.filter(
            Q(user__username__icontains=search)
            | Q(user__email__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(phone_number__icontains=search)
        )

    ordering = (request.query_params.get('ordering') or 'username').strip()
    order_map = {
        'username': 'user__username',
        '-username': '-user__username',
        'email': 'user__email',
        '-email': '-user__email',
        'id': 'id',
        '-id': '-id',
        'date_of_birth': 'date_of_birth',
        '-date_of_birth': '-date_of_birth',
    }
    patients = patients.order_by(order_map.get(ordering, 'user__username'))

    paginator = DoctorPatientListPagination()
    page = paginator.paginate_queryset(patients, request)
    serializer = DoctorPatientListSerializer(page, many=True, context={'doctor': doctor})
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_logged_in_doctor_patient_detail(request, patient_id):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    patient = get_object_or_404(PatientProfile, pk=patient_id)
    if not Appointment.objects.filter(doctor=doctor, patient=patient).exists():
        return Response({'message': 'not found'}, status=status.HTTP_404_NOT_FOUND)

    data = DoctorPatientDetailSerializer(patient, context={'doctor': doctor}).data
    return Response({'patient': data}, status=status.HTTP_200_OK)

