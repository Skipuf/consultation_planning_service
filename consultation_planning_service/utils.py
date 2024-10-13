from rest_framework.views import exception_handler
from rest_framework.response import Response

from django.core.cache import cache

import hashlib


def custom_exception_handler(exc, context):
    # Получаем стандартный ответ
    response = exception_handler(exc, context)

    if response is not None:
        errors = response.data

        # Преобразуем все значения в списки, если они не являются списками
        formatted_errors = {
            key: value if isinstance(value, list) else [value]
            for key, value in errors.items()
        }

        # Обновляем формат ошибки в едином виде
        response.data = {
            "status": "error",
            "errors": formatted_errors,
            "data": {},
        }

    return response


def api_response(status="success", data=None, errors=None, http_status=200):
    """
    Универсальная функция для формирования стандартизированных ответов.

    :param status: "success" или "error"
    :param data: данные ответа
    :param errors: ошибки, если они есть
    :param http_status: HTTP статус для ответа
    :return: объект Response
    """
    response = {
        "status": status,
        "data": data if data is not None else {},
        "errors": errors if errors is not None else {},
    }

    return Response(response, status=http_status)


class StandardResponseMixin:
    """
    Миксин для стандартизации всех ответов ViewSet
    """

    def finalize_response(self, request, response, *args, **kwargs):
        # Если уже есть форматированный ответ, пропускаем обработку
        if isinstance(response.data, dict) and {"status", "data", "errors"}.issubset(response.data.keys()):
            return super().finalize_response(request, response, *args, **kwargs)

        # Если это ошибка, просто возвращаем
        if response.status_code >= 400:
            return super().finalize_response(request, response, *args, **kwargs)

        # Формируем стандартный успешный ответ
        formatted_response = {
            "status": "success",
            "data": response.data,
            "errors": {},
        }
        response.data = formatted_response

        return super().finalize_response(request, response, *args, **kwargs)


class CacheResponseMixin:
    """
    Миксин для автоматического кэширования ответов методов list и retrieve.
    """
    cache_timeout = None
    name_prefix_cache = ''

    def _get_cache_key(self, prefix, request):
        """
        Создает уникальный ключ для кэша на основе префикса и параметров запроса.
        """
        query_string = request.GET.urlencode()
        hash_key = hashlib.md5(query_string.encode('utf-8')).hexdigest()
        return f"{prefix}_{hash_key}"

    def get(self, request, *args, **kwargs):
        """
        Переопределение метода get с поддержкой кэширования.
        """
        cache_key = f'{self.name_prefix_cache}_detail_cache_{request.user.id}'
        cached_response = cache.get(cache_key)

        if cached_response:
            return Response(cached_response)

        response = super().get(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=self.cache_timeout)
        return response

    def list(self, request, *args, **kwargs):
        """
        Переопределение метода list с поддержкой кэширования.
        """
        cache_key = self._get_cache_key(f'{self.name_prefix_cache}_list_cache', request)
        cached_response = cache.get(cache_key)

        if cached_response:
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=self.cache_timeout)
        return response

    def retrieve(self, request, *args, **kwargs):
        """
        Переопределение метода retrieve с поддержкой кэширования.
        """
        cache_key = f'{self.name_prefix_cache}_detail_cache_{kwargs["pk"]}'
        cached_response = cache.get(cache_key)

        if cached_response:
            return Response(cached_response)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=self.cache_timeout)
        return response
