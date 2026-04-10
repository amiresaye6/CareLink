from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta, date, time
from accounts.models import DoctorProfile
from appointments.models import Appointment, ScheduleException, WeeklySchedule

# Create your views here.
