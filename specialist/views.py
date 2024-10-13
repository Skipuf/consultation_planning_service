from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from consultation_planning_service.utils import StandardResponseMixin, api_response, CacheResponseMixin
from specialist.models import Candidates, Specialist
from specialist.permissions import (
    IsAdmin,
    Only_a_patch_is_allowed_for_owners,
    we_accept_applications_from_everyone,
    IsOwner_or_IsAdmin
)
from specialist.serializers import CandidatesSerializer, SpecialistSerializer
from .tasks import (
    task_send_email_candidates_accept,
    task_send_email_candidates_cancel,
    task_send_email_specialist_block,
    task_send_email_specialist_unblock
)


class SpecialistList(CacheResponseMixin, StandardResponseMixin, ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdmin]
    permission_classes_by_action = {
        'partial_update': [IsAuthenticated, Only_a_patch_is_allowed_for_owners],
        'create': [IsAuthenticated, IsAdmin],
        'list': [IsAuthenticated, IsAdmin],
        'retrieve': [IsAuthenticated, IsAdmin],
    }
    queryset = Specialist.objects.all().order_by('user')
    serializer_class = SpecialistSerializer

    name_prefix_cache = 'SpecialistList'

    http_method_names = ['get', 'post', 'patch']

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user__username', 'is_active']
    ordering_fields = ['user', 'is_active']
    ordering = ['user']

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]

    def get_object(self):
        user_id = self.kwargs.get('pk')
        return get_object_or_404(Specialist, user_id=user_id)

    @swagger_auto_schema(
        operation_description="Получить список специалистов с поддержкой фильтрации, "
                              "сортировки и поиска. (только для админов)",
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
        Получить список специалистов. (только для админов)
        """
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Создание нового специалиста. В рамках данного проекта не применяется. "
                              "Чтобы корректно создать специалиста, "
                              "необходимо предварительно подать заявку через Candidates.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id', 'description'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_STRING,
                                     description='id пользователя(не специалиста).'),
                'description': openapi.Schema(type=openapi.TYPE_STRING,
                                              description='Описание профиля специалиста.')
            }
        ),
    )
    def create(self, request, *args, **kwargs):
        """
        Создание нового специалиста. В рамках данного проекта не применяется.
        Чтобы корректно создать специалиста,
        необходимо предварительно подать заявку через CandidatesList.
        """
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Получить специалиста по ID пользователя. (только для админов)",
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Получить специалиста по ID пользователя. (только для админов)
        """
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Обновить существующего специалиста. (только для админов и самого специалиста)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['description'],
            properties={
                'description': openapi.Schema(type=openapi.TYPE_STRING,
                                              description='Описание профиля специалиста.'),
            }
        ),
    )
    def partial_update(self, request, *args, **kwargs):
        """
        Обновить существующего специалиста. (только для админов и специалиста)
        """
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Заблокировать специалиста. (только для админов)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_STRING,
                                     description='id пользователя(не специалиста).'),
            }
        ),
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def block(self, request):
        """
        Заблокировать специалиста. (только для админов)
        """
        try:
            specialist = get_object_or_404(Specialist, user_id=request.data.get('id'))
            specialist.block()
            task_send_email_specialist_block.delay(specialist.id)
            return api_response(data={'status': 'Специалист заблокирован.'})
        except Specialist.DoesNotExist:
            return api_response(errors={'error': 'Специалист не найден.'},
                                http_status=status.HTTP_404_NOT_FOUND,
                                status="error")

    @swagger_auto_schema(
        operation_description="Разблокировать специалиста. (только для админов)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_STRING,
                                     description='id пользователя(не специалиста).'),
            }
        ),
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def unblock(self, request):
        """
        Разблокировать специалиста. (только для админов)
        """
        try:
            specialist = get_object_or_404(Specialist, user_id=request.data.get('id'))
            specialist.unblock()
            task_send_email_specialist_unblock.delay(specialist.id)
            return api_response(data={'status': 'Специалист разблокирован.'})
        except Specialist.DoesNotExist:
            return api_response(errors={'error': 'Специалист не найден.'},
                                http_status=status.HTTP_404_NOT_FOUND,
                                status="error")


