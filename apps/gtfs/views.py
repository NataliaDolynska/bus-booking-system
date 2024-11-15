import os
import tempfile

from celery.app.task import Task
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django_q.tasks import async_task
from django_q.models import Task

from apps.bookings.models import Booking
from django.core import serializers
from loguru import logger
from apps.gtfs.models import *
from apps.tasks.models import TaskProgress
from apps.tasks.utils.db_utils import if_exists
from apps.tasks.utils.file_utils import compute_file_hash
from tasks_scripts.gtfs_load import load_gtfs_data


# Create your views here.

def index(request):
    context = {
        'segment': 'gtfs',
    }
    return render(request, 'gtfs/upload-gtfs.html', context)


def task_status(request):
    task_id = request.GET.get("task_id")
    try:
        logger.info(f"Task status requested for task_id: {task_id}", )
        progress_record = if_exists(TaskProgress, task_id=task_id)
        if not progress_record:
            return JsonResponse({
                "error": "Task progress record not found.",
            }, status=500)
        progress = progress_record.progress
        message = progress_record.message
        status = progress_record.status
        return JsonResponse({
            "status": status,
            "progress": progress,
            "message": message,
        })
    except Task.DoesNotExist:
        return JsonResponse({
            "error": "Task not found.",
        }, status=500)


@login_required(login_url='/users/signin/')
def admin_upload_gtfs(request):
    if request.method == 'POST':
        gtfs_file = request.FILES.get('gtfs_file')
        if gtfs_file:
            # Save the uploaded file to a temporary location
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, gtfs_file.name)

            with open(temp_file_path, 'wb+') as destination:
                for chunk in gtfs_file.chunks():
                    destination.write(chunk)

            # Start the asynchronous task
            file_hash = compute_file_hash(temp_file_path)
            exits = if_exists(TaskProgress, file_hash=file_hash)
            if exits:
                logger.debug(f"Scheduling task already exists. ")
                task = Task.get_task(exits.task_id)
                if not task:
                    task_id = exits.task_id
                    return JsonResponse({'task_id': task_id, 'status': exits.status})
                else:
                    status = "success" if task.success else "failure"
                    return JsonResponse({'task_id': exits.task_id, 'status': status, 'message': 'Task finished'})
                #     exits.delete()
            logger.debug(f"Scheduling task with function: {load_gtfs_data}")
            from django_q.brokers import get_broker
            task_id = async_task(load_gtfs_data, file_path=temp_file_path, save=True)
            logger.info(f"Loading task with id is {task_id}")
            TaskProgress.objects.get_or_create(task_id=task_id, file_hash=file_hash)

            return JsonResponse({'task_id': task_id})
        else:
            return JsonResponse({'error': 'No file uploaded.'}, status=400)
    else:
        return render(request, 'gtfs/upload-gtfs.html')
