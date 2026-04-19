import random
from datetime import datetime, timedelta, time

from django.contrib.auth.models import Group
from django.core.management.base import CommandError
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User, PatientProfile, DoctorProfile, ReceptionistProfile
from appointments.models import (
    Appointment,
    WeeklySchedule,
    ScheduleException,
    AppointmentAuditTrail,
)
from medical.models import ConsultationRecord, PrescriptionItem, TestRequest

ROLE_TO_GROUP_NAME = {
    'PATIENT': 'Patients',
    'DOCTOR': 'Doctors',
    'RECEPTIONIST': 'Receptionists',
    'ADMIN': 'Admins',
}

DRUGS = [
    ('Azithromycin', '250mg once daily', 5),
    ('Paracetamol', '500mg q6h PRN', 7),
    ('Amoxicillin', '500mg three times daily', 10),
    ('Omeprazole', '20mg once daily', 14),
    ('Metformin', '500mg twice daily', 30),
]
TESTS = ['CBC', 'Lipid Panel', 'HbA1c', 'Chest X-Ray', 'ECG', 'Liver Function']

DOCTOR_PIC_SUFFIX = '.jpg'


def doctor_profile_picture_path(username: str) -> str:
    return f'doctors/profile_pics/{username}{DOCTOR_PIC_SUFFIX}'


def assign_user_to_role_group(user):
    name = ROLE_TO_GROUP_NAME.get(user.role)
    if not name:
        return
    group, _ = Group.objects.get_or_create(name=name)
    user.groups.add(group)