class CandidatesList(CacheResponseMixin, StandardResponseMixin, ModelViewSet):
    permission_classes = [IsAuthenticated, we_accept_applications_from_everyone]
    queryset = Candidates.objects.all().order_by('user')
    serializer_class = CandidatesSerializer

    name_prefix_cache = 'CandidatesList'

    http_method_names = ['get', 'post', 'patch']

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user__username', 'status']
    ordering_fields = ['user', 'status']
    ordering = ['user']

    def get_object(self):
        user_id = self.kwargs.get('pk')
        return get_object_or_404(Specialist, user_id=user_id)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Получить список кандидатов с поддержкой фильтрации, "
                              "сортировки и поиска. (только для админов)",
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
        Получить список кандидатов. (только для админов)
        """
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Регистрация специалиста.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['description'],
            properties={
                'description': openapi.Schema(type=openapi.TYPE_STRING,
                                              description='Описание профиля специалиста.'),
            }
        ),
    )
    def create(self, request, *args, **kwargs):
        """
        Регистрация специалиста.
        """
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Получить кандидата по ID. (только для админов)",
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Получить кандидата по ID кандидата. (только для админов)
        """
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Обновить существующего кандидата. (только для админов)",
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
        Обновить существующего кандидата. (только для админов)
        """
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Повторная заявка, если прошлую отклонили.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['description'],
            properties={
                'description': openapi.Schema(type=openapi.TYPE_STRING,
                                              description='Описание профиля специалиста.'),
            }
        ),
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def reapplication(self, request):
        """
        Повторная заявка, если прошлую отклонили.
        """
        data = request.data

        candidate = get_object_or_404(Candidates, user__pk=request.user.id)
        serializer = self.get_serializer(candidate, data=data, partial=True)

        serializer.validate_reapplication_status(candidate.status)
        serializer.validate_reapplication_description(data.get('description'))

        candidate.reapplication(data.get('description'))

        return api_response(
            data={'message': 'Повторная заявка успешно отправлена.'}
        )

    @swagger_auto_schema(
        operation_description="Проверить статус кандидата.",
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsOwner_or_IsAdmin])
    def status(self, request, pk=None):
        """
        Проверить статус кандидата.
        """
        candidate = get_object_or_404(Candidates, user__pk=pk)

        self.check_object_permissions(request, candidate)

        if candidate.status == "Cancelled":
            return api_response(data={'user': candidate.user.id,
                                      'status': candidate.status,
                                      'rejection_text': candidate.rejection_text})
        else:
            return api_response(data={'user': candidate.user.id,
                                      'status': candidate.status})

    @swagger_auto_schema(
        operation_description="Подтверждение кандидата. (только для админов)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_STRING, description='id пользователя.'),
            }
        ),
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def accept(self, request):
        """
        Подтверждение кандидата. (только для админов)
        """
        data = request.data

        candidate = get_object_or_404(Candidates, user__pk=data.get('id'))
        serializer = self.get_serializer(candidate, data=data, partial=True)

        serializer.validate_status_transition(candidate)
        candidate.accept()
        Specialist.objects.create(user=candidate.user, description=candidate.description)

        task_send_email_candidates_accept.delay(candidate.id)

        return api_response(
            data={'message': 'Заявка одобрена и пользователь добавлен как специалист.'},
            status="success"
        )

    @swagger_auto_schema(
        operation_description="Отмена кандидата. (только для админов)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id', 'rejection_text'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_STRING, description='id пользователя.'),
                'rejection_text': openapi.Schema(type=openapi.TYPE_STRING, description='Причина отказа.'),
            }
        ),
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def cancel(self, request):
        """
        Отмена кандидата. (только для админов)
        """
        data = request.data

        candidate = get_object_or_404(Candidates, user__pk=data.get('id'))
        serializer = self.get_serializer(candidate, data=data, partial=True)

        serializer.validate_status_transition(candidate)
        serializer.validate_rejection_text(data.get('rejection_text'))
        candidate.cancel(data.get('rejection_text'))

        task_send_email_candidates_cancel.delay(candidate.id)

        return api_response(
            data={'message': 'Заявка пользователя отклонена.'},
            status="success"
        )
