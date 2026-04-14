from datetime import datetime, timedelta

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.models import DoctorProfile, PatientProfile
from appointments.models import WeeklySchedule, ScheduleException, Appointment
from appointments.api.serializers import DoctorAppointmentDetailsSerializer, BookAppointmentSerializer
from rest_framework.permissions import IsAuthenticated , AllowAny
from accounts.apis.permissions import IsPatient, IsDoctor, IsAdmin, IsReceptionist
from dashboard.api.doctor.views import update_logged_in_doctor_appointment_status


def _parse_int(value, default):
    try:
        return int(value)
    except Exception:
        return default


def _date_range(now, request):
    range_value = (request.query_params.get('range') or '').strip().lower()
    if range_value == 'all':
        days = 90
    else:
        days = 14

    days = _parse_int(request.query_params.get('days'), days)
    if days < 1:
        days = 1
    if days > 365:
        days = 365

    start = now
    end = now + timedelta(days=days)
    return start, end


def _get_day_working_windows(doctor, day_date):
    exc = ScheduleException.objects.filter(doctor=doctor, date=day_date).first()
    if exc:
        if exc.is_day_off:
            return []
        if exc.start_time and exc.end_time:
            return [(exc.start_time, exc.end_time)]
        return []

    weekday = day_date.weekday()
    windows = []
    for ws in WeeklySchedule.objects.filter(doctor=doctor, day_of_week=weekday).order_by('start_time'):
        windows.append((ws.start_time, ws.end_time))
    return windows


def _is_datetime_in_doctor_availability(doctor, dt):
    day_date = timezone.localdate(dt)
    windows = _get_day_working_windows(doctor, day_date)
    if not windows:
        return False

    local_dt = timezone.localtime(dt)
    t = local_dt.time()
    duration_min = int(doctor.session_duration or 30)
    end_t = (local_dt + timedelta(minutes=duration_min)).time()

    for start_t, end_t_window in windows:
        if start_t <= t and end_t <= end_t_window:
            return True
    return False


def _get_logged_in_patient(request):
    try:
        if getattr(request.user, 'role', None) != 'PATIENT':
            return None
        return request.user.patient_profile
    except Exception:
        return None


def _parse_date(value):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except Exception:
        return None


def _day_bounds(day_date):
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(day_date, datetime.min.time()), tz)
    end = timezone.make_aware(datetime.combine(day_date, datetime.max.time()), tz)
    return start, end


def _generate_available_slots(doctor, range_start, range_end):
   
    booked = set(
        Appointment.objects.filter(
            doctor=doctor,
            scheduled_datetime__gte=range_start,
            scheduled_datetime__lte=range_end,
        )
        .exclude(status='CANCELLED')
        .values_list('scheduled_datetime', flat=True)
    )

    duration_min = int(doctor.session_duration or 30)
    buffer_min = int(doctor.buffer_time or 0)
    step_min = max(1, duration_min + buffer_min)

    slots = []
    current_day = timezone.localdate(range_start)
    end_day = timezone.localdate(range_end)
    tz = timezone.get_current_timezone()

    while current_day <= end_day:
        for start_t, end_t in _get_day_working_windows(doctor, current_day):
            day_start = timezone.make_aware(datetime.combine(current_day, start_t), tz)
            day_end = timezone.make_aware(datetime.combine(current_day, end_t), tz)

            cursor = day_start
            while cursor + timedelta(minutes=duration_min) <= day_end:
                if cursor >= range_start and cursor <= range_end and cursor > timezone.now():
                    if cursor not in booked:
                        slots.append(cursor)
                cursor = cursor + timedelta(minutes=step_min)

        current_day = current_day + timedelta(days=1)

    return slots


def _doctor_display_name(doctor):
    u = doctor.user
    fn = (u.first_name or '').strip()
    ln = (u.last_name or '').strip()
    if fn or ln:
        return f'Dr. {fn} {ln}'.strip()
    return f'Dr. {u.username}'


