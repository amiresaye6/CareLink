import csv
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.models import User
from django.db.models import Q
import datetime
from datetime import time
from datetime import timezone


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

    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def users(self, request):
        """User List Report"""
        data = []
        columns = [ "User Id", "User Name", "First Name", "Last Name", "Email", "Role", "Joining Date", "Is user active"]
        
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
                Q(last_name__icontains=search)
            )

        for user in queryset:
            data.append([
                user.id,
                user.username,
                user.first_name,
                user.last_name,
                user.email,
                user.get_role_display(),
                user.date_joined,
                user.is_active
                
            ])

        return self.generateCsvFile(f"users_report_{datetime.datetime.now()}_.csv", columns, data)

    @action(detail=False, methods=['get'])
    def doctors(self, request):
        """Doctor Directory Report"""

        data = []
        columns = [ "Doctor ID", "Name", "Email", "Specialty", "Session Duration", "Buffer Time", "Active Status", "Date Joined", "Total Appointments", "Average Rating" ]

        queryset = [{"cond": "to be done!!!"}]

        for record in queryset:
            data.append([
               record["cond"]
            ])

        return self.generateCsvFile(f"doctors_report_{datetime.datetime.now()}_.csv", columns, data)

    @action(detail=False, methods=['get'])
    def patients(self, request):
        """Patient Directory Report"""

        data = []
        columns = [ "Patient ID", "Name", "Email", "Phone", "Date of Birth", "Medical History", "Active Status", "Date Registered", "Total Appointments" ]

        queryset = [{"cond": "to be done!!!"}]

        for record in queryset:
            data.append([
               record["cond"]
            ])

        return self.generateCsvFile(f"patients_report_{datetime.datetime.now()}_.csv", columns, data)

    @action(detail=False, methods=['get'])
    def receptionists(self, request):
        """Receptionist List Report"""

        data = []
        columns = [ "Receptionist ID", "Name", "Email", "Assigned Doctor", "Active Status", "Start Date" ]

        queryset = [{"cond": "to be done!!!"}]

        for record in queryset:
            data.append([
               record["cond"]
            ])

        return self.generateCsvFile(f"receptionist_report_{datetime.datetime.now()}_.csv", columns, data)

    @action(detail=False, methods=['get'])
    def appointments(self, request):
        """Appointments Report"""

        data = []
        columns = [ "Appointment ID", "Patient Name", "Doctor Name", "Date & Time", "Status", "Type", "Duration", "Check-in Time", "Notes" ]
        # filterable by status, date range
        queryset = [{"cond": "to be done!!!"}]

        for record in queryset:
            data.append([
               record["cond"]
            ])

        return self.generateCsvFile(f"appointments_report_{datetime.datetime.now()}_.csv", columns, data)
