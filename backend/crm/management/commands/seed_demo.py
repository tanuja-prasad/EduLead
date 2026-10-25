"""Seed repeatable, fictional branch-specific CRM demo data.

Run: python manage.py seed_demo --dry-run
     python manage.py seed_demo
"""
import random
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from crm.models import Office, Employee, Lead, LeadActivity, FollowUp, Admission, Prediction

BRANCHES = [
    ('Pune', 'Maharashtra', 150, 5, 100, 350000),
    ('Mumbai', 'Maharashtra', 120, 4, 80, 450000),
    ('Bangalore', 'Karnataka', 100, 4, 65, 420000),
    ('Delhi', 'Delhi', 100, 4, 65, 400000),
]
FIRST = ['Aarav','Diya','Rohan','Ananya','Kabir','Ishita','Arjun','Meera','Vivaan','Sara','Aditya','Nisha','Rahul','Sneha','Kunal','Pooja','Siddharth','Neha','Yash','Aditi','Omkar','Riya','Harsh','Tanvi','Pranav','Kavya','Sahil','Priya','Atharva','Mahi']
LAST = ['Sharma','Patil','Mehta','Singh','Joshi','Shah','Nair','Kulkarni','Gupta','Khan','Rao','Verma','Deshmukh','Iyer','Jain','More','Roy','Kapoor','Bhosale','Menon','Pawar','Malhotra','Patel','Reddy']
COURSES = ['MBA','MSc Data Science','MSc Artificial Intelligence','MSc Computer Science','Business Analytics','Cyber Security','MCA','BTech Computer Science','BBA','MS Information Systems']
COUNTRIES = ['India','UK','USA','Germany','Canada','Australia','Ireland']
UNIVERSITIES = ['University of Manchester','University of Birmingham','University of Leeds','TU Berlin','University College Dublin','Monash University']
SOURCES = ['INSTAGRAM','FACEBOOK','GOOGLE','WEBSITE','WALKIN','DIRECT','REFERRAL']
STATUSES = ['NEW','CONTACTED','INTERESTED','COUNSELLING','APPLICATION','OFFER','ENROLLED','LOST']
NOTES = ['Discuss course eligibility and admission requirements','Share fee structure and scholarship options','Check documents and application progress','Review shortlisted universities','Confirm next counselling appointment','Discuss entrance test and academic profile']
PREFIX = 'edulead-showcase-2026'