def _appointment_interval_end(appt):
    dur = int(appt.doctor.session_duration or 30)
    return appt.scheduled_datetime + timedelta(minutes=dur)


def _patient_active_same_doctor_appointment(patient, doctor, now):
    """
    Another visit with this doctor is not allowed while an existing appointment
    with this doctor is still upcoming or in progress (interval end > now).
    """
    qs = (
        Appointment.objects.filter(patient=patient, doctor=doctor)
        .exclude(status='CANCELLED')
        .select_related('doctor', 'doctor__user')
        .order_by('scheduled_datetime')
    )
    for appt in qs:
        if _appointment_interval_end(appt) > now:
            return appt
    return None


def _patient_has_overlapping_appointment(patient, start_dt, end_dt):
    """
    True if [start_dt, end_dt) overlaps any existing non-cancelled appointment
    interval (any doctor), using each doctor's session duration.
    Ignores visits that have already ended.
    """
    now = timezone.now()
    max_dur = timedelta(hours=6)
    qs = (
        Appointment.objects.filter(
            patient=patient,
            scheduled_datetime__lt=end_dt,
            scheduled_datetime__gt=start_dt - max_dur,
        )
        .exclude(status='CANCELLED')
        .select_related('doctor')
    )
    for appt in qs:
        appt_end = _appointment_interval_end(appt)
        if appt_end <= now:
            continue
        if start_dt < appt_end and end_dt > appt.scheduled_datetime:
            return True
    return False


def _patient_busy_intervals(patient, range_start, range_end):
    """Upcoming non-cancelled appointment intervals overlapping the requested window (any doctor)."""
    intervals = []
    now = timezone.now()
    qs = (
        Appointment.objects.filter(
            patient=patient,
            scheduled_datetime__lt=range_end,
        )
        .exclude(status='CANCELLED')
        .select_related('doctor', 'doctor__user')
        .order_by('scheduled_datetime')
    )
    for appt in qs:
        appt_end = _appointment_interval_end(appt)
        if appt_end <= now:
            continue
        if appt_end <= range_start or appt.scheduled_datetime >= range_end:
            continue
        intervals.append(
            {
                'scheduled_datetime': appt.scheduled_datetime,
                'ends_at': appt_end,
                'doctor_id': appt.doctor_id,
                'doctor_name': _doctor_display_name(appt.doctor),
            }
        )
    return intervals


def _filter_slots_for_patient(slots, patient, doctor, duration_min):
    """Remove slots that overlap the patient's other appointments (any doctor)."""
    if not slots:
        return []
    out = []
    for slot in slots:
        end_slot = slot + timedelta(minutes=duration_min)
        if not _patient_has_overlapping_appointment(patient, slot, end_slot):
            out.append(slot)
    return out


