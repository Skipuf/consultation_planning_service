from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from rest_framework_simplejwt.tokens import RefreshToken


# Create your models here.
class User(AbstractUser):
    email = models.EmailField(unique=True, blank=False, null=False)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    groups = models.ManyToManyField(
        Group,
        related_name='custom_users',
        blank=True,
        help_text='Группы, к которым принадлежит пользователь.',
        verbose_name='группы'
    )

    def token(self):
        return RefreshToken.for_user(self).access_token

    def confirm_email(self):
        self.is_verified = True
        self.save()

    def block(self):
        self.is_active = False
        self.save()

    def unblock(self):
        self.is_active = True
        self.save()