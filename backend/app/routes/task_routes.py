# app/routes/task_routes.py

from fastapi import APIRouter, HTTPException
from app.utils.make_json_safe import make_json_safe
from app.utils.celery_helpers import does_task_exist, stop_task
from celery_app import celery_app
from app.models.task_status import TaskStatus
from database import db
from types import SimpleNamespace
from celery.exceptions import CeleryError

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/task-status/{task_id}")
def check_status(task_id: str):
    # First, check if task exists in Celery backend and fetch result if it does
    try:
        if not does_task_exist(task_id):
            raise CeleryError("Task not found in Celery backend")
        result = celery_app.AsyncResult(task_id)
    except CeleryError:
        # Fallback to database
        try:
            task_state = db.get_task_status(task_id)
            if not task_state:
                raise HTTPException(status_code=404, detail="Task not found in Celery or database")
            # Use default values if state or meta are missing
            result = SimpleNamespace(
                state=task_state.get("state", "UNKNOWN"),
                info=task_state.get("meta", {}),
                result=None,
                traceback=str(task_state.get("traceback", None)) if task_state.get("traceback") else None
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if result.state == "SUCCESS":
        # Use result.info for metadata, fall back to TaskStatus.get_meta if empty
        info = result.info if isinstance(result.info, dict) else TaskStatus.get_meta(
            user_id="",
            step=1,
            out_of=1,
            description="Task completed successfully",
            attempt=1
        )
        return_value = result.info
    elif result.state == "PENDING":
        # Task is still pending, return empty info and None result
        info = TaskStatus.get_meta(
            user_id="",
            step=0,
            out_of=1,
            description="Task is pending",
            attempt=1
        )
        return_value = None
    else:
        # Use result.info if available, even if empty, to preserve task metadata
        info = result.info if isinstance(result.info, dict) else TaskStatus.get_meta(
            user_id="",
            step=1,
            out_of=1,
            description=f"Task is {result.state.lower()}",
            attempt=1
        )
        return_value = None
    
    # Print what we are returning for debugging
    print(f"Returning task status for {task_id}: state={result.state}, info={info}, result={return_value}, traceback={result.traceback}")

    return {
        "state": result.state,
        "info": make_json_safe(info),
        "result": make_json_safe(return_value),
        "traceback": str(result.traceback) if result.traceback else None
    }
    
@router.post("/task-stop/{task_id}")
def stop_task_route(task_id: str, terminate: bool = False):
    """
    Stop a Celery task by its ID.

    :param task_id: The ID of the task to stop.
    :param terminate: If true, forcefully terminate the task (default: False).
    :return: A dictionary with the task ID and status of the stop operation.
    """
    try:
        # Check if task exists
        if not does_task_exist(task_id):
            raise HTTPException(status_code=404, detail="Task not found in Celery backend")

        # Attempt to stop the task
        success = stop_task(task_id, terminate=terminate)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to stop task")

        return {
            "task_id": task_id,
            "status": "Task stopped successfully" if success else "Failed to stop task",
            "terminated": terminate
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error stopping task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error stopping task: {str(e)}")