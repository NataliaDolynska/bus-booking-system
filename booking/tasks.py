# tasks.py
import tempfile

from celery import current_task
import celery
from celery.app import shared_task


from .gtfs_loader import GTFSLoader
import os
import zipfile
import shutil
from loguru import logger

from .models import TaskProgress
from .utils.file_utils import compute_file_hash
from .utils.fs_utils import extract_zip_flat


def get_current_task_id():
    return current_task.request.id


# @shared_task(bind=True)
def import_gtfs_data(file_path):
    # logger.info(f"Importing GTFS data from {str(file_path)}", )

    try:

        # Extract the zip file
        file_hash = compute_file_hash(file_path)
        task_progress = TaskProgress.objects.get(file_hash=file_hash)
        temp_dir = tempfile.TemporaryDirectory()

        files  = extract_zip_flat(file_path, temp_dir.name)
        logger.info(f"Extracting files: {files}")

        loader = GTFSLoader(task_id=task_progress.task_id)
        logger.info(f"Loading GTFS data from {temp_dir.name}")
        loader.load_data(temp_dir.name)

        # Cleanup
        # os.remove("file_path")
        temp_dir.cleanup()
        # shutil.rmtree(temp_dir)

        return {'status': 'completed'}
    except Exception as e:
        logger.error(f"Error importing GTFS data: {repr(e)}")
        raise Exception(f"Error importing GTFS data: {repr(e)}")