class Command(BaseCommand):
    help = 'Add 470 fictional branch-specific leads, 310 follow-ups and realistic histories; safe to rerun.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Validate and show changes, then roll back')

    def handle(self, *args, **options):
        rng = random.Random(20261025)
        now = timezone.now()
        totals = {'offices': 0, 'employees': 0, 'leads': 0, 'followups': 0, 'admissions': 0, 'activities': 0, 'predictions': 0}
        try:
            with transaction.atomic():
                for branch_no, (city, state, count, counsellor_count, followup_count, expense) in enumerate(BRANCHES, start=1):
                    # Reuse an existing branch for this city instead of creating a second one.
                    city_aliases = ['Bangalore', 'Bengaluru'] if city == 'Bangalore' else [city]
                    candidates = list(Office.objects.filter(city__in=city_aliases).order_by('id'))
                    office = next((o for o in candidates if o.name.lower() == f'{city} branch'.lower()), candidates[0] if candidates else None)
                    if office is None:
                        office = Office.objects.create(name=f'{city} Branch', city=city, state=state, monthly_expense=expense, active=True)
                        totals['offices'] += 1
                    self.stdout.write(f'Office: {office.name} (ID {office.pk}, {office.city})')
                    manager = self._employee(f'{PREFIX}-manager-{city.lower()}@example.com', 'MANAGER', office, f'{city} Demo', 'Manager', totals)
                    counsellors = [self._employee(f'{PREFIX}-c{i+1}-{city.lower()}@example.com', 'COUNSELLOR', office, f'Demo {city}', f'Counsellor {i+1}', totals) for i in range(counsellor_count)]
                    for i in range(count):
                        # The email is a stable, unique marker; no existing real leads are overwritten.
                        email = f'{PREFIX}-b{branch_no}-lead{i+1:04d}@example.com'
                        if Lead.objects.filter(email=email).exists():
                            continue
                        status = STATUSES[(i * 5 + branch_no) % len(STATUSES)]
                        if i % 11 == 0:
                            status = 'ENROLLED'
                        counsellor = counsellors[i % len(counsellors)]
                        first = FIRST[(i * 7 + branch_no) % len(FIRST)]
                        last = LAST[(i * 11 + branch_no) % len(LAST)]
                        fee = Decimal(80000 + rng.randrange(0, 18) * 15000)
                        lead = Lead.objects.create(
                            office=office, student_name=f'{first} {last}',
                            phone=f'000{branch_no}{i+1:06d}', email=email,
                            source=SOURCES[i % len(SOURCES)], country=COUNTRIES[(i + branch_no) % len(COUNTRIES)],
                            course=COURSES[(i * 3 + branch_no) % len(COURSES)],
                            academic_score=round(55 + rng.random() * 42, 1),
                            budget=Decimal(400000 + rng.randrange(0, 25) * 100000), expected_fee=fee,
                            status=status, assigned_manager=manager, assigned_counsellor=counsellor,
                            created_by=manager.user,
                        )
                        created_at = now - timedelta(days=rng.randrange(0, 150), hours=rng.randrange(0, 24))
                        Lead.objects.filter(pk=lead.pk).update(created_at=created_at, updated_at=created_at)
                        totals['leads'] += 1
                        LeadActivity.objects.create(lead=lead, employee=manager, activity_type='CREATED', remark='Fictional showcase enquiry for CRM demonstration')
                        totals['activities'] += 1
                        if status not in ('NEW',):
                            LeadActivity.objects.create(lead=lead, employee=counsellor, activity_type='CALL', remark=NOTES[i % len(NOTES)])
                            totals['activities'] += 1
                        if status in ('APPLICATION','OFFER','ENROLLED'):
                            LeadActivity.objects.create(lead=lead, employee=counsellor, activity_type='STATUS', remark='Admission application progress updated', new_status=status)
                            totals['activities'] += 1
                        if status == 'ENROLLED':
                            Admission.objects.create(lead=lead, revenue=fee, university=UNIVERSITIES[i % len(UNIVERSITIES)], admitted_on=(now - timedelta(days=i % 85)).date())
                            totals['admissions'] += 1
                        # Deterministic sample probability for demo display, NOT an actual ML inference.
                        probability = {'NEW': .18, 'CONTACTED': .30, 'INTERESTED': .56, 'COUNSELLING': .64, 'APPLICATION': .76, 'OFFER': .90, 'ENROLLED': .99, 'LOST': .05}[status]
                        Prediction.objects.create(lead=lead, admission_probability=probability, priority='High' if probability >= .7 else ('Medium' if probability >= .4 else 'Low'), expected_revenue=fee * Decimal(str(probability)), model_version='demo-synthetic-v1')
                        totals['predictions'] += 1
                    # Attach follow-ups only to this command's records, and only once.
                    demo_leads = list(Lead.objects.filter(office=office, email__startswith=f'{PREFIX}-b{branch_no}-').exclude(status__in=['ENROLLED','LOST']).order_by('id'))
                    for j in range(followup_count):
                        lead = demo_leads[j % len(demo_leads)]
                        marker = f'[SHOWCASE-2026-{branch_no}-{j+1:03d}]'
                        if FollowUp.objects.filter(lead=lead, note__startswith=marker).exists():
                            continue
                        # Mix overdue, today and future reminders.
                        delta = (-10 + j % 22)
                        followup_time = now + timedelta(days=delta, hours=(j % 7) - 3)
                        FollowUp.objects.create(lead=lead, counsellor=lead.assigned_counsellor, followup_at=followup_time, note=f'{marker} {NOTES[j % len(NOTES)]}', completed=(delta < -3 and j % 3 == 0))
                        totals['followups'] += 1
                    self.stdout.write(f'{city}: {count} target demo enquiries, {followup_count} target follow-ups, {counsellor_count} counsellors')
                if options['dry_run']:
                    transaction.set_rollback(True)
                    self.stdout.write(self.style.WARNING('DRY RUN: all database changes rolled back.'))
                else:
                    self.stdout.write(self.style.SUCCESS('Demo data saved successfully.'))
                self.stdout.write('New records this run: ' + ', '.join(f'{k}={v}' for k,v in totals.items()))
        except Exception as exc:
            raise CommandError(f'Demo seeding failed; transaction rolled back: {exc}') from exc

    def _employee(self, email, role, office, first, last, totals):
        user, created = User.objects.get_or_create(username=email, defaults={'email': email, 'first_name': first, 'last_name': last, 'is_active': True})
        if created:
            user.set_unusable_password()  # Never ship predictable demo passwords to production.
            user.save(update_fields=['password'])
        employee, made = Employee.objects.get_or_create(user=user, defaults={'role': role, 'office': office, 'active': True})
        if not made and (employee.role != role or employee.office_id != office.id):
            raise CommandError(f'Existing demo account has conflicting role/office: {email}')
        totals['employees'] += int(made)
        return employee
