from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from accounts.apis.permissions import IsAdmin, IsDoctor
from django.shortcuts import get_object_or_404

from accounts.models import DoctorProfile
from appointments.models import WeeklySchedule, ScheduleException
from dashboard.api.doctor.serializers import (
    DoctorProfileModelSerializer,
    WeeklyScheduleModelSerializer,
    WeeklyScheduleBulkSetSerializer,
    WEEKLY_DAYS_EXCEPT_FRIDAY,
    ScheduleExceptionModelSerializer,
)



def _get_logged_in_doctor(request):
    try:
        return request.user.doctor_profile
    except Exception:
        return None


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

