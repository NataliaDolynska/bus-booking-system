from django.db import models

# Create your models here.
class TaskProgress(models.Model):
    task_id = models.CharField(max_length=50, unique=True)  # To match Django Q's task_id format
    file_hash = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10, unique=False, default='pending')
    progress = models.FloatField(default=0)
    message = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Progress for Task {self.task_id}: {self.progress}%"
