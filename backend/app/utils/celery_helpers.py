from celery.result import AsyncResult
from celery_app import celery_app
from celery.exceptions import Ignore
import time
import logging

logger = logging.getLogger(__name__)

def update_super_task_state(super_task_id: str, state: str, meta: dict):
    """
    Update the state of a super task in Celery.
    
    :param super_task_id: The ID of the super task to update.
    :param state: The new state to set for the task.
    :param meta: Metadata to store with the task state.
    """
    try:
        # Use the configured celery_app to ensure backend is available
        celery_app.AsyncResult(super_task_id).backend.store_result(
            task_id=super_task_id,
            result=meta,  # this becomes `info`
            state=state
        )
    except Exception as e:
        # Log, but don't fail the task due to state update
        logger.warning(f"Failed to update state for task {super_task_id}: {e}")

def get_task_progress(task_id: str):
    """
    Get the progress of a Celery task by its ID.
    
    :param task_id: The ID of the task to check.
    :return: A dictionary containing the task state and metadata.
    """
    # Use the configured celery_app to ensure result backend is functional
    result = AsyncResult(task_id, app=celery_app)
    return {
        "state": result.state,
        "meta": result.info
    }

def does_task_exist(task_id: str) -> bool:
    """
    Check if a Celery task exists in the backend by its ID.
    
    :param task_id: The ID of the task to check.
    :return: True if the task exists, False otherwise.
    """
    try:
        # Use the configured celery_app to query the result backend
        result = AsyncResult(task_id, app=celery_app)
        
        # A task "exists" if it has a valid state or metadata in the backend
        if result.state != "PENDING" or result.info is not None or result.result is not None:
            return True
        # If state is PENDING and no info/result, check if task is in backend
        if result.backend.get_status(task_id) is not None:
            return True
        return False
    except Exception as e:
        # Log the error but don't fail, return False as task likely doesn't exist
        logger.warning(f"Error checking existence of task {task_id}: {e}")
        return False

def is_task_revoked(task_id: str) -> bool:
    """Check if a task is revoked."""
    try:
        return AsyncResult(task_id, app=celery_app).state == "REVOKED"
    except Exception as e:
        logger.warning(f"Error checking revoked state for task {task_id}: {e}")
        return False

def abort_if_revoked(task_id: str, super_task_id: str | None = None) -> None:
    """Abort the current task if it or its super task has been revoked."""
    if is_task_revoked(task_id):
        raise Ignore()
    if super_task_id and is_task_revoked(super_task_id):
        raise Ignore()

def stop_task(task_id: str, terminate: bool = False, signal: str = "SIGTERM") -> bool:
    """
    Stop a Celery task by revoking it, with an option to forcefully terminate.

    :param task_id: The ID of the task to stop.
    :param terminate: If True, forcefully terminate the task using the specified signal.
    :param signal: The signal to send for termination (default: SIGTERM).
    :return: True if the task was successfully revoked or terminated, False otherwise.
    """
    try:
        # Check if the task exists
        if not does_task_exist(task_id):
            logger.warning(f"Task {task_id} does not exist in the backend.")
            return False

        # Get task result object
        result = AsyncResult(task_id, app=celery_app)

        # Check if task is already completed or revoked
        if result.state in ["SUCCESS", "FAILURE", "REVOKED"]:
            logger.info(f"Task {task_id} is already in state {result.state}, no action needed.")
            return True

        # Revoke the task
        result.revoke(terminate=terminate, signal=signal)
        logger.info(f"Task {task_id} {'terminated' if terminate else 'revoked'} successfully.")

        # Update task state to REVOKED in the backend (optional, for consistency)
        update_super_task_state(task_id, "REVOKED", {"reason": "Task stopped by user"})
        return True

    except Exception as e:
        logger.error(f"Failed to stop task {task_id}: {e}")
        return False