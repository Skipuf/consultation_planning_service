from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group

from django.core.cache import cache

from accounts.models import User
from .models import Specialist, Candidates


@receiver(post_save, sender=Specialist)
def specialist_created(instance, created, **kwargs):
    cache.delete_pattern('SpecialistList_list_cache_*')
    cache.delete(f'SpecialistList_detail_cache_{instance.user_id}')

    user = User.objects.get(pk=instance.user.id)
    specialist_group = Group.objects.get(name="specialist")

    if instance.is_active:
        user.groups.add(specialist_group)
        print('Роль выдана')
    else:
        user.groups.remove(specialist_group)


@receiver(post_save, sender=Candidates)
def Candidates_created(instance, created, **kwargs):
    cache.delete_pattern('CandidatesList_list_cache_*')
    cache.delete(f'CandidatesList_detail_cache_{instance.user_id}')
