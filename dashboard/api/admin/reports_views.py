import csv
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from accounts.models import User, DoctorProfile, PatientProfile, ReceptionistProfile
from appointments.models import Appointment
from django.db.models import Q
import datetime
from accounts.apis.permissions import IsAdmin


class ReportsViewset(viewsets.ViewSet):
    """Reports for dashboard"""
    
    def generateCsvFile(self, file_name, columns, data):
        """helper function to make the httpResponse csv file."""
        
        response = HttpResponse(
            content_type = "text/csv",
            headers = {
                'Content-Disposition': f'attachment; filename="{file_name}"'
            },
        )
        
        writer = csv.writer(response)
        writer.writerow(columns)
        for record in data:
            writer.writerow(record)
            
        return response

    permission_classes = [IsAuthenticated, IsAdmin]
    @action(detail=False, methods=['get'])
    def users(self, request):
        """User List Report"""
        data = []
        columns = ["User Id", "User Name", "First Name", "Last Name", "Email", "Role", "Joining Date", "Is user active"]
        
        queryset = User.objects.all()
        
        role = request.query_params.get('role')
        if role:
            valid_roles = dict(User.ROLE_CHOICES)
            if role in valid_roles:
                queryset = queryset.filter(role = role)
                
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active = is_active_bool)
            
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter (
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(id__icontains=search) 
            )

        for user in queryset:
            data.append([
                user.id,
                user.username,
                user.first_name,
                user.last_name,
                user.email,
                user.get_role_display(),
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                'Yes' if user.is_active else 'No'
            ])

        return self.generateCsvFile(f"users_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", columns, data)

    @action(detail=False, methods=['get'])
    def doctors(self, request):
        """Doctor Directory Report"""

        data = []
        columns = ["Doctor ID", "Name", "Email", "Specialty", "Session Duration", "Buffer Time", "Active Status", "Date Joined", "Total Appointments"]

        queryset = DoctorProfile.objects.select_related('user').all()
        
        specialty = request.query_params.get('specialty')
        if specialty:
            queryset = queryset.filter(specialty=specialty)
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(user__is_active=is_active_bool)
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__id__icontains=search) |
                Q(user__email__icontains=search)
            )

        for doctor in queryset:
            total_appointments = Appointment.objects.filter(doctor=doctor).count()
            

            data.append([
                doctor.id,
                f"Dr. {doctor.user.first_name} {doctor.user.last_name}",
                doctor.user.email,
                doctor.get_specialty_display(),
                f"{doctor.session_duration} min",
                f"{doctor.buffer_time} min",
                'Yes' if doctor.user.is_active else 'No',
                doctor.user.date_joined.strftime('%Y-%m-%d'),
                total_appointments,
            ])

        return self.generateCsvFile(f"doctors_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", columns, data)

    @action(detail=False, methods=['get'])
    def patients(self, request):
        """Patient Directory Report"""

        data = []
        columns = ["Patient ID", "Name", "Email", "Phone", "Date of Birth", "Medical History", "Active Status", "Date Registered", "Total Appointments"]

        queryset = PatientProfile.objects.select_related('user').all()
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(user__is_active=is_active_bool)
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__id__icontains=search) |
                Q(phone_number__icontains=search)
            )

        for patient in queryset:
            total_appointments = Appointment.objects.filter(patient=patient).count()
            
            data.append([
                patient.id,
                f"{patient.user.first_name} {patient.user.last_name}",
                patient.user.email,
                patient.phone_number if patient.phone_number else 'N/A',
                patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else 'N/A',
                patient.medical_history if patient.medical_history else 'None',
                'Yes' if patient.user.is_active else 'No',
                patient.user.date_joined.strftime('%Y-%m-%d'),
                total_appointments
            ])

        return self.generateCsvFile(f"patients_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", columns, data)

    @action(detail=False, methods=['get'])
    def receptionists(self, request):
        """Receptionist List Report"""

        data = []
        columns = ["Receptionist ID", "Name", "Email", "Assigned Doctor", "Active Status", "Start Date"]

        queryset = ReceptionistProfile.objects.select_related('user', 'doctor__user').all()
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(user__is_active=is_active_bool)
        
        doctor_id = request.query_params.get('doctor_id')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__id__icontains=search) |
                Q(user__email__icontains=search)
            )

        for receptionist in queryset:
            data.append([
                receptionist.id,
                f"{receptionist.user.first_name} {receptionist.user.last_name}",
                receptionist.user.email,
                f"Dr. {receptionist.doctor.user.first_name} {receptionist.doctor.user.last_name}",
                'Yes' if receptionist.user.is_active else 'No',
                receptionist.user.date_joined.strftime('%Y-%m-%d')
            ])

        return self.generateCsvFile(f"receptionist_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", columns, data)

    @action(detail=False, methods=['get'])
    def appointments(self, request):
        """Appointments Report"""

        data = []
        columns = ["Appointment ID", "Patient Name", "Doctor Name", "Date & Time", "Status", "Type", "Duration", "Check-in Time", "Notes"]
        
        queryset = Appointment.objects.select_related('patient__user', 'doctor__user').all()
        
        status_param = request.query_params.get('status')
        if status_param:
            valid_statuses = dict(Appointment.STATUS_CHOICES)
            if status_param in valid_statuses:
                queryset = queryset.filter(status=status_param)
        
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        
        if from_date:
            try:
                from_date_obj = datetime.datetime.strptime(from_date, '%Y-%m-%d').date()
                queryset = queryset.filter(scheduled_datetime__date__gte=from_date_obj)
            except ValueError:
                pass
        
        if to_date:
            try:
                to_date_obj = datetime.datetime.strptime(to_date, '%Y-%m-%d').date()
                queryset = queryset.filter(scheduled_datetime__date__lte=to_date_obj)
            except ValueError:
                pass
        
        doctor_id = request.query_params.get('doctor_id')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        
        patient_id = request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        for appointment in queryset:
            duration = f"{appointment.doctor.session_duration} min"
            
            check_in_time = appointment.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if appointment.check_in_time else 'N/A'
            
            appt_type = 'Telemedicine' if appointment.is_telemedicine else 'In-Person'
            
            data.append([
                appointment.id,
                f"{appointment.patient.user.first_name} {appointment.patient.user.last_name}",
                f"Dr. {appointment.doctor.user.first_name} {appointment.doctor.user.last_name}",
                appointment.scheduled_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                appointment.get_status_display(),
                appt_type,
                duration,
                check_in_time,
                appointment.meeting_link if appointment.meeting_link else 'N/A'
            ])

        return self.generateCsvFile(f"appointments_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", columns, data)