class Command(BaseCommand):
    help = 'Seeds the database with a small, consistent clinic dataset (schedule-aware slots).'

    def handle(self, *args, **kwargs):
        self.stdout.write('Wiping seeded users and data (full user table reset)...')


        User.objects.all().delete()

        now = timezone.now()
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)
        project_tz = timezone.get_current_timezone()

        schedule_map = {}  
        exception_map = {} 
        slot_cache = {}  

        def _minutes_since_midnight(t: time) -> int:
            return int(t.hour) * 60 + int(t.minute)

        def _get_work_window(doctor_prof, target_date):
            """
            Return (start_time, end_time) for the day, considering WeeklySchedule and ScheduleException.
            If day is off / unscheduled -> (None, None)
            """
            dow = int(target_date.weekday())
            base = schedule_map.get(doctor_prof.id, {}).get(dow)
            if not base:
                return None, None
            start_t, end_t = base

            exc = exception_map.get(doctor_prof.id, {}).get(target_date)
            if not exc:
                return start_t, end_t

            is_day_off, exc_start, exc_end = exc
            if is_day_off:
                return None, None

            # Partial override window (if provided)
            if exc_start and exc_end:
                return exc_start, exc_end
            return start_t, end_t

        def doctor_day_slots(doctor_prof, target_date):
            """
            Build valid slot starts for a doctor on a specific date using their:
            - weekly schedule day window
            - schedule exceptions
            - step = session_duration + buffer_time
            Slots are generated so that session fits fully inside the work window.
            """
            key = (doctor_prof.id, target_date)
            if key in slot_cache:
                return slot_cache[key]

            start_t, end_t = _get_work_window(doctor_prof, target_date)
            if not start_t or not end_t:
                slot_cache[key] = []
                return []

            session_min = int(getattr(doctor_prof, 'session_duration', 0) or 0)
            buffer_min = int(getattr(doctor_prof, 'buffer_time', 0) or 0)
            step_min = max(session_min + buffer_min, 1)

            day_start_min = _minutes_since_midnight(start_t)
            day_end_min = _minutes_since_midnight(end_t)

            # last slot start so that [start, start+session] fits inside end
            last_start_min = day_end_min - max(session_min, 1)
            if last_start_min < day_start_min:
                slot_cache[key] = []
                return []

            slots = []
            # Align first slot at the schedule start (00 offset), then step by step_min
            cur = day_start_min
            while cur <= last_start_min:
                naive = datetime.combine(target_date, time(cur // 60, cur % 60))
                dt = timezone.make_aware(naive, project_tz)
                slots.append(dt)
                cur += step_min

            slot_cache[key] = slots
            return slots

        admin_user = User.objects.create_superuser(
            username='amir_admin',
            email='amir@clinic.com',
            password='password123',
            role='ADMIN',
        )
        assign_user_to_role_group(admin_user)

        u_doc = User.objects.create_user(
            username='amir_doc',
            email='amir.doc@clinic.com',
            password='password123',
            role='DOCTOR',
            first_name='Amir',
            last_name='Physician',
        )
        assign_user_to_role_group(u_doc)

        u_rec = User.objects.create_user(
            username='amir_rec',
            email='amir.rec@clinic.com',
            password='password123',
            role='RECEPTIONIST',
            first_name='Amir',
            last_name='Reception',
        )
        assign_user_to_role_group(u_rec)

        u_pat = User.objects.create_user(
            username='amir_pat',
            email='amir.pat@email.com',
            password='password123',
            role='PATIENT',
            first_name='Amir',
            last_name='Patient',
        )
        assign_user_to_role_group(u_pat)

        prof_amir_doc = DoctorProfile.objects.create(
            user=u_doc,
            specialty='GENERAL',
            session_duration=30,
            buffer_time=5,
            session_price=150,
        )
        DoctorProfile.objects.filter(pk=prof_amir_doc.pk).update(
            profile_picture=doctor_profile_picture_path(u_doc.username),
        )

        pat_amir = PatientProfile.objects.create(
            user=u_pat,
            date_of_birth='1992-06-01',
            phone_number='01010001000',
            medical_history='Primary demo patient — stress test account with full history.',
        )

        ReceptionistProfile.objects.create(user=u_rec, doctor=prof_amir_doc)

        extra_doctors_meta = [
            ('donia_doc', 'donia@clinic.com', 'Donia', 'Cardio', 'CARDIOLOGY', 'hager_rec', 'hager@clinic.com', 'Hager', 'Desk'),
            ('mohamed_doc', 'mohamed@clinic.com', 'Mohamed', 'General', 'GENERAL', 'ahmed_rec', 'ahmed@clinic.com', 'Ahmed', 'Front'),
            ('youssef_doc', 'youssef@clinic.com', 'Youssef', 'Skin', 'DERMATOLOGY', 'layla_rec', 'layla@clinic.com', 'Layla', 'Desk'),
            ('nour_doc', 'nour@clinic.com', 'Nour', 'Neuro', 'NEUROLOGY', 'omar_rec', 'omar@clinic.com', 'Omar', 'Front'),
            ('sara_doc', 'sara.doc@clinic.com', 'Sara', 'Kids', 'PEDIATRICS', 'mona_rec', 'mona@clinic.com', 'Mona', 'Desk'),
            ('khaled_doc', 'khaled.doc@clinic.com', 'Khaled', 'Ortho', 'ORTHOPEDICS', 'tarek_rec', 'tarek@clinic.com', 'Tarek', 'Front'),
            ('heba_doc', 'heba@clinic.com', 'Heba', 'GP', 'GENERAL', 'rana_rec', 'rana@clinic.com', 'Rana', 'Desk'),
            ('karim_doc', 'karim@clinic.com', 'Karim', 'Neuro', 'NEUROLOGY', 'yassin_rec', 'yassin@clinic.com', 'Yassin', 'Front'),
        ]

        doctor_profiles = [prof_amir_doc]

        for uname, email, fn, ln, spec, runame, remail, rfn, rln in extra_doctors_meta:
            du = User.objects.create_user(
                username=uname,
                email=email,
                password='password123',
                role='DOCTOR',
                first_name=fn,
                last_name=ln,
            )
            assign_user_to_role_group(du)
            dp = DoctorProfile.objects.create(
                user=du,
                specialty=spec,
                session_duration=30,
                buffer_time=5,
                session_price=random.choice([80, 100, 120]),
            )
            DoctorProfile.objects.filter(pk=dp.pk).update(
                profile_picture=doctor_profile_picture_path(du.username),
            )
            doctor_profiles.append(dp)

            ru = User.objects.create_user(
                username=runame,
                email=remail,
                password='password123',
                role='RECEPTIONIST',
                first_name=rfn,
                last_name=rln,
            )
            assign_user_to_role_group(ru)
            ReceptionistProfile.objects.create(user=ru, doctor=dp)

        patients = [pat_amir]
        for i in range(1, 55):
            u = User.objects.create_user(
                username=f'pat_{i:03d}',
                email=f'pat{i:03d}@seed.local',
                password='password123',
                role='PATIENT',
                first_name=f'Patient{i}',
                last_name='Demo',
            )
            assign_user_to_role_group(u)
            pp = PatientProfile.objects.create(
                user=u,
                date_of_birth=f'{1980 + (i % 30):04d}-{(i % 12) + 1:02d}-15',
                phone_number=f'0109{ i % 10:01d}{i % 10:01d}{i % 10:01d}{i % 10:01d}{i % 10:01d}{i % 10:01d}{i % 10:01d}{i % 10:01d}',
                medical_history='Seeded profile.' if i % 3 else '',
            )
            patients.append(pp)

        patients_other = [p for p in patients if p.pk != pat_amir.pk]

        for dp in doctor_profiles:
            for day in range(0, 5):
                WeeklySchedule.objects.create(
                    doctor=dp,
                    day_of_week=day,
                    start_time=time(8, 0),
                    end_time=time(18, 0),
                )
                schedule_map.setdefault(dp.id, {})[day] = (time(8, 0), time(18, 0))

        for day in (5, 6):  
            WeeklySchedule.objects.create(
                doctor=prof_amir_doc,
                day_of_week=day,
                start_time=time(8, 0),
                end_time=time(16, 0),
            )
            schedule_map.setdefault(prof_amir_doc.id, {})[day] = (time(8, 0), time(16, 0))

        ScheduleException.objects.create(
            doctor=doctor_profiles[1],
            date=yesterday,
            is_day_off=False,
            start_time=time(9, 0),
            end_time=time(13, 0),
        )
        exception_map.setdefault(doctor_profiles[1].id, {})[yesterday] = (False, time(9, 0), time(13, 0))
        ScheduleException.objects.create(
            doctor=doctor_profiles[3],
            date=today - timedelta(days=10),
            is_day_off=True,
        )
        exception_map.setdefault(doctor_profiles[3].id, {})[today - timedelta(days=10)] = (True, None, None)

        used_slots = {}

        def book_exact(doctor_prof, patient_prof, slot_dt, status, **extra):
            """Book a slot that must already be valid for the doctor/day (no shifting)."""
            key = doctor_prof.id
            used_slots.setdefault(key, set())
            s = slot_dt.replace(second=0, microsecond=0)
            d = timezone.localdate(s)
            valid = set(doctor_day_slots(doctor_prof, d))
            if s not in valid:
                raise CommandError(
                    f'Seed bug: slot {s.isoformat()} not valid for {doctor_prof.user.username} on {d}'
                )
            if s in used_slots[key]:
                raise CommandError(
                    f'Seed bug: duplicate slot for {doctor_prof.user.username} at {s.isoformat()}'
                )
            used_slots[key].add(s)
            return Appointment.objects.create(
                patient=patient_prof,
                doctor=doctor_prof,
                scheduled_datetime=s,
                status=status,
                **extra,
            )

        past_pairs = []
        for day_back in range(1, 14):
            if len(past_pairs) >= 5:
                break
            d = today - timedelta(days=day_back)
            slots = doctor_day_slots(prof_amir_doc, d)
            if slots:
                past_pairs.append((d, slots[0]))

        if len(past_pairs) < 5:
            raise CommandError('Could not find 5 schedulable past days for amir_doc; widen date range in seed.')

        for i, (_d, slot) in enumerate(past_pairs):
            pat = patients_other[i % len(patients_other)]
            if i < 4:
                ap = book_exact(prof_amir_doc, pat, slot, 'COMPLETED', check_in_time=slot - timedelta(minutes=10))
                cons = ConsultationRecord.objects.create(
                    appointment=ap,
                    diagnosis='Follow-up visit',
                    clinical_notes='Seeded consultation (compact seed).',
                )
                drug = DRUGS[i % len(DRUGS)]
                PrescriptionItem.objects.create(
                    consultation=cons,
                    drug_name=drug[0],
                    dose=drug[1],
                    duration_days=drug[2],
                )
                if i % 2 == 0:
                    TestRequest.objects.create(consultation=cons, test_name=TESTS[i % len(TESTS)])
            else:
                book_exact(prof_amir_doc, pat, slot, 'NO_SHOW')

        # 3 today: CHECKED_IN (queue), other patients only
        today_slots = doctor_day_slots(prof_amir_doc, today)
        if len(today_slots) < 3:
            raise CommandError('amir_doc needs at least 3 free slots today for CHECKED_IN queue rows.')
        for i in range(3):
            pat = patients_other[i % len(patients_other)]
            book_exact(
                prof_amir_doc,
                pat,
                today_slots[i],
                'CHECKED_IN',
                check_in_time=now - timedelta(minutes=5 * (3 - i)),
            )

        # 2 future: REQUESTED (pending)
        future_booked = 0
        for ahead in range(1, 21):
            if future_booked >= 2:
                break
            fd = today + timedelta(days=ahead)
            for slot in doctor_day_slots(prof_amir_doc, fd):
                if slot <= now:
                    continue
                pat = patients_other[(future_booked + 3) % len(patients_other)]
                book_exact(prof_amir_doc, pat, slot, 'REQUESTED')
                future_booked += 1
                if future_booked >= 2:
                    break

        if future_booked < 2:
            raise CommandError('Could not book 2 future REQUESTED appointments for amir_doc within date range.')

        # One audit trail on a past completed appointment (optional realism)
        past_completed = (
            Appointment.objects.filter(doctor=prof_amir_doc, status='COMPLETED')
            .order_by('-scheduled_datetime')
            .first()
        )
        if past_completed:
            AppointmentAuditTrail.objects.create(
                appointment=past_completed,
                old_datetime=past_completed.scheduled_datetime - timedelta(days=1),
                new_datetime=past_completed.scheduled_datetime,
                changed_by=u_rec,
                reason='Seeded reschedule note (compact).',
                action_type='RESCHEDULE',
                actor_role='RECEPTIONIST',
            )

        # --- Other doctors: minimal (1 completed yesterday each, on valid slots) ---
        for dp in doctor_profiles[1:]:
            p1 = patients[(dp.id % len(patients))]
            slots_y = doctor_day_slots(dp, yesterday)
            if not slots_y:
                continue
            a1 = book_exact(dp, p1, slots_y[0], 'COMPLETED', check_in_time=slots_y[0] - timedelta(minutes=8))
            cons = ConsultationRecord.objects.create(
                appointment=a1,
                diagnosis='Minor ailment',
                clinical_notes='Other doctor seed row (compact).',
            )
            PrescriptionItem.objects.create(consultation=cons, drug_name='Cetirizine', dose='10mg daily', duration_days=7)

        # --- Validation: ensure all appointments are valid schedule slots ---
        invalid = []
        for appt in Appointment.objects.select_related('doctor', 'doctor__user').all():
            doctor = appt.doctor
            dt = appt.scheduled_datetime
            d = timezone.localdate(dt)
            dt_norm = timezone.localtime(dt).replace(second=0, microsecond=0)
            valid = set(doctor_day_slots(doctor, d))
            if dt_norm not in valid:
                invalid.append(
                    (
                        appt.id,
                        doctor.user.username,
                        d.isoformat(),
                        dt.isoformat(),
                        doctor.session_duration,
                        doctor.buffer_time,
                    )
                )

        if invalid:
            sample = invalid[:10]
            raise CommandError(
                'Seed validation failed: some appointments are outside schedule or not aligned to '
                'session_duration + buffer_time.\n'
                f'Invalid count: {len(invalid)}. Sample (id, doctor, date, datetime, session, buffer): {sample}'
            )

        self.stdout.write(
            self.style.SUCCESS(
                '\n======================================================\n'
                'DATABASE SEEDED SUCCESSFULLY\n'
                'Primary test users: amir_doc | amir_rec | amir_pat | amir_admin\n'
                'Password (all seeded users): password123\n'
                'Doctor photos: add files under MEDIA_ROOT as doctors/profile_pics/<username>.jpg\n'
                '  e.g. amir_doc.jpg, donia_doc.jpg, mohamed_doc.jpg, … (see DOCTOR_PIC_SUFFIX in seed.py)\n'
                '======================================================'
            )
        )
