from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Создайте группу с правами на редактирование и удаление CalendarItem.'

    def handle(self, *args, **kwargs):
        # Создаём группу
        group_name = 'specialist'
        group, created = Group.objects.get_or_create(name=group_name)

        if created:
            self.stdout.write(f"Групаа '{group_name}' Создана.")
        else:
            self.stdout.write(f"Группа '{group_name}' уже существует.")

        # Получаем права на изменение и удаление CalendarItem
        change_permission = Permission.objects.get(codename='change_consultation')
        delete_permission = Permission.objects.get(codename='delete_consultation')

        # Добавляем права группе
        group.permissions.add(change_permission, delete_permission)
        self.stdout.write(f"Разрешения 'change' и 'delete' для Consultation предоставлены '{group_name}'.")
