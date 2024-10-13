from django.urls import path, include
from rest_framework import routers

from accounts.views import ProfileViewSet, ConsultationsAccount, BookedAccountView, SignUp, VerifyEmail, \
    CustomTokenObtainPairView, CustomTokenRefreshView

router = routers.DefaultRouter()
router.register('profile', ProfileViewSet, basename='specialist')

urlpatterns = [
    path('', include(router.urls)),

    path('consultations/', ConsultationsAccount.as_view(), name='consultations'),
    path('bookeds/', BookedAccountView.as_view(), name='bookeds'),

    path('register/', SignUp.as_view(), name='signup'),
    path('email-verify/', VerifyEmail.as_view(), name="email_verify"),

    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='refresh'),
]
