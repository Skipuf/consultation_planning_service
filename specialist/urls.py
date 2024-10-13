from django.urls import path, include
from rest_framework import routers

from .views import CandidatesList, SpecialistList

router = routers.DefaultRouter()
router.register(r'specialist', SpecialistList, basename='specialist')
router.register(r'candidates', CandidatesList, basename='candidates')

urlpatterns = [
    path('', include(router.urls)),
]
