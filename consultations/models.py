from celery import current_app
from django.db import models
from django.contrib.postgres.fields import DateTimeRangeField

from accounts.models import User


class Consultation(models.Model):
    POSITIONS_TIME_SELECTION = [
        ('1', '1 час'),
        ('2', '2 часа'),
        ('3', '3 часа')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    time_selection = models.CharField(max_length=1, choices=POSITIONS_TIME_SELECTION, default='1')
    datetime = DateTimeRangeField()
    booking = models.BooleanField(default=False)
    price = models.FloatField(default=0.0)
    description = models.TextField(blank=True, default="")

    archive = models.BooleanField(default=False)

    celery_task_id = models.CharField(max_length=255, blank=True, null=True)

    def update_booking(self, booked):
        self.booking = booked
        self.save()
        if booked:
            booking_list = Booked.objects.filter(consultation=self, status='In processing')
            for booking in booking_list:
                booking.cancelled('Консультация была забронирована другим пользователем.')

    def cancelled(self, rejection_text):
        for booked in Booked.objects.filter(consultation=self, archive=False):
            if booked.status != 'Cancelled':
                booked.cancelled(rejection_text)

        if self.celery_task_id:
            current_app.control.revoke(self.celery_task_id, terminate=True)

        self.set_archive()

    def set_archive(self):
        self.archive = True
        self.save()


class Booked(models.Model):
    POSITIONS_STATUS = [
        ('In processing', 'В обработке'),
        ('Cancelled', 'Отменено'),
        ('Booked', 'Забронировано'),
        ('Successfully', 'Успешно'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    status = models.CharField(max_length=13, choices=POSITIONS_STATUS, default='In processing')
    rejection_text = models.TextField(null=True, default="")
    description = models.TextField(blank=True, null=True, default="")

    archive = models.BooleanField(default=False)

    def cancelled(self, text):
        if self.status == 'Booked':
            self.consultation.update_booking(False)

        self.status = 'Cancelled'
        self.rejection_text = text
        self.archive = True
        self.save()

    def booked(self):
        self.status = 'Booked'
        self.save()

        self.consultation.update_booking(True)

    def successfully(self):
        self.status = 'Successfully'
        self.archive = True
        self.save()
