from django.urls import path, include
from rest_framework import routers

from .views import ConsultationList, BookedList

router = routers.DefaultRouter()
router.register(r'consultation', ConsultationList)
router.register(r'booked', BookedList)

urlpatterns = [
    path('', include(router.urls)),
]
