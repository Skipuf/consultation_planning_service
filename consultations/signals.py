from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from django.core.cache import cache

from consultations.models import Booked, Consultation
from consultations.tasks import task_send_email_booked_create, task_send_email_booked_cancellation, \
    task_send_email_booked_accept


@receiver(pre_save, sender=Booked)
def booked_pre_save(sender, instance, **kwargs):
    if instance.pk:
        old_instance = Booked.objects.get(pk=instance.pk)
        instance._old_values = {field.name: getattr(old_instance, field.name) for field in instance._meta.fields}


@receiver(post_save, sender=Booked)
def booked_post_save(sender, instance, created, **kwargs):
    cache.delete_pattern('BookedList_list_cache_*')
    cache.delete(f'BookedList_detail_cache_{instance.user_id}')
    cache.delete(f'BookedAccountView_detail_cache_{instance.user_id}')
    cache.delete(f'ConsultationsAccount_detail_cache_{instance.user_id}')

    if created:
        # Если объект был создан, а не обновлён
        task_send_email_booked_create.delay(instance.consultation.id)
    else:
        # Если объект был обновлён, проверяем, какие поля изменились
        changed_fields = {}
        for field in instance._meta.fields:
            field_name = field.name
            old_value = instance._old_values.get(field_name)
            new_value = getattr(instance, field_name)
            if old_value != new_value:
                changed_fields[field_name] = (old_value, new_value)

        if changed_fields:
            if 'status' in changed_fields:
                if changed_fields['status'][1] == 'Booked':
                    task_send_email_booked_accept.delay(instance.id)
                elif changed_fields['status'][1] == 'Cancelled':
                    task_send_email_booked_cancellation.delay(instance.id)


@receiver(post_save, sender=Consultation)
def consultation_post_save(sender, instance, created, **kwargs):
    cache.delete_pattern('ConsultationList_list_cache_*')
    cache.delete(f'ConsultationList_detail_cache_{instance.user_id}')
    cache.delete(f'ConsultationsAccount_detail_cache_{instance.user_id}')
    cache.delete(f'BookedAccountView_detail_cache_{instance.user_id}')