def _build_patient_booking_for_response(patient, doctor, slots, range_start, range_end, now):
    """Returns (filtered_available_slots, patient_booking_dict) for GET doctor details."""
    active_same = _patient_active_same_doctor_appointment(patient, doctor, now)
    if active_same:
        appt_end = _appointment_interval_end(active_same)
        pb = {
            'can_book_with_this_doctor': False,
            'same_doctor_block': {
                'active': True,
                'scheduled_datetime': active_same.scheduled_datetime,
                'ends_at': appt_end,
                'message': (
                    'You already have an upcoming or in-progress visit with this doctor. '
                    'You can book again after that appointment has finished.'
                ),
            },
            'busy_intervals': _patient_busy_intervals(patient, range_start, range_end),
        }
        return [], pb

    duration_min = int(doctor.session_duration or 30)
    filtered = _filter_slots_for_patient(slots, patient, doctor, duration_min)
    pb = {
        'can_book_with_this_doctor': True,
        'same_doctor_block': None,
        'busy_intervals': _patient_busy_intervals(patient, range_start, range_end),
    }
    return filtered, pb


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_appointment_details(request, id):
    is_doctor = IsDoctor().has_permission(request, None)
    is_receptionist = IsReceptionist().has_permission(request, None)
    is_patient = IsPatient().has_permission(request, None)
    if not (is_doctor or is_receptionist or is_patient):
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    if is_doctor:
        try:
            if request.user.doctor_profile.id != id:
                return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    elif is_receptionist:
        try:
            if request.user.receptionist_profile.doctor.id != id:
                return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    doctor = get_object_or_404(DoctorProfile.objects.select_related('user'), pk=id)

    now = timezone.now()

    selected_date = None
    date_q = (request.query_params.get('date') or '').strip()
    if date_q:
        selected_date = _parse_date(date_q)
        if not selected_date:
            return Response({'message': 'not valid', 'errors': {'date': ['Use YYYY-MM-DD']}}, status=status.HTTP_400_BAD_REQUEST)
        if selected_date < timezone.localdate(now):
            return Response({'message': 'not valid', 'errors': {'date': ['Date must be in the future']}}, status=status.HTTP_400_BAD_REQUEST)
        range_start, range_end = _day_bounds(selected_date)
    else:
        range_start, range_end = _date_range(now, request)

    available_slots = _generate_available_slots(doctor, range_start, range_end)

    patient_booking = None
    if is_patient:
        patient = _get_logged_in_patient(request)
        if patient:
            available_slots, patient_booking = _build_patient_booking_for_response(
                patient, doctor, available_slots, range_start, range_end, now
            )

    data = {
        'doctor': doctor,
        'weekly_schedules': WeeklySchedule.objects.filter(doctor=doctor).order_by('day_of_week', 'start_time'),
        'schedule_exceptions': ScheduleException.objects.filter(doctor=doctor, date__gte=timezone.localdate(now)).order_by('date'),
        'range_start': range_start,
        'range_end': range_end,
        'selected_date': selected_date,
        'available_slots': available_slots,
        'session_duration': int(doctor.session_duration or 30),
        'buffer_time': int(doctor.buffer_time or 0),
        'patient_booking': patient_booking,
    }

    serializer = DoctorAppointmentDetailsSerializer(instance=data)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated , IsPatient])
