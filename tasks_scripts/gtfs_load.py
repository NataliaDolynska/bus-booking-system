import tempfile

from apps.gtfs.gtfs_loader import GTFSLoader
from apps.tasks.models import TaskProgress
from apps.tasks.utils.db_utils import if_exists
from apps.tasks.utils.file_utils import compute_file_hash
from apps.tasks.utils.fs_utils import extract_zip_flat
from loguru import logger


def update_progress(task_id, message, total_steps, current_step):
    if task_id:
        try:
            progress_record = if_exists(TaskProgress, task_id=task_id)
            if not progress_record:
                logger.error(
                    f"TaskProgress.update_progress: TaskProgress does not exist for task_id {task_id}")
                return

            progress = int((current_step / total_steps) * 100)
            progress_record.status = "processing"
            progress_record.progress = progress
            progress_record.message = message
            progress_record.save()
        except TaskProgress.DoesNotExist:
            logger.error(f"TaskProgress.update_progress: TaskProgress does not exist for task_id {task_id}", )
            raise ValueError(
                f"TaskProgress.update_progress: TaskProgress does not exist for task_id {task_id}",
                task_id)


def load_gtfs_data(file_path):
    try:
        file_hash = compute_file_hash(file_path)
        task_progress = TaskProgress.objects.get(file_hash=file_hash)
        temp_dir = tempfile.TemporaryDirectory()

        files = extract_zip_flat(file_path, temp_dir.name)
        logger.info(f"Extracting files: {files}")

        loader = GTFSLoader(task_id=task_progress.task_id, progress_fn=update_progress)
        logger.info(f"Loading GTFS data from {temp_dir.name}")
        loader.load_data(temp_dir.name)

        temp_dir.cleanup()

        return {'status': 'completed'}
    except Exception as e:
        logger.error(f"Error importing GTFS data: {repr(e)}")
        raise Exception(f"Error importing GTFS data: {repr(e)}")


import os, sys


def main(argv):
    try:
        load_gtfs_data(argv[1])
    except Exception as e:

        print('Err: ' + str(e))
        exit(1)


if __name__ == '__main__':
    main(sys.argv)
