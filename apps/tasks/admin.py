from django.contrib import admin

from apps.tasks.models import TaskProgress

# Register your models here.
admin.site.register(TaskProgress)
