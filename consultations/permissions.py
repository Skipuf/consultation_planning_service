from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение, позволяющее редактировать запись только автору.
    Остальные пользователи могут только просматривать записи.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user


class IsOwner(permissions.BasePermission):
    """
    Разрешение, позволяющее редактировать запись только автору.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsInSpecialistGroupOrReadOnly(permissions.BasePermission):
    """
    Разрешает доступ на запись только пользователям в группе 'specialists',
    но позволяет просматривать записи всем.
    """

    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        return request.user.groups.filter(name='specialist').exists()


class IsConsultationAuthorOrBookingAuthor(permissions.BasePermission):
    """
    разрешение, позволяющее получить доступ только автору консультации или автору бронирования.
    """

    def has_object_permission(self, request, view, obj):
        if obj.user == request.user:
            return True

        if obj.consultation.user == request.user:
            return True

        return False


class IsConsultationAuthor(permissions.BasePermission):
    """
    разрешение, позволяющее получить доступ только автору консультации.
    """

    def has_object_permission(self, request, view, obj):
        return obj.consultation.user == request.user