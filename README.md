# EduLead — Final Real-World CRM Structure

EduLead is a multi-office education consultancy CRM built with React, Django REST Framework, MySQL and scikit-learn.

## Roles

### Admin / CEO / CMO
Global access. No office is attached to this role.
- Total and office-wise revenue
- Expected revenue and expected admissions
- Projected profit
- Office conversion
- Manager performance
- Counsellor performance
- Source analytics

### Manager
Belongs to exactly one office.
- Sees only that office's leads
- Assigns leads only to counsellors from that office
- Views lead history
- Views office pipeline/revenue and source performance

### Counsellor
Belongs to exactly one office.
- Sees only assigned leads
- Adds remarks/contact history
- Updates lead status
- Schedules follow-ups
- Runs/views ML lead prediction

## Simple database

The project intentionally keeps the business database easy to explain:

1. `Office` — branch name, city, monthly expense
2. `Employee` — links Django User to role and office
3. `Lead` — enquiry details, office, manager, counsellor, expected fee
4. `LeadActivity` — complete lead history/remarks/status changes
5. `FollowUp` — reminders
6. `Admission` — successful admission and actual revenue
7. `Prediction` — ML probability, HIGH/MEDIUM/LOW priority and expected revenue

Django's built-in `auth_user` is used for secure usernames/passwords instead of building a duplicate login table.

## Revenue logic

- Actual Revenue = SUM of `Admission.revenue`
- Lead Expected Revenue = ML probability × `Lead.expected_fee`
- Expected Admissions = SUM of active lead probabilities
- Office Expected Additional Revenue = SUM of latest expected revenue for active leads in that office
- Projected Profit = Confirmed Revenue + Expected Additional Revenue − Office Monthly Expense

These are projections, not guaranteed business outcomes.

## ML logic

Logistic Regression predicts admission probability from:
- source
- country
- course
- academic score
- budget
- completed follow-ups
- activity count

Priority:
- HIGH: >= 70%
- MEDIUM: 40% to < 70%
- LOW: < 40%

Expected revenue for one lead:
`expected_fee × admission_probability / 100`

`ml/demo_training_data.csv` is only demonstration data. Before commercial use, train and validate the model on consented historical consultancy data and monitor accuracy/bias/drift.

## Signup and login

Signup asks for role and branch. Manager/Counsellor must select an office. Admin/CEO/CMO is global and therefore has no office.

For security, a public visitor cannot make themselves organization Admin merely by selecting ADMIN. Admin signup also requires `ADMIN_SIGNUP_CODE` from `.env`.

Login asks for username, password, role and office. The backend verifies that the selected role/office matches the employee account. Admin does not select an office.

## Run

### 1. MySQL

```sql
CREATE DATABASE edulead CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Backend

```bash
cd backend
python -m venv venv
```

Windows Git Bash:

```bash
source venv/Scripts/activate
```

Install and configure:

```bash
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations crm
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

### 3. Train demo ML model

From project root:

```bash
python ml/train_model.py
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Demo users

- Admin: `admin` / `Admin@123` (select Admin, no office)
- Pune Manager: `manager.pune` / `Manager@123` (select Pune Branch)
- Pune Counsellor: `counsellor.pune` / `Counsellor@123` (select Pune Branch)

## Important production hardening

Before using real student data: set `DEBUG=False`, use a strong secret, HTTPS, restricted hosts/CORS, managed MySQL, backups, MFA/admin invite workflow, audit logging, password policy, privacy/consent/retention rules, automated tests, rate limiting, monitoring and a production WSGI/ASGI server. The included signup flow is intentionally understandable for an academic project; a commercial deployment should normally use admin-created/invited employee accounts rather than unrestricted employee self-registration.


## Email-based authentication (final flow)
- Signup: employee enters email, password, role, and office (office is not required for Admin/CEO/CMO).
- Login: employee enters only email and password.
- Django reads the employee role and office from the database and React redirects to the correct dashboard automatically.
- The Django built-in username field is kept only internally and stores the same email value to avoid a custom user model.
- Home page: http://localhost:5173/

## Demo CRM data
Run `python manage.py seed_demo` to create presentation/demo records. The command creates 4 offices, managers/counsellors, 96 enquiries from Instagram, Facebook, Google Ads, Website, Walk-in, Referral and Direct Call, plus 28 demo admissions with revenue. Records are explicitly demo data and the command is designed to be safe to rerun.

Managers can create real/manual enquiries from **Manager → Leads → Add Lead**. The backend automatically attaches a manager-created lead to the manager's own office; the manager does not choose another office.


## Final stability fixes
- Manager-created leads get the logged-in manager's office automatically; the browser never supplies office.
- Manager-created leads are automatically linked to that manager.
- JWT access tokens are refreshed automatically using the stored refresh token.
- Refreshing a protected dashboard reloads `/api/me/` and then each page reloads its data from Django/MySQL.
- If both tokens are expired/invalid, the user is safely returned to login instead of seeing raw token errors.
- ML prediction falls back to the demo scoring method if an old joblib/scikit-learn artifact cannot be loaded; retraining in the backend environment remains recommended.

## Engagement & Automation Features (Oct 2026)

### 1. Counsellor call transcript
Counsellor Lead Details now contains **Call & Transcript**. `tel:` launches the device call handler and Chrome/Edge Web Speech API can capture microphone speech into an editable transcript. Saving creates a `CallTranscript` row. Managers can read transcripts for leads in their office.

**Important:** browser speech recognition cannot directly capture both sides of a PSTN/mobile phone call. For production two-sided automatic phone transcription, integrate a consent-aware telephony provider (for example Twilio) plus a speech-to-text service. The current implementation is a working browser-microphone prototype and stores transcripts in MySQL.

### 2. Virtual counselling meeting + calendar email
Counsellors can choose a date/time and schedule a virtual meeting. EduLead generates a unique Jitsi meeting URL, stores it in `Meeting`, and sends the student an email with an `.ics` calendar invitation. Development defaults to Django's console email backend. For real delivery set SMTP values in `backend/.env` (see `.env.example`).

### 3. Follow-up calendar/time + reminders
Counsellors use a native date/time picker. `FollowupReminder` checks pending follow-ups while the authenticated CRM is open and shows an in-app/browser notification 5 minutes before and at due time. Browser notification permission must be allowed. A production deployment that must notify even when the browser is closed should add a server-side scheduler such as Celery/Redis or a managed job service.

### 4. Bulk ML prediction
Manager Lead Management has **Run ML Predictions** and Counsellor My Leads has **Predict My Leads**. One request to `POST /api/leads/predict-all/` predicts every active visible lead (excluding ENROLLED and LOST), stores prediction rows, and refreshes the lead list/dashboard metrics. Role/office scoping still happens in Django.

### Database update required
Two new Django models were added: `CallTranscript` and `Meeting`. From `backend` run:

```bash
python manage.py makemigrations crm
python manage.py migrate
```

### Real email setup
Copy `.env.example` values into `.env` and set:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@example.com
```

Use an app password/provider credential rather than a normal mailbox password. Do not commit `.env`.
