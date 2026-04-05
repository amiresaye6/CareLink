from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, time, datetime

# Import models across all apps (No Bonus Features)
from accounts.models import User, PatientProfile, DoctorProfile
from appointments.models import Appointment, WeeklySchedule, ScheduleException, AppointmentAuditTrail
from medical.models import ConsultationRecord, PrescriptionItem, TestRequest

class Command(BaseCommand):
    help = 'Seeds the database with core clinic data (No bonus features)'

    def handle(self, *args, **kwargs):
        self.stdout.write('Wiping old data and seeding fresh database...')

        # 1. Clear existing dummy data
        User.objects.exclude(is_superuser=True).delete()

        # 2. Setup Time References
        now = timezone.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)

        # Helper to make exact time slots (e.g., 09:00 AM) timezone aware
        def make_slot(target_date, hour, minute):
            return timezone.make_aware(datetime.combine(target_date, time(hour, minute)))

        # 3. Create Users
        admin_user = User.objects.create_superuser(username='amir_admin', email='amir@clinic.com', password='password123', role='ADMIN')
        doc_donia = User.objects.create_user(username='donia_doc', email='donia@clinic.com', password='password123', role='DOCTOR')
        doc_mohamed = User.objects.create_user(username='mohamed_doc', email='mohamed@clinic.com', password='password123', role='DOCTOR')
        rec_hager = User.objects.create_user(username='hager_rec', email='hager@clinic.com', password='password123', role='RECEPTIONIST')
        
        # We need multiple patients to test queues
        pat_amir_m = User.objects.create_user(username='amir_maula', email='amir.m@email.com', password='password123', role='PATIENT')
        pat_sara = User.objects.create_user(username='sara_smith', email='sara@email.com', password='password123', role='PATIENT')
        pat_khaled = User.objects.create_user(username='khaled_omar', email='khaled@email.com', password='password123', role='PATIENT')

        # 4. Create Profiles
        prof_donia = DoctorProfile.objects.create(user=doc_donia, specialty='Cardiology', session_duration=30)
        prof_mohamed = DoctorProfile.objects.create(user=doc_mohamed, specialty='General Practice', session_duration=15)
        
        prof_amir_m = PatientProfile.objects.create(user=pat_amir_m, date_of_birth='1995-08-15', phone_number='01011111111', medical_history='Mild asthma.')
        prof_sara = PatientProfile.objects.create(user=pat_sara, date_of_birth='1990-02-20', phone_number='01022222222')
        prof_khaled = PatientProfile.objects.create(user=pat_khaled, date_of_birth='1985-11-05', phone_number='01033333333', medical_history='Hypertension')

        # 5. Create Schedules & Exceptions
        # Donia works Monday(0) to Wednesday(2)
        for day in range(3):
            WeeklySchedule.objects.create(doctor=prof_donia, day_of_week=day, start_time=time(9, 0), end_time=time(17, 0))
        
        # Mohamed works Thursday(3) and Friday(4)
        WeeklySchedule.objects.create(doctor=prof_mohamed, day_of_week=3, start_time=time(10, 0), end_time=time(18, 0))
        WeeklySchedule.objects.create(doctor=prof_mohamed, day_of_week=4, start_time=time(10, 0), end_time=time(14, 0))

        # Exception: Donia takes tomorrow off
        ScheduleException.objects.create(doctor=prof_donia, date=tomorrow, is_day_off=True)

        # 6. Create Appointments (Hitting all lifecycle statuses)
        
        # A. Past Appointment -> COMPLETED
        app_past = Appointment.objects.create(
            patient=prof_amir_m, doctor=prof_donia, 
            scheduled_datetime=make_slot(yesterday, 10, 0),
            status='COMPLETED', check_in_time=make_slot(yesterday, 9, 50)
        )

        # B. Today's Appointment -> CHECKED_IN (Sitting in Hager's waiting room right now)
        app_today_1 = Appointment.objects.create(
            patient=prof_sara, doctor=prof_mohamed, 
            scheduled_datetime=make_slot(today, 11, 0),
            status='CHECKED_IN', check_in_time=now - timedelta(minutes=15)
        )

        # C. Today's Appointment -> NO_SHOW (Patient didn't arrive)
        Appointment.objects.create(
            patient=prof_khaled, doctor=prof_donia, 
            scheduled_datetime=make_slot(today, 9, 0),
            status='NO_SHOW'
        )

        # D. Future Appointment -> CONFIRMED (Also test Telemedicine)
        app_future = Appointment.objects.create(
            patient=prof_amir_m, doctor=prof_mohamed, 
            scheduled_datetime=make_slot(tomorrow, 12, 0),
            status='CONFIRMED', is_telemedicine=True, meeting_link='https://zoom.us/j/123456789'
        )

        # 7. Audit Trail (Simulate Hager rescheduling app_future from 10:00 to 12:00)
        AppointmentAuditTrail.objects.create(
            appointment=app_future,
            old_datetime=make_slot(tomorrow, 10, 0),
            new_datetime=make_slot(tomorrow, 12, 0),
            changed_by=rec_hager,
            reason="Patient called, stuck in traffic. Rescheduled to noon slot."
        )

        # 8. EMR Data (For the completed past appointment)
        consultation = ConsultationRecord.objects.create(
            appointment=app_past, diagnosis='Acute Bronchitis', 
            clinical_notes='Patient presented with mild cough and shortness of breath. Chest clear on auscultation.'
        )
        PrescriptionItem.objects.create(consultation=consultation, drug_name='Azithromycin', dose='250mg once daily', duration_days=5)
        PrescriptionItem.objects.create(consultation=consultation, drug_name='Albuterol Inhaler', dose='2 puffs q4-6h PRN', duration_days=14)
        TestRequest.objects.create(consultation=consultation, test_name='Chest X-Ray')

        self.stdout.write(self.style.SUCCESS(
            '\n======================================================\n'
            '🚀 DATABASE SEEDED SUCCESSFULLY!\n'
            'All lifecycle constraints, schedules, and audit trails generated.\n'
            'Universal Password for all users: password123\n'
            '======================================================'
        ))