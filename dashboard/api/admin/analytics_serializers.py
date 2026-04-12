from rest_framework import serializers

class UserAnalyticsSerializer(serializers.Serializer):
    """Serializer for user analytics"""
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    inactive_users = serializers.IntegerField()
    by_role = serializers.DictField()
    new_this_month = serializers.IntegerField()
    new_this_week = serializers.IntegerField()
    active_percentage = serializers.FloatField()


class DoctorAnalyticsSerializer(serializers.Serializer):
    """Serializer for doctor analytics"""
    total_doctors = serializers.IntegerField()
    total_with_schedule = serializers.IntegerField()
    by_specialty = serializers.DictField()
    session_duration_breakdown = serializers.DictField()


class PatientAnalyticsSerializer(serializers.Serializer):
    """Serializer for patient analytics"""
    total_patients = serializers.IntegerField()
    active_patients = serializers.IntegerField()
    patients_with_appointments = serializers.IntegerField()
    patients_with_completed_appointments = serializers.IntegerField()
    new_this_month = serializers.IntegerField()
    new_this_week = serializers.IntegerField()
    average_appointments_per_patient = serializers.FloatField()
    patients_with_consultations = serializers.IntegerField()
    patients_with_prescriptions = serializers.IntegerField()
    patients_with_test_requests = serializers.IntegerField()


class AppointmentAnalyticsSerializer(serializers.Serializer):
    """Serializer for appointment analytics"""
    total_appointments = serializers.IntegerField()
    by_status = serializers.DictField()
    today = serializers.IntegerField()
    this_week = serializers.IntegerField()
    this_month = serializers.IntegerField()
    telemedicine_count = serializers.IntegerField()
    in_person_count = serializers.IntegerField()
    completion_rate_percentage = serializers.FloatField()
    no_show_rate_percentage = serializers.FloatField()
    cancellation_rate_percentage = serializers.FloatField()


class ConsultationAnalyticsSerializer(serializers.Serializer):
    """Serializer for consultation analytics"""
    total_consultations = serializers.IntegerField()
    total_prescriptions = serializers.IntegerField()
    total_test_requests = serializers.IntegerField()
    average_prescription_items_per_consultation = serializers.FloatField()
    average_test_requests_per_consultation = serializers.FloatField()
    consultations_this_month = serializers.IntegerField()
    consultations_this_week = serializers.IntegerField()
    top_prescribed_tests = serializers.ListField()


class SchedulingAnalyticsSerializer(serializers.Serializer):
    """Serializer for scheduling analytics"""
    total_weekly_schedules = serializers.IntegerField()
    doctors_with_schedule = serializers.IntegerField()
    schedule_exceptions_today = serializers.IntegerField()
    doctors_off_today = serializers.IntegerField()
    average_working_hours_per_doctor = serializers.FloatField()
    by_day_of_week = serializers.DictField()


class AuditTrailAnalyticsSerializer(serializers.Serializer):
    """Serializer for appointment audit trail analytics"""
    total_rescheduled_appointments = serializers.IntegerField()
    reschedules_this_month = serializers.IntegerField()
    reschedules_this_week = serializers.IntegerField()
    top_reschedule_reasons = serializers.ListField()
    average_reschedules_per_appointment = serializers.FloatField()


class DashboardOverviewSerializer(serializers.Serializer):
    """Serializer for dashboard overview"""
    users = serializers.DictField()
    doctors = serializers.DictField()
    patients = serializers.DictField()
    appointments = serializers.DictField()
    consultations = serializers.DictField()
    telemedicine = serializers.DictField()
    key_metrics = serializers.DictField()