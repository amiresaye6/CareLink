from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, F, Case, When, IntegerField, Avg
from django.utils import timezone
from datetime import timedelta
from accounts.apis.permissions import IsAdmin

from accounts.models import User, PatientProfile, DoctorProfile
from appointments.models import Appointment, WeeklySchedule, ScheduleException, AppointmentAuditTrail
from medical.models import ConsultationRecord, PrescriptionItem, TestRequest

from .analytics_serializers import (
    UserAnalyticsSerializer,
    DoctorAnalyticsSerializer,
    PatientAnalyticsSerializer,
    AppointmentAnalyticsSerializer,
    ConsultationAnalyticsSerializer,
    SchedulingAnalyticsSerializer,
    AuditTrailAnalyticsSerializer,
    DashboardOverviewSerializer,
)


class AnalyticsViewSet(viewsets.ViewSet):
    """
    Analytics ViewSet for dashboard
    
    Endpoints:
    - GET /api/dashboard/admin/analytics/users/
    - GET /api/dashboard/admin/analytics/doctors/
    - GET /api/dashboard/admin/analytics/patients/
    - GET /api/dashboard/admin/analytics/appointments/
    - GET /api/dashboard/admin/analytics/consultations/
    - GET /api/dashboard/admin/analytics/scheduling/
    - GET /api/dashboard/admin/analytics/audit-trail/
    - GET /api/dashboard/admin/analytics/overview/
    
    Query Parameters:
    - ?doctor_id=5          -> Filter by specific doctor
    - ?specialty=CARDIOLOGY -> Filter by specialty
    """
    
    permission_classes = [IsAuthenticated, IsAdmin]
    
    @action(detail=False, methods=['get'])
    def users(self, request):
        """User analytics"""
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = User.objects.filter(is_active=False).count()
        
        by_role = dict(User.objects.values_list('role').annotate(count=Count('id')).values_list('role', 'count'))
        
        new_this_month = User.objects.filter(date_joined__date__gte=month_ago).count()
        new_this_week = User.objects.filter(date_joined__date__gte=week_ago).count()
        
        active_percentage = (active_users / total_users * 100) if total_users > 0 else 0.0
        
        data = {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'by_role': by_role,
            'new_this_month': new_this_month,
            'new_this_week': new_this_week,
            'active_percentage': round(active_percentage, 2)
        }
        
        serializer = UserAnalyticsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def doctors(self, request):
        """Doctor analytics"""
        
        doctor_id = request.query_params.get('doctor_id')
        
        doctors = DoctorProfile.objects.all()
        if doctor_id:
            doctors = doctors.filter(id=doctor_id)
        
        total_doctors = doctors.count()
        
        doctors_with_schedule = doctors.filter(weekly_schedules__isnull=False).distinct().count()
        
        by_specialty = dict(
            doctors.values_list('specialty').annotate(count=Count('id')).values_list('specialty', 'count')
        )
        
        session_breakdown = dict(
            doctors.values_list('session_duration').annotate(count=Count('id')).values_list('session_duration', 'count')
        )
        session_duration_breakdown = {
            f"{duration}_minutes": count 
            for duration, count in session_breakdown.items()
        }
        
        data = {
            'total_doctors': total_doctors,
            'total_with_schedule': doctors_with_schedule,
            'by_specialty': by_specialty,
            'session_duration_breakdown': session_duration_breakdown,
        }
        
        serializer = DoctorAnalyticsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def patients(self, request):
        """Patient analytics"""
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        patients = PatientProfile.objects.all()
        total_patients = patients.count()
        
        active_patients = patients.filter(user__is_active=True).count()
        
        patients_with_appointments = patients.filter(appointments__isnull=False).distinct().count()
        
        patients_with_completed = patients.filter(
            appointments__status='COMPLETED'
        ).distinct().count()
        
        new_this_month = patients.filter(user__date_joined__date__gte=month_ago).count()
        new_this_week = patients.filter(user__date_joined__date__gte=week_ago).count()
        
        total_appointments = Appointment.objects.filter(patient__in=patients).count()
        avg_appointments = (total_appointments / total_patients) if total_patients > 0 else 0.0
        
        patients_with_consultations = patients.filter(
            appointments__consultation__isnull=False
        ).distinct().count()
        
        patients_with_prescriptions = patients.filter(
            appointments__consultation__prescriptions__isnull=False
        ).distinct().count()
        
        patients_with_test_requests = patients.filter(
            appointments__consultation__tests__isnull=False
        ).distinct().count()
        
        data = {
            'total_patients': total_patients,
            'active_patients': active_patients,
            'patients_with_appointments': patients_with_appointments,
            'patients_with_completed_appointments': patients_with_completed,
            'new_this_month': new_this_month,
            'new_this_week': new_this_week,
            'average_appointments_per_patient': round(avg_appointments, 2),
            'patients_with_consultations': patients_with_consultations,
            'patients_with_prescriptions': patients_with_prescriptions,
            'patients_with_test_requests': patients_with_test_requests,
        }
        
        serializer = PatientAnalyticsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def appointments(self, request):
        """Appointment analytics"""
        
        doctor_id = request.query_params.get('doctor_id')
        
        appointments = Appointment.objects.all()
        if doctor_id:
            appointments = appointments.filter(doctor_id=doctor_id)
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        total_appointments = appointments.count()
        
        by_status = dict(
            appointments.values_list('status').annotate(count=Count('id')).values_list('status', 'count')
        )
        
        today_appointments = appointments.filter(scheduled_datetime__date=today).count()
        this_week = appointments.filter(scheduled_datetime__date__gte=week_ago).count()
        this_month = appointments.filter(scheduled_datetime__date__gte=month_ago).count()
        
        telemedicine_count = appointments.filter(is_telemedicine=True).count()
        in_person_count = appointments.filter(is_telemedicine=False).count()
        
        completed_count = appointments.filter(status='COMPLETED').count()
        cancelled_count = appointments.filter(status='CANCELLED').count()
        no_show_count = appointments.filter(status='NO_SHOW').count()
        
        completion_rate = (completed_count / total_appointments * 100) if total_appointments > 0 else 0.0
        no_show_rate = (no_show_count / total_appointments * 100) if total_appointments > 0 else 0.0
        cancellation_rate = (cancelled_count / total_appointments * 100) if total_appointments > 0 else 0.0
        
        data = {
            'total_appointments': total_appointments,
            'by_status': by_status,
            'today': today_appointments,
            'this_week': this_week,
            'this_month': this_month,
            'telemedicine_count': telemedicine_count,
            'in_person_count': in_person_count,
            'completion_rate_percentage': round(completion_rate, 2),
            'no_show_rate_percentage': round(no_show_rate, 2),
            'cancellation_rate_percentage': round(cancellation_rate, 2),
        }
        
        serializer = AppointmentAnalyticsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def consultations(self, request):
        """Consultation and EMR analytics"""
        
        doctor_id = request.query_params.get('doctor_id')
        
        consultations = ConsultationRecord.objects.all()
        if doctor_id:
            consultations = consultations.filter(appointment__doctor_id=doctor_id)
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        total_consultations = consultations.count()
        total_prescriptions = PrescriptionItem.objects.filter(
            consultation__in=consultations
        ).count()
        total_test_requests = TestRequest.objects.filter(
            consultation__in=consultations
        ).count()
        
        avg_prescriptions = (total_prescriptions / total_consultations) if total_consultations > 0 else 0.0
        avg_tests = (total_test_requests / total_consultations) if total_consultations > 0 else 0.0
        
        consultations_this_month = consultations.filter(created_at__date__gte=month_ago).count()
        consultations_this_week = consultations.filter(created_at__date__gte=week_ago).count()
        
        top_tests = TestRequest.objects.filter(
            consultation__in=consultations
        ).values_list('test_name').annotate(count=Count('id')).order_by('-count')[:5]
        
        top_prescribed_tests = [
            {'test_name': test[0], 'count': test[1]}
            for test in top_tests
        ]
        
        data = {
            'total_consultations': total_consultations,
            'total_prescriptions': total_prescriptions,
            'total_test_requests': total_test_requests,
            'average_prescription_items_per_consultation': round(avg_prescriptions, 2),
            'average_test_requests_per_consultation': round(avg_tests, 2),
            'consultations_this_month': consultations_this_month,
            'consultations_this_week': consultations_this_week,
            'top_prescribed_tests': top_prescribed_tests,
        }
        
        serializer = ConsultationAnalyticsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def scheduling(self, request):
        """Scheduling analytics"""
        
        doctor_id = request.query_params.get('doctor_id')
        
        schedules = WeeklySchedule.objects.all()
        exceptions = ScheduleException.objects.all()
        
        if doctor_id:
            schedules = schedules.filter(doctor_id=doctor_id)
            exceptions = exceptions.filter(doctor_id=doctor_id)
        
        today = timezone.now().date()
        
        total_schedules = schedules.count()
        doctors_with_schedule = schedules.values('doctor').distinct().count()
        

        exceptions_today = exceptions.filter(date=today).count()
        doctors_off_today = exceptions.filter(date=today, is_day_off=True).values('doctor').distinct().count()
        
        day_names = {0: 'MONDAY', 1: 'TUESDAY', 2: 'WEDNESDAY', 3: 'THURSDAY', 
                     4: 'FRIDAY', 5: 'SATURDAY', 6: 'SUNDAY'}
        by_day = dict(
            schedules.values_list('day_of_week').annotate(count=Count('id')).values_list('day_of_week', 'count')
        )
        by_day_of_week = {day_names.get(day, 'UNKNOWN'): count for day, count in by_day.items()}
        
        total_working_hours = 0
        for schedule in schedules:
            start = schedule.start_time
            end = schedule.end_time
            hours = (end.hour - start.hour) + (end.minute - start.minute) / 60
            total_working_hours += hours
        
        avg_working_hours = (total_working_hours / doctors_with_schedule) if doctors_with_schedule > 0 else 0.0
        
        data = {
            'total_weekly_schedules': total_schedules,
            'doctors_with_schedule': doctors_with_schedule,
            'schedule_exceptions_today': exceptions_today,
            'doctors_off_today': doctors_off_today,
            'average_working_hours_per_doctor': round(avg_working_hours, 2),
            'by_day_of_week': by_day_of_week,
        }
        
        serializer = SchedulingAnalyticsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def audit_trail(self, request):
        """Appointment audit trail analytics"""
        
        doctor_id = request.query_params.get('doctor_id')
        
        trails = AppointmentAuditTrail.objects.all()
        if doctor_id:
            trails = trails.filter(appointment__doctor_id=doctor_id)
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        total_rescheduled = trails.values('appointment').distinct().count()
        reschedules_this_month = trails.filter(timestamp__date__gte=month_ago).count()
        reschedules_this_week = trails.filter(timestamp__date__gte=week_ago).count()
        
        top_reasons = trails.values_list('reason').annotate(count=Count('id')).order_by('-count')[:5]
        top_reschedule_reasons = [
            {'reason': reason[0], 'count': reason[1]}
            for reason in top_reasons
        ]
        
        total_appointments = Appointment.objects.count()
        avg_reschedules = (total_rescheduled / total_appointments) if total_appointments > 0 else 0.0
        
        data = {
            'total_rescheduled_appointments': total_rescheduled,
            'reschedules_this_month': reschedules_this_month,
            'reschedules_this_week': reschedules_this_week,
            'top_reschedule_reasons': top_reschedule_reasons,
            'average_reschedules_per_appointment': round(avg_reschedules, 2),
        }
        
        serializer = AuditTrailAnalyticsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Dashboard overview - all key metrics"""
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = User.objects.filter(is_active=False).count()
        
        total_doctors = DoctorProfile.objects.count()
        doctors_with_schedule = DoctorProfile.objects.filter(
            weekly_schedules__isnull=False
        ).distinct().count()
        
        total_patients = PatientProfile.objects.count()
        active_patients = PatientProfile.objects.filter(user__is_active=True).count()
        
        total_appointments = Appointment.objects.count()
        today_appointments = Appointment.objects.filter(scheduled_datetime__date=today).count()
        pending_appointments = Appointment.objects.filter(status='REQUESTED').count()
        completed_appointments = Appointment.objects.filter(status='COMPLETED').count()
        cancelled_appointments = Appointment.objects.filter(status='CANCELLED').count()
        no_show_appointments = Appointment.objects.filter(status='NO_SHOW').count()
    
        total_consultations = ConsultationRecord.objects.count()
        consultations_this_month = ConsultationRecord.objects.filter(created_at__date__gte=month_ago).count()
        
        telemedicine_count = Appointment.objects.filter(is_telemedicine=True).count()
        telemedicine_percentage = (telemedicine_count / total_appointments * 100) if total_appointments > 0 else 0.0
        
        completion_rate = (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0.0
        no_show_rate = (no_show_appointments / total_appointments * 100) if total_appointments > 0 else 0.0
        cancellation_rate = (cancelled_appointments / total_appointments * 100) if total_appointments > 0 else 0.0
        
        data = {
            'users': {
                'total': total_users,
                'active': active_users,
                'inactive': inactive_users,
            },
            'doctors': {
                'total': total_doctors,
                'with_schedule': doctors_with_schedule,
            },
            'patients': {
                'total': total_patients,
                'active': active_patients,
            },
            'appointments': {
                'total': total_appointments,
                'today': today_appointments,
                'pending': pending_appointments,
                'completed': completed_appointments,
                'cancelled': cancelled_appointments,
                'no_show': no_show_appointments,
            },
            'consultations': {
                'total': total_consultations,
                'this_month': consultations_this_month,
            },
            'telemedicine': {
                'total': telemedicine_count,
                'percentage': round(telemedicine_percentage, 2),
            },
            'key_metrics': {
                'completion_rate': round(completion_rate, 2),
                'no_show_rate': round(no_show_rate, 2),
                'cancellation_rate': round(cancellation_rate, 2),
            }
        }
        
        serializer = DashboardOverviewSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)