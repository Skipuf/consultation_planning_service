from django.contrib import admin

# Register your models here.
from .models import Candidates, Specialist

# Register your models here.
admin.site.register(Candidates)
admin.site.register(Specialist)