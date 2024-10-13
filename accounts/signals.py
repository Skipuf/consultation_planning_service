from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User
from .tasks import task_send_email_verify_email_user


@receiver(post_save, sender=User)
def signal_send_email_verify_email_user(instance, created, **kwargs):
    if not created:
        return

    task_send_email_verify_email_user.delay(instance.id)
