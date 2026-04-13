from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from accounts.apis.permissions import IsAdmin, IsDoctor, IsPatient, IsReceptionist, IsDoctorOrReceptionist
from datetime import datetime, timedelta

from django.db.models import Q, Count, Min, Exists, OuterRef
from django.shortcuts import get_object_or_404
from django.utils import timezone

from django.core.exceptions import ObjectDoesNotExist

from accounts.models import DoctorProfile, PatientProfile
from appointments.models import WeeklySchedule, ScheduleException, Appointment
from medical.models import ConsultationRecord
from dashboard.api.doctor.serializers import (
    DoctorProfileModelSerializer,
    WeeklyScheduleModelSerializer,
    WeeklyScheduleBulkSetSerializer,
    WEEKLY_DAYS_EXCEPT_FRIDAY,
    ScheduleExceptionModelSerializer,
    DoctorPatientListSerializer,
    DoctorPatientDetailSerializer,
    DoctorAppointmentListSerializer,
    DoctorAppointmentDetailSerializer,
    DoctorUpdateAppointmentStatusSerializer,
)



def _get_logged_in_doctor(request):
    try:
        return request.user.doctor_profile
    except Exception:
        return None


def _get_logged_in_receptionist_doctor(request):
    try:
        return request.user.receptionist_profile.doctor
    except Exception:
        return None


def _parse_int(value):
    try:
        return int(value)
    except Exception:
        return None


def _resolve_doctor_for_schedule(request):
    doctor_id = (
        request.query_params.get('doctor_id')
        or request.data.get('doctor_id')
        or request.query_params.get('doctor')
        or request.data.get('doctor')
    )
    doctor_id = _parse_int(doctor_id) if doctor_id is not None else None

    if IsDoctor().has_permission(request, None):
        doctor = _get_logged_in_doctor(request)
        if not doctor:
            return None
        if doctor_id is not None and doctor_id != doctor.id:
            return None
        return doctor

    if IsReceptionist().has_permission(request, None):
        assigned = _get_logged_in_receptionist_doctor(request)
        if not assigned:
            return None
        if doctor_id is None:
            return assigned
        if doctor_id != assigned.id:
            return None
        return assigned

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


def _consultation_record_complete(appointment):
    try:
        c = appointment.consultation
    except ObjectDoesNotExist:
        return False
    if not c.diagnosis or not str(c.diagnosis).strip():
        return False
    if not c.clinical_notes or not str(c.clinical_notes).strip():
        return False
    return True


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


class DoctorAppointmentListPagination(PageNumberPagination):
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
                'appointments': data,
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
@permission_classes([IsAuthenticated, IsDoctorOrReceptionist])
def get_logged_in_weekly_schedules(request):
    doctor = _resolve_doctor_for_schedule(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    schedules = WeeklySchedule.objects.filter(doctor=doctor).order_by('day_of_week', 'start_time')
    schedules = WeeklyScheduleModelSerializer(schedules, many=True)
    return Response(schedules.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsDoctorOrReceptionist])
