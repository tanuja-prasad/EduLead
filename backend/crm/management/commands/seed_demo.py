from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from crm.models import Admission, Employee, Lead, LeadActivity, Office


class Command(BaseCommand):
    help = "Create realistic DEMO offices, employees, enquiries and admissions. Safe to run more than once."

    def handle(self, *args, **options):
        offices = {}
        office_specs = [
            ("Pune Branch", "Pune", "Maharashtra", 350000),
            ("Mumbai Branch", "Mumbai", "Maharashtra", 450000),
            ("Bangalore Branch", "Bangalore", "Karnataka", 420000),
            ("Delhi Branch", "Delhi", "Delhi", 400000),
        ]
        for name, city, state, expense in office_specs:
            office, _ = Office.objects.update_or_create(
                name=name,
                defaults={"city": city, "state": state, "monthly_expense": expense, "active": True},
            )
            offices[city] = office

        def make_employee(email, password, role, office=None, first_name="", last_name=""):
            user, _ = User.objects.get_or_create(username=email)
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.set_password(password)
            user.save()
            profile, _ = Employee.objects.update_or_create(
                user=user,
                defaults={"role": role, "office": office, "active": True},
            )
            return profile

        make_employee("admin@edulead.demo", "Admin@123", Employee.ADMIN, first_name="EduLead", last_name="Admin")
        teams = {}
        for city, office in offices.items():
            key = city.lower()
            manager = make_employee(
                f"manager.{key}@edulead.demo", "Manager@123", Employee.MANAGER, office,
                first_name=city, last_name="Manager",
            )
            counsellors = [
                make_employee(
                    f"counsellor1.{key}@edulead.demo", "Counsellor@123", Employee.COUNSELLOR, office,
                    first_name=f"{city} Counsellor", last_name="One",
                ),
                make_employee(
                    f"counsellor2.{key}@edulead.demo", "Counsellor@123", Employee.COUNSELLOR, office,
                    first_name=f"{city} Counsellor", last_name="Two",
                ),
            ]
            # Preserve the earlier convenient counsellor email as well.
            make_employee(
                f"counsellor.{key}@edulead.demo", "Counsellor@123", Employee.COUNSELLOR, office,
                first_name=f"{city} Demo", last_name="Counsellor",
            )
            teams[city] = (manager, counsellors)

        names = [
            "Aarav Sharma", "Diya Patil", "Rohan Mehta", "Ananya Singh", "Kabir Joshi", "Ishita Shah",
            "Arjun Nair", "Meera Kulkarni", "Vivaan Gupta", "Sara Khan", "Aditya Rao", "Nisha Verma",
            "Rahul Deshmukh", "Sneha Iyer", "Kunal Jain", "Pooja More", "Siddharth Roy", "Neha Kapoor",
            "Yash Bhosale", "Aditi Menon", "Omkar Pawar", "Riya Malhotra", "Harsh Patel", "Tanvi Reddy",
        ]
        sources = ["INSTAGRAM", "FACEBOOK", "WALKIN", "GOOGLE", "WEBSITE", "REFERRAL", "DIRECT", "INSTAGRAM"]
        countries = ["UK", "USA", "Germany", "Canada", "Australia", "Ireland"]
        courses = ["MSc Data Science", "MBA", "MSc Computer Science", "MSc AI", "Business Analytics", "Cyber Security"]
        statuses = ["NEW", "CONTACTED", "INTERESTED", "COUNSELLING", "APPLICATION", "OFFER", "LOST"]
        universities = ["University of Manchester", "University of Birmingham", "University of Leeds", "TU Berlin", "University College Dublin", "Monash University"]

        created = 0
        admission_count = 0
        total_revenue = Decimal("0")
        today = date.today()

        # 24 enquiries per office = 96 demo enquiries.
        # 7 admissions per office = 28 admissions, enough to make revenue dashboards meaningful.
        for office_index, (city, office) in enumerate(offices.items()):
            manager, counsellors = teams[city]
            for i in range(24):
                unique = office_index * 100 + i
                is_admitted = i < 7
                status = "ENROLLED" if is_admitted else statuses[(i + office_index) % len(statuses)]
                source = sources[(i + office_index) % len(sources)]
                phone = f"900{office_index}{i:06d}"[-10:]
                expected_fee = Decimal(str(90000 + ((i * 17000 + office_index * 12000) % 180000)))
                lead, was_created = Lead.objects.update_or_create(
                    phone=phone,
                    defaults={
                        "office": office,
                        "student_name": names[i % len(names)],
                        "email": f"demo.lead{unique}@example.com",
                        "source": source,
                        "country": countries[(i + office_index) % len(countries)],
                        "course": courses[(i * 2 + office_index) % len(courses)],
                        "academic_score": 62 + ((i * 3 + office_index) % 31),
                        "budget": 900000 + ((i * 125000) % 1800000),
                        "expected_fee": expected_fee,
                        "status": status,
                        "assigned_manager": manager,
                        "assigned_counsellor": counsellors[i % len(counsellors)],
                        "created_by": manager.user,
                    },
                )
                created += int(was_created)
                # Spread demo enquiries over the last ~5 months for realistic activity.
                Lead.objects.filter(pk=lead.pk).update(created_at=timezone.now() - timedelta(days=(i * 5 + office_index * 3) % 145))
                LeadActivity.objects.get_or_create(
                    lead=lead,
                    activity_type="CREATED",
                    remark="Demo enquiry imported for project presentation",
                    defaults={"employee": manager},
                )

                if is_admitted:
                    revenue = Decimal(str(125000 + ((i * 31000 + office_index * 19000) % 175000)))
                    admission, _ = Admission.objects.update_or_create(
                        lead=lead,
                        defaults={
                            "revenue": revenue,
                            "university": universities[(i + office_index) % len(universities)],
                            "admitted_on": today - timedelta(days=(i * 13 + office_index * 9) % 150),
                        },
                    )
                    admission_count += 1
                    total_revenue += admission.revenue

        self.stdout.write(self.style.SUCCESS(
            f"Demo data ready: {Lead.objects.count()} total leads, {admission_count} seeded admissions, "
            f"seeded admission revenue ₹{total_revenue:,.0f}. Newly created leads this run: {created}."
        ))
        self.stdout.write("Demo sources include Instagram, Facebook, Google Ads, Website, Walk-in, Referral and Direct Call.")
