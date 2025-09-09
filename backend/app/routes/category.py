# app/routes/category.py

from fastapi import APIRouter, HTTPException, Body
from app.models.image_extraction_result import ImageExtractionResult
from database import db
from typing import List

router = APIRouter()

@router.get("/api/categories/{user_id}")
def get_categories(user_id: str):
    result: List[str] = db.get_user_categories(user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found or no categories available")
    return {"categories": result}