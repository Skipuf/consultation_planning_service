from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Пользовательское разрешение, позволяющее предоставлять доступ только администраторам.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class we_accept_applications_from_everyone(BasePermission):
    """
    Разрешено отправлять только заявки на регистрацию. Все остальные запросы только для админов.
    """

    def has_permission(self, request, view):
        # Разрешаем всем отправлять POST-запросы на создание заявки
        if request.method == 'POST':
            return True

        # Остальные запросы доступны только администраторам
        return request.user and request.user.is_staff


class IsOwner_or_IsAdmin(BasePermission):
    """
    Разрешение, позволяющее только автору и админам.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff


class Only_a_patch_is_allowed_for_owners(BasePermission):
    """
    Разрешение, только patch для владельцев
    """

    def has_object_permission(self, request, view, obj):
        if request.method == 'PATCH':
            return obj.user == request.user or request.user.is_staff
        return False
