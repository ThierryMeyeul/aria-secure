from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Patient

admin.site.register(Patient)