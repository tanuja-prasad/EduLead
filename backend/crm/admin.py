from django.contrib import admin

from .models import Admission, Employee, FollowUp, Lead, LeadActivity, Office, Prediction

admin.site.register(Office)
admin.site.register(Employee)
admin.site.register(Lead)
admin.site.register(LeadActivity)
admin.site.register(FollowUp)
admin.site.register(Admission)
admin.site.register(Prediction)