def book_appointment(request, doctor_id):
    patient = _get_logged_in_patient(request)
    if not patient:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    ser = BookAppointmentSerializer(data=request.data)
    if not ser.is_valid():
        return Response({'message': 'not valid', 'errors': ser.errors}, status=status.HTTP_400_BAD_REQUEST)

    scheduled_dt = ser.validated_data['scheduled_datetime']
    is_telemedicine = ser.validated_data.get('is_telemedicine', False)

    if timezone.is_naive(scheduled_dt):
        scheduled_dt = timezone.make_aware(scheduled_dt, timezone.get_current_timezone())

    if scheduled_dt <= timezone.now():
        return Response({'message': 'not valid', 'errors': {'scheduled_datetime': ['Must be in the future']}}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        doctor = get_object_or_404(DoctorProfile.objects.select_for_update(), pk=doctor_id)
        patient_locked = PatientProfile.objects.select_for_update().get(pk=patient.pk)

        if not _is_datetime_in_doctor_availability(doctor, scheduled_dt):
            return Response(
                {'message': 'not valid', 'errors': {'scheduled_datetime': ['Not in doctor availability']}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        duration_min = int(doctor.session_duration or 30)
        end_dt = scheduled_dt + timedelta(minutes=duration_min)
        now = timezone.now()

        if _patient_active_same_doctor_appointment(patient_locked, doctor, now):
            return Response(
                {
                    'message': 'not valid',
                    'code': 'same_doctor_pending',
                    'errors': {
                        'scheduled_datetime': [
                            'You already have an upcoming or in-progress visit with this doctor. '
                            'Wait until it finishes before booking another.'
                        ],
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if _patient_has_overlapping_appointment(patient_locked, scheduled_dt, end_dt):
            return Response(
                {
                    'message': 'not valid',
                    'code': 'time_overlap',
                    'errors': {
                        'scheduled_datetime': [
                            'This time overlaps another visit you already booked (including the full '
                            'session length). Choose a different time.'
                        ],
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Appointment.objects.filter(doctor=doctor, scheduled_datetime=scheduled_dt).exclude(status='CANCELLED').exists():
            return Response({'message': 'not valid', 'errors': {'scheduled_datetime': ['Slot already booked']}}, status=status.HTTP_400_BAD_REQUEST)

        try:
            appt = Appointment.objects.create(
                patient=patient_locked,
                doctor=doctor,
                scheduled_datetime=scheduled_dt,
                status='REQUESTED',
                is_telemedicine=is_telemedicine,
            )
        except IntegrityError:
            return Response({'message': 'not valid', 'errors': {'scheduled_datetime': ['Slot already booked']}}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            'message': 'appointment requested!',
            'appointment': {
                'id': appt.id,
                'doctor_id': doctor.id,
                'patient_id': patient.id,
                'scheduled_datetime': appt.scheduled_datetime,
                'status': appt.status,
                'is_telemedicine': appt.is_telemedicine,
                'meeting_link': appt.meeting_link,
            },
        },
        status=status.HTTP_201_CREATED,
    )



@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsDoctor])
def doctor_patch_appointment(request, appointment_id):
    return update_logged_in_doctor_appointment_status(request, appointment_id)


from appointments.api.serializers import (
    QueueSerializer,
    AppointmentListSerializer,
    AppointmentStatusUpdateSerializer,
)
from django.db.models import Q
@api_view(['GET'])
@permission_classes([IsReceptionist | IsDoctor])
def today_queue(request):
    
    today = timezone.localdate()

    try:
        if request.user.role == 'RECEPTIONIST':
            doctor = request.user.receptionist_profile.doctor
        else:
            doctor = request.user.doctor_profile

        appointments = Appointment.objects.filter(
            scheduled_datetime__date=today,
            doctor=doctor
        )
    except:
        appointments = Appointment.objects.filter(scheduled_datetime__date=today)
    
    appointments = appointments.exclude(
        status__in=['CANCELLED', 'NO_SHOW']
    ).select_related(
        'patient__user', 'doctor__user'
    ).order_by('check_in_time', 'scheduled_datetime')

    serializer = QueueSerializer(appointments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsReceptionist])
def appointment_list(request):

    try:
        doctor = request.user.receptionist_profile.doctor
        appointments = Appointment.objects.filter(doctor=doctor)
    except:
        appointments = Appointment.objects.all()

    appointments = appointments.select_related(
        'patient__user', 'doctor__user'
    ).order_by('-scheduled_datetime')

    status_filter  = request.query_params.get('status')
    date_filter    = request.query_params.get('date')
    doctor_filter  = request.query_params.get('doctor')
    search_query = request.query_params.get('search') or request.query_params.get('patient')

    if search_query:
        appointments = appointments.filter(
            Q(patient__user__username__icontains=search_query) |
            Q(patient__user__first_name__icontains=search_query) |
            Q(patient__user__last_name__icontains=search_query)
        )

    if status_filter:
        appointments = appointments.filter(status=status_filter.upper())
    if date_filter:
        appointments = appointments.filter(scheduled_datetime__date=date_filter)
    if doctor_filter:
        appointments = appointments.filter(doctor__id=doctor_filter)
    serializer = AppointmentListSerializer(appointments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsReceptionist | IsAdmin])
def update_appointment_status(request, appointment_id):
    
    appointment = get_object_or_404(Appointment, pk=appointment_id)

    serializer = AppointmentStatusUpdateSerializer(
        appointment,
        data=request.data,
        partial=True,
    )

    if serializer.is_valid():
        new_status = serializer.validated_data['status']

        if new_status == 'CHECKED_IN':
            appointment.check_in_time = timezone.now()

        serializer.save()

        return Response(
            {
                'message': f'Appointment status updated to {new_status}.',
                'appointment': AppointmentListSerializer(appointment).data,
            },
            status=status.HTTP_200_OK,
        )

    return Response(
        {'message': 'not valid', 'errors': serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )

