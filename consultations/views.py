from datetime import datetime as dt

from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from celery import current_app

from consultation_planning_service.utils import StandardResponseMixin, api_response, CacheResponseMixin
from .filters import ConsultationFilter, BookedFilter
from .models import Consultation, Booked
from .permissions import (
    IsOwnerOrReadOnly,
    IsInSpecialistGroupOrReadOnly,
    IsOwner,
    IsConsultationAuthor,
    IsConsultationAuthorOrBookingAuthor
)
from .serializers import ConsultationSerializer, BookedSerializer
from .tasks import archive_consultation


# Create your views here.
class ConsultationList(CacheResponseMixin, StandardResponseMixin, ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsInSpecialistGroupOrReadOnly]
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer

    name_prefix_cache = 'ConsultationList'

    # Поддержка фильтрации и сортировки
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = ConsultationFilter

    # Поля для сортировки
    ordering_fields = ['datetime', 'price']
    ordering = ['datetime']

    # Поиск по имени пользователя
    search_fields = ['user__username']

    http_method_names = ['get', 'post', 'patch']

    def perform_create(self, serializer):
        consultation = serializer.save(user=self.request.user)

        end_time = consultation.datetime.lower.replace(tzinfo=None)
        delay = (end_time - dt.now()).total_seconds()
        task = archive_consultation.apply_async((consultation.id,), countdown=delay)

        consultation.celery_task_id = task.id
        consultation.save()

    def perform_update(self, serializer):
        consultation = serializer.save()

        if consultation.celery_task_id:
            current_app.control.revoke(consultation.celery_task_id, terminate=True)

        end_time = consultation.datetime.lower.replace(tzinfo=None)
        delay = (end_time - dt.now()).total_seconds()
        task = archive_consultation.apply_async((consultation.id,), countdown=delay)

        consultation.celery_task_id = task.id
        consultation.save()

    @swagger_auto_schema(
        operation_description="Получить список консультаций с поддержкой фильтрации, сортировки и поиска.",
        manual_parameters=[
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Номер страницы для пагинации",
                type=openapi.TYPE_INTEGER,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """
        Получить список консультаций.
        """
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Создать новую консультацию.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['time_selection', 'datetime'],
            properties={
                'time_selection': openapi.Schema(type=openapi.TYPE_STRING,
                                                 description='Продолжительность консультации — от 1 до 3 часов'),
                'datetime': openapi.Schema(type=openapi.TYPE_STRING,
                                           description='Время начала в формате: 2025-09-25 18:00'),
                'description': openapi.Schema(type=openapi.TYPE_STRING,
                                              description='Описание.'),
            }
        ),
    )
    def create(self, request, *args, **kwargs):
        """
        Создать новую консультацию.
        """
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Получить консультацию по ID.",
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Получить консультацию по ID.
        """
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Обновить существующую консультацию.",
        request_body=ConsultationSerializer,
    )
    def partial_update(self, request, *args, **kwargs):
        """
        Обновить существующую консультацию.
        """
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Отменить консультацию (только автор консультации)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id', 'rejection_text'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_STRING, description='id консультации'),
                'rejection_text': openapi.Schema(type=openapi.TYPE_STRING, description='Причина отмены'),
            }
        ),
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsOwner])
    def cancellation(self, request):
        data = request.data

        consultation = get_object_or_404(Consultation, pk=data.get('id'))

        if consultation.archive:
            return api_response(errors={'detail': 'Нельзя отменить консультацию из архива.'},
                                http_status=status.HTTP_400_BAD_REQUEST,
                                status='error')

        self.check_object_permissions(request, consultation)

        serializer = self.get_serializer(Consultation, data=data, partial=True)

        rejection_text = request.data.get('rejection_text')
        serializer.validate_rejection_text(rejection_text)

        consultation.cancelled(rejection_text)

        return api_response(data={'detail': 'Консультация отклонена.',
                                  'rejection_text': rejection_text})


class BookedList(CacheResponseMixin, StandardResponseMixin, ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    queryset = Booked.objects.all()
    serializer_class = BookedSerializer

    name_prefix_cache = 'BookedList'

    # Добавляем поддержку фильтров и сортировки
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = BookedFilter

    # Поля для сортировки
    ordering_fields = ['consultation__datetime', 'status', 'archive']
    ordering = ['consultation__datetime']  # По умолчанию сортировка по дате начала консультации

    # Поиск по имени пользователя и владельца консультации
    search_fields = ['user__username', 'consultation__user__username']

    http_method_names = ['get', 'post', 'patch']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Получить список бронирования с поддержкой фильтрации, сортировки и поиска.",
        manual_parameters=[
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Номер страницы для пагинации",
                type=openapi.TYPE_INTEGER,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """
        Получить список бронирования.
        """
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Создать новую бронь.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['consultation'],
            properties={
                'consultation': openapi.Schema(type=openapi.TYPE_INTEGER,
                                               description='id консультации'),
                'description': openapi.Schema(type=openapi.TYPE_STRING,
                                              description='Описание.'),
            }
        ),
    )
    def create(self, request, *args, **kwargs):
        """
        Создать новую бронь.
        """
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Получить бронь по ID.",
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Получить бронь по ID.
        """
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Обновить существующую бронь.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['description'],
            properties={
                'description': openapi.Schema(type=openapi.TYPE_STRING,
                                              description='Описание.'),
            }
        ),
    )
    def partial_update(self, request, *args, **kwargs):
        """
        Обновить существующую бронь
        """
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Подтвердить бронь (только автор консультации)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_STRING, description='id бронирования'),
            }
        ),
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsConsultationAuthor])
    def accept(self, request):
        data = request.data

        booked = get_object_or_404(Booked, pk=data.get('id'))

        self.check_object_permissions(request, booked)

        booked.booked()

        return api_response(data={'detail': 'Консультация подтверждена.'})

    @swagger_auto_schema(
        operation_description="Отменить бронь (только автор консультации и автор бронирования)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id', 'rejection_text'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_STRING, description='id бронирования'),
                'rejection_text': openapi.Schema(type=openapi.TYPE_STRING, description='Причина отмены'),
            }
        ),
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsConsultationAuthorOrBookingAuthor])
    def cancellation(self, request):
        data = request.data

        booked = get_object_or_404(Booked, pk=data.get('id'))

        self.check_object_permissions(request, booked)

        serializer = self.get_serializer(booked, data=data, partial=True)

        rejection_text = request.data.get('rejection_text')
        serializer.validate_rejection_text(rejection_text)

        booked.cancelled(rejection_text)

        return api_response(data={'detail': 'Бронь отклонена.',
                                  'rejection_text': rejection_text})
