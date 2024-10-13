import jwt

from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from consultation_planning_service.utils import StandardResponseMixin, api_response, CacheResponseMixin
from consultations.models import Consultation, Booked
from specialist.permissions import IsAdmin
from .models import User
from .serializers import (
    AccountSerializer,
    BookedAccountSerializer,
    ConsultationAccountSerializer,
    EmailVerificationSerializer,
    SignUpSerializer
)
from .tasks import (
    task_send_email_verify_email_user_success,
    task_send_email_user_block,
    task_send_email_user_unblock
)


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class ProfileViewSet(StandardResponseMixin, ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AccountSerializer

    name_prefix_cache = 'ProfileViewSet'

    def get_serializer(self, *args, **kwargs):
        """Метод для получения сериалайзера"""
        return self.serializer_class(*args, **kwargs)

    @swagger_auto_schema(
        operation_description="Получить данные текущего аккаунта"
    )
    def list(self, request, *args, **kwargs):
        """Обрабатывает запрос для текущего пользователя."""
        user = User.objects.get(id=request.user.id)
        serializer = self.get_serializer(user)
        return api_response(data=serializer.data)

    @swagger_auto_schema(
        operation_description="Получить данные аккаунта по id"
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        """Обрабатывает запрос для пользователя по id."""
        user = get_object_or_404(User, id=pk)
        serializer = self.get_serializer(user)
        return api_response(data=serializer.data)

    @swagger_auto_schema(
        operation_description="Заблокировать пользователя. (только для админов)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_STRING, description='id пользователя'),
            }
        ),
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def block(self, request):
        self.check_permissions(request)

        user = get_object_or_404(User, id=request.data.get('id'))
        if user.is_active:
            user.block()
            task_send_email_user_block.delay(user.id)

            consultations = Consultation.objects.filter(user=user, archive=False)
            for consultation in consultations:
                consultation.cancelled('Автор консультации заблокирован.')

        return api_response(data={'user': 'Пользователь успешно заблокирован.'})

    @swagger_auto_schema(
        operation_description="Разблокировать пользователя. (только для админов)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_STRING, description='id пользователя'),
            }
        ),
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def unblock(self, request):
        self.check_permissions(request)

        user = get_object_or_404(User, id=request.data.get('id'))
        if not user.is_active:
            user.unblock()
            task_send_email_user_unblock.delay(user.id)

        return api_response(data={'user': 'Пользователь успешно разблокирован.'})


class ConsultationsAccount(CacheResponseMixin, StandardResponseMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConsultationAccountSerializer
    pagination_class = CustomPagination

    name_prefix_cache = 'ConsultationsAccount'

    @swagger_auto_schema(
        operation_description="Получить данные о своих консультацях (только для специалистов)",
    )
    def get(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='specialist').exists():
            return api_response(errors={'specialist': "Вы не являетесь специалистом."},
                                http_status=status.HTTP_403_FORBIDDEN,
                                status='error')

        consultations = Consultation.objects.filter(archive=False).order_by('datetime')

        self.check_object_permissions(request, request.user)

        page = self.paginate_queryset(consultations)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return api_response(data=result.data)

        serializer = self.get_serializer(consultations, many=True)
        return api_response(data=serializer.data)


class BookedAccountView(CacheResponseMixin, StandardResponseMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookedAccountSerializer
    pagination_class = CustomPagination

    name_prefix_cache = 'BookedAccountView'

    @swagger_auto_schema(
        operation_description="Получить данные о своих бронированиях.",
    )
    def get(self, request, *args, **kwargs):
        booked = Booked.objects.filter(archive=False).order_by('consultation__datetime')

        self.check_object_permissions(request, request.user)

        page = self.paginate_queryset(booked)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return api_response(data=result.data)

        serializer = self.get_serializer(booked, many=True)
        return api_response(data=serializer.data)


class SignUp(StandardResponseMixin, GenericAPIView):
    serializer_class = SignUpSerializer

    @swagger_auto_schema(
        operation_description="Регистрция нового пользователя.",
        request_body=SignUpSerializer
    )
    def post(self, request):
        data = request.data
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user = serializer.data
        return Response(user, status=status.HTTP_201_CREATED)


class VerifyEmail(StandardResponseMixin, GenericAPIView):
    serializer_class = EmailVerificationSerializer

    @swagger_auto_schema(
        operation_description="Подтверждение email пользователя.",
        manual_parameters=[
            openapi.Parameter(
                'token',
                openapi.IN_QUERY,
                description="Токен, необходимый для подтверждения email.",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    )
    def get(self, request):
        token = request.GET.get('token')
        try:
            payload = jwt.decode(token, options={"verify_signature": False})

            user = User.objects.get(id=payload['user_id'])
            if not user.is_verified:
                user.confirm_email()
                task_send_email_verify_email_user_success.delay(user.id)
            return api_response(data={'email': 'Успешно активирован'})
        except jwt.ExpiredSignatureError:
            return api_response(errors={'token': 'Срок действия активации истек'},
                                http_status=status.HTTP_400_BAD_REQUEST,
                                status="error")
        except jwt.exceptions.DecodeError:
            return api_response(errors={'token': 'Недопустимый токен'},
                                http_status=status.HTTP_400_BAD_REQUEST,
                                status="error")


class CustomTokenObtainPairView(TokenObtainPairView):
    @swagger_auto_schema(
        operation_description="Авторизация пользователя.",
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(email=request.data.get('email'))
            if not user.is_verified:
                return api_response(
                    errors={
                        "is_verified": 'Почта не подтверждена.',
                    },
                    http_status=status.HTTP_403_FORBIDDEN,
                    status='error'
                )

            tokens = response.data

            return api_response(
                data={
                    "refresh": tokens.get("refresh"),
                    "access": tokens.get("access"),
                },
            )
        return response


class CustomTokenRefreshView(TokenRefreshView):
    @swagger_auto_schema(
        operation_description="Refresh токена пользователя.",
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            tokens = response.data

            return api_response(
                data={"access": tokens.get("access")}
            )
        return response
