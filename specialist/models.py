from django.db import models

from accounts.models import User


# Create your models here.
class Specialist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def block(self):
        self.is_active = False
        self.save()

    def unblock(self):
        self.is_active = True
        self.save()


class Candidates(models.Model):
    POSITIONS_STATUS = [
        ('In processing', 'В обработке'),
        ('Cancelled', 'Отменено'),
        ('Successfully', 'Успешно'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=13, choices=POSITIONS_STATUS, default='In processing')
    rejection_text = models.TextField(null=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def reapplication(self, description):
        self.status = 'In processing'
        self.description = description
        self.rejection_text = ""
        self.save()

    def accept(self):
        self.status = 'Successfully'
        self.save()

    def cancel(self, text):
        self.status = 'Cancelled'
        self.rejection_text = text
        self.save()