def update_logged_in_weekly_schedule(request, id):
    doctor = _resolve_doctor_for_schedule(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    schedule = get_object_or_404(WeeklySchedule, pk=id, doctor=doctor)
    schedule = WeeklyScheduleModelSerializer(schedule, data=request.data, partial=True)
    if schedule.is_valid():
        schedule.save()
        return Response({'message': 'object updated!', 'schedule': schedule.data}, status=status.HTTP_200_OK)
    return Response({'message': 'not valid', 'errors': schedule.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsDoctorOrReceptionist])
def delete_logged_in_weekly_schedule(request, id):
    doctor = _resolve_doctor_for_schedule(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    schedule = get_object_or_404(WeeklySchedule, pk=id, doctor=doctor)
    schedule.delete()
    return Response({'message': 'object deleted!'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsDoctorOrReceptionist])
def create_logged_in_weekly_schedule(request):
    doctor = _resolve_doctor_for_schedule(request)
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
@permission_classes([IsAuthenticated, IsDoctorOrReceptionist])
def bulk_set_logged_in_weekly_schedules(request):
    doctor = _resolve_doctor_for_schedule(request)
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
@permission_classes([IsAuthenticated, IsDoctorOrReceptionist])
def bulk_delete_logged_in_weekly_schedules(request):
    doctor = _resolve_doctor_for_schedule(request)
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
@permission_classes([IsAuthenticated, IsDoctorOrReceptionist])
def get_logged_in_schedule_exceptions(request):
    doctor = _resolve_doctor_for_schedule(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    exc = ScheduleException.objects.filter(doctor=doctor).order_by('date')
    exc = ScheduleExceptionModelSerializer(exc, many=True)
    return Response(exc.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsDoctorOrReceptionist])
def create_logged_in_schedule_exception(request):
    doctor = _resolve_doctor_for_schedule(request)
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
@permission_classes([IsAuthenticated, IsDoctorOrReceptionist])
def update_logged_in_schedule_exception(request, id):
    doctor = _resolve_doctor_for_schedule(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    exc = get_object_or_404(ScheduleException, pk=id, doctor=doctor)
    exc = ScheduleExceptionModelSerializer(exc, data=request.data, partial=True)
    if exc.is_valid():
        exc.save()
        return Response({'message': 'object updated!', 'exception': exc.data}, status=status.HTTP_200_OK)
    return Response({'message': 'not valid', 'errors': exc.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsDoctorOrReceptionist])
def delete_logged_in_schedule_exception(request, id):
    doctor = _resolve_doctor_for_schedule(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    exc = get_object_or_404(ScheduleException, pk=id, doctor=doctor)
    exc.delete()
    return Response({'message': 'object deleted!'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated , IsDoctor])
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
@permission_classes([IsAuthenticated, IsDoctor])
def get_logged_in_doctor_patient_detail(request, patient_id):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    patient = get_object_or_404(PatientProfile, pk=patient_id)
    if not Appointment.objects.filter(doctor=doctor, patient=patient).exists():
        return Response({'message': 'not found'}, status=status.HTTP_404_NOT_FOUND)

    data = DoctorPatientDetailSerializer(patient, context={'doctor': doctor}).data
    return Response({'patient': data}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated , IsDoctor])
def get_logged_in_doctor_appointments(request):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    doc_param = (request.query_params.get('doctor') or '').strip()
    if doc_param:
        try:
            if int(doc_param) != doctor.id:
                return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
        except ValueError:
            return Response({'message': 'not valid', 'errors': {'doctor': ['Invalid doctor id']}}, status=status.HTTP_400_BAD_REQUEST)

    qs = (
        Appointment.objects.filter(doctor=doctor)
        .select_related('patient', 'patient__user')
        .annotate(
            has_consultation=Exists(
                ConsultationRecord.objects.filter(appointment_id=OuterRef('pk')),
            ),
        )
    )

    status_param = (request.query_params.get('status') or request.query_params.get('appointment_status') or '').strip()
    if status_param:
        statuses = [s.strip() for s in status_param.split(',') if s.strip()]
        allowed = {c[0] for c in Appointment.STATUS_CHOICES}
        statuses = [s for s in statuses if s in allowed]
        if statuses:
            qs = qs.filter(status__in=statuses)

    if _truthy_query_param(request.query_params.get('upcoming')):
        qs = qs.filter(scheduled_datetime__gte=timezone.now()).exclude(status='CANCELLED')

    if _truthy_query_param(request.query_params.get('past')):
        qs = qs.filter(scheduled_datetime__lt=timezone.now())

    if _truthy_query_param(request.query_params.get('is_telemedicine')):
        qs = qs.filter(is_telemedicine=True)
    elif (request.query_params.get('is_telemedicine') or '').strip().lower() in ('0', 'false', 'no'):
        qs = qs.filter(is_telemedicine=False)

    from_d = _parse_query_date(
        request.query_params.get('date_from')
        or request.query_params.get('scheduled_from')
        or request.query_params.get('appointment_from')
    )
    to_d = _parse_query_date(
        request.query_params.get('date_to')
        or request.query_params.get('scheduled_to')
        or request.query_params.get('appointment_to')
    )
    if from_d:
        qs = qs.filter(scheduled_datetime__date__gte=from_d)
    if to_d:
        qs = qs.filter(scheduled_datetime__date__lte=to_d)

    search = (request.query_params.get('search') or request.query_params.get('q') or '').strip()
    if search:
        if search.isdigit():
            qs = qs.filter(Q(id=int(search)) | Q(patient__user__username__icontains=search) | Q(patient__user__email__icontains=search) | Q(patient__user__first_name__icontains=search) | Q(patient__user__last_name__icontains=search) | Q(patient__phone_number__icontains=search))
        else:
            qs = qs.filter(
                Q(patient__user__username__icontains=search)
                | Q(patient__user__email__icontains=search)
                | Q(patient__user__first_name__icontains=search)
                | Q(patient__user__last_name__icontains=search)
                | Q(patient__phone_number__icontains=search)
            )

    ordering = (request.query_params.get('ordering') or '-scheduled_datetime').strip()
    order_map = {
        'scheduled_datetime': 'scheduled_datetime',
        '-scheduled_datetime': '-scheduled_datetime',
        'status': 'status',
        '-status': '-status',
        'id': 'id',
        '-id': '-id',
        'patient': 'patient__user__username',
        '-patient': '-patient__user__username',
        'patient__user__last_name': 'patient__user__last_name',
        '-patient__user__last_name': '-patient__user__last_name',
        'check_in_time': 'check_in_time',
        '-check_in_time': '-check_in_time',
    }
    qs = qs.order_by(order_map.get(ordering, '-scheduled_datetime'))

    paginator = DoctorAppointmentListPagination()
    page = paginator.paginate_queryset(qs, request)
    serializer = DoctorAppointmentListSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated , IsDoctor])
def get_logged_in_doctor_appointment_detail(request, appointment_id):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    appt = get_object_or_404(
        Appointment.objects.filter(doctor=doctor)
        .select_related('patient', 'patient__user', 'consultation')
        .prefetch_related('consultation__prescriptions', 'consultation__tests'),
        pk=appointment_id,
    )
    data = DoctorAppointmentDetailSerializer(appt).data
    return Response({'appointment': data}, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsDoctor])
def update_logged_in_doctor_appointment_status(request, appointment_id):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    appt = get_object_or_404(Appointment.objects.filter(doctor=doctor), pk=appointment_id)

    ser = DoctorUpdateAppointmentStatusSerializer(data=request.data, context={'appointment': appt})
    if not ser.is_valid():
        return Response({'message': 'not valid', 'errors': ser.errors}, status=status.HTTP_400_BAD_REQUEST)

    new_status = ser.validated_data['status']
    current = appt.status

    if new_status == current:
        return Response(
            {'message': 'not valid', 'errors': {'status': ['Already this status']}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    visit_cycle = {'CHECKED_IN', 'COMPLETED', 'NO_SHOW'}

    if current == 'REQUESTED':
        if new_status not in ('CONFIRMED', 'CANCELLED'):
            return Response(
                {
                    'message': 'not valid',
                    'errors': {
                        'status': [
                            'From REQUESTED: confirm (CONFIRMED) or decline (CANCELLED). '
                            'You cannot check in from here—reception sets CHECKED_IN after the visit is confirmed. '
                            'Or delete the request while it is still REQUESTED.',
                        ]
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
    elif current == 'CONFIRMED':
        if new_status not in ('NO_SHOW', 'REQUESTED'):
            return Response(
                {
                    'message': 'not valid',
                    'errors': {
                        'status': [
                            'From CONFIRMED: mark no-show (NO_SHOW), move back to requested (REQUESTED), '
                            'or wait for reception to check the patient in (CHECKED_IN).',
                        ]
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
    elif current in visit_cycle and new_status in visit_cycle:
        if new_status == 'COMPLETED':
            if not _consultation_record_complete(appt):
                return Response(
                    {
                        'message': 'not valid',
                        'errors': {'status': ['COMPLETED requires a completed consultation record (diagnosis and clinical notes)']},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
    else:
        return Response(
            {'message': 'not valid', 'errors': {'status': ['Cannot update status from this state']}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    appt.status = new_status
    appt.save(update_fields=['status'])
    data = DoctorAppointmentDetailSerializer(
        Appointment.objects.filter(doctor=doctor)
        .select_related('patient', 'patient__user', 'consultation')
        .prefetch_related('consultation__prescriptions', 'consultation__tests')
        .get(pk=appt.pk)
    ).data
    return Response({'message': 'object updated!', 'appointment': data}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsDoctor])
def delete_logged_in_doctor_appointment(request, appointment_id):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    appt = get_object_or_404(Appointment.objects.filter(doctor=doctor), pk=appointment_id)
    if appt.status != 'REQUESTED':
        return Response(
            {'message': 'not valid', 'errors': {'status': ['Delete is only allowed when status is REQUESTED']}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    appt.delete()
    return Response({'message': 'object deleted!'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDoctor])
def doctor_dashboard_stats(request):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    today = timezone.localdate()
    first_of_month = today.replace(day=1)

    base = Appointment.objects.filter(doctor=doctor)
    total_appointments = base.count()
    appointments_new_this_month = base.filter(scheduled_datetime__date__gte=first_of_month).count()

    patient_qs = base.values('patient_id').distinct()
    total_patients = patient_qs.count()

    first_appts = (
        Appointment.objects.filter(doctor=doctor)
        .values('patient_id')
        .annotate(first_dt=Min('scheduled_datetime'))
    )
    patients_new_this_month = sum(
        1 for row in first_appts if row['first_dt'] and timezone.localdate(row['first_dt']) >= first_of_month
    )

    completed_total = base.filter(status='COMPLETED').count()
    completed_today = base.filter(status='COMPLETED', scheduled_datetime__date=today).count()

    no_show_total = base.filter(status='NO_SHOW').count()
    denom = base.exclude(status='CANCELLED').count()
    no_show_rate = round((100.0 * no_show_total / denom), 1) if denom else 0.0

    checked_in_today_qs = base.filter(status='CHECKED_IN', scheduled_datetime__date=today)
    checked_in_today = checked_in_today_qs.count()
    now = timezone.now()
    wait_sum = 0.0
    wait_n = 0
    for appt in checked_in_today_qs.exclude(check_in_time__isnull=True):
        delta_sec = (now - appt.check_in_time).total_seconds()
        if delta_sec >= 0:
            wait_sum += delta_sec / 60.0
            wait_n += 1
    avg_wait_minutes_today = round(wait_sum / wait_n, 1) if wait_n else 0.0

    pending_requests = base.filter(status='REQUESTED').count()

    confirmed_today = base.filter(status='CONFIRMED', scheduled_datetime__date=today).count()
    waiting_now = checked_in_today

    return Response(
        {
            'total_appointments': total_appointments,
            'appointments_new_this_month': appointments_new_this_month,
            'total_patients': total_patients,
            'patients_new_this_month': patients_new_this_month,
            'completed_total': completed_total,
            'completed_today': completed_today,
            'no_show_total': no_show_total,
            'no_show_rate': no_show_rate,
            'avg_wait_minutes_today': avg_wait_minutes_today,
            'checked_in_today': checked_in_today,
            'pending_requests': pending_requests,
            'confirmed_today': confirmed_today,
            'currently_waiting': waiting_now,
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDoctor])
def doctor_appointments_over_time(request):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    period = (request.query_params.get('period') or '7d').strip().lower()
    days = {'7d': 7, '30d': 30, '90d': 90}.get(period, 7)
    today = timezone.localdate()
    points = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        c = Appointment.objects.filter(doctor=doctor, scheduled_datetime__date=d).count()
        if days <= 14:
            label = d.strftime('%a')
        else:
            label = d.strftime('%m/%d')
        points.append({'date': d.isoformat(), 'label': label, 'count': c})

    return Response({'period': period, 'points': points})


_STATUS_ORDER = (
    'COMPLETED',
    'CONFIRMED',
    'CHECKED_IN',
    'REQUESTED',
    'NO_SHOW',
    'CANCELLED',
)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDoctor])
def doctor_appointment_status_breakdown(request):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    rows = (
        Appointment.objects.filter(doctor=doctor)
        .values('status')
        .annotate(count=Count('id'))
    )
    count_by_status = {r['status']: r['count'] for r in rows}
    total = sum(count_by_status.values()) or 0
    segments = []
    if total:
        for st in _STATUS_ORDER:
            c = count_by_status.get(st, 0)
            if c:
                segments.append(
                    {
                        'status': st,
                        'count': c,
                        'percent': round(100.0 * c / total, 1),
                    }
                )
    return Response({'segments': segments, 'total': total})


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDoctor])
def doctor_queue_today(request):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    today = timezone.localdate()
    qs = (
        Appointment.objects.filter(doctor=doctor, status='CHECKED_IN', scheduled_datetime__date=today)
        .select_related('patient', 'patient__user')
        .exclude(check_in_time__isnull=True)
        .order_by('check_in_time')
    )
    now = timezone.now()
    items = []
    for appt in qs[:25]:
        user = appt.patient.user
        fn = (user.first_name or '').strip()
        ln = (user.last_name or '').strip()
        name = f'{fn} {ln}'.strip() or user.username
        initials = ''
        if fn and ln:
            initials = (fn[0] + ln[0]).upper()
        elif name:
            initials = name[:2].upper()
        wait_minutes = int((now - appt.check_in_time).total_seconds() // 60)
        if wait_minutes < 0:
            wait_minutes = 0
        items.append(
            {
                'id': appt.id,
                'patient_initials': initials,
                'patient_name': name,
                'scheduled_datetime': appt.scheduled_datetime,
                'wait_minutes': wait_minutes,
            }
        )
    return Response({'items': items})

