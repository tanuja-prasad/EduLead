from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdmissionViewSet,
    CallTranscriptViewSet,
    EmployeeViewSet,
    FollowUpViewSet,
    LeadViewSet,
    MeetingViewSet,
    OfficeViewSet,
    dashboard,
    login,
    me,
    public_offices,
    signup,
)

router = DefaultRouter()
router.register("offices", OfficeViewSet, basename="office")
router.register("employees", EmployeeViewSet, basename="employee")
router.register("leads", LeadViewSet, basename="lead")
router.register("followups", FollowUpViewSet, basename="followup")
router.register("admissions", AdmissionViewSet, basename="admission")
router.register("call-transcripts", CallTranscriptViewSet, basename="call-transcript")
router.register("meetings", MeetingViewSet, basename="meeting")

urlpatterns = [
    path("auth/offices/", public_offices),
    path("auth/signup/", signup),
    path("auth/login/", login),
    path("me/", me),
    path("dashboard/", dashboard),
    path("", include(router.urls)),
]
