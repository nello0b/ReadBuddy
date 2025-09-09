from fastapi import APIRouter, HTTPException
import os
from database import db

router = APIRouter()

@router.delete("/static/audio/{filename}")
async def delete_audio_file(filename: str):
    file_path = os.path.join("static", "audio", filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"detail": "File deleted"}
    else:
        raise HTTPException(status_code=404, detail="File not found")

@router.delete("/static/image/{filename}")
async def delete_image_file(filename: str):
    file_path = os.path.join("static", "image", filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"detail": "File deleted"}
    else:
        raise HTTPException(status_code=404, detail="File not found")

@router.delete("/api/image-extraction-result/{extraction_id}/{user_id}")
def delete_image_extraction(extraction_id: str, user_id: str):
    deleted = db.delete_image_extraction_result(extraction_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Extraction result not found")
    return {"detail": "Extraction result deleted"}

@router.delete("/api/quiz/{quiz_id}/{user_id}")
def delete_quiz(quiz_id: str, user_id: str):
    deleted = db.delete_quiz(quiz_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return {"detail": "Quiz deleted"}

@router.delete("/api/summaries/{summary_id}/{user_id}")
def delete_summary(summary_id: str, user_id: str):
    deleted = db.delete_summary(summary_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Summary not found")
    return {"detail": "Summary deleted"}


