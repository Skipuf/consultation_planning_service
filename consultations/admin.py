from django.contrib import admin
from .models import Consultation, Booked

# Register your models here.
admin.site.register(Consultation)
admin.site.register(Booked)
