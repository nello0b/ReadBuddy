# app/routes/image_upload.py

from fastapi import APIRouter, File, UploadFile, HTTPException
from database import db
from celery_app import celery_app

import shutil
import os
import uuid
from app.tasks.image_extraction_result_tasks import create_and_save_image_extraction_result

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/api/process-image/{user_id}")
async def process_image(user_id: str, file: UploadFile = File(...)):
    # check if the user exists in the database
    user = db.get_user_by_sub(user_id)
    if not user:
        logger.exception(f"User with ID {user_id} not found.")
        raise HTTPException(status_code=404, detail="User not found.")

    if file is None:
        logger.exception(f"No file uploaded for user {user_id}.")
        raise HTTPException(status_code=400, detail="No file uploaded.")
    if not file.content_type or not file.content_type.startswith("image/"):
        logger.exception(f"Uploaded file is not an image: {file.content_type} for user {user_id}.")
        raise HTTPException(status_code=400, detail="Uploaded file is not an image.")

    os.makedirs("temp", exist_ok=True)
    temp_file_path = os.path.join("temp", f"{uuid.uuid4()}.png")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        await file.close() 

    try:
        async_result = create_and_save_image_extraction_result.delay(user_id, temp_file_path)
        task_id = async_result.id

    except Exception as e:
        logger.exception(f"Failed to start processing for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")

    return {"task_id": str(task_id), "status": "Task entered the queue. Check the task status later."}

