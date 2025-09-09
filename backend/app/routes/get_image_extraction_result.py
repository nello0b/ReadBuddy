# app/routes/get_image_extraction_result.py

from fastapi import APIRouter, HTTPException, Body
from app.models.image_extraction_result import ImageExtractionResult
from database import db
from typing import List, Dict

router = APIRouter()

# returns the image extraction result for a user by extraction_id
@router.get("/api/image-extraction-result/{extraction_id}/{user_id}")
def get_image_extraction_result_by_id(extraction_id: str, user_id: str):
    result:ImageExtractionResult = db.get_image_extraction_result_by_id(extraction_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Extraction result not found")
    return result.to_dict()

# returns the image extraction results for a user by a list of extraction_ids
@router.post("/api/image-extraction-results/{user_id}")
def get_image_extraction_results_by_ids(
    user_id: str,
    body: Dict[str, List[str]] = Body(...)
):
    extraction_ids = body.get("extraction_ids")
    if not extraction_ids:
        raise HTTPException(status_code=422, detail="Missing 'extraction_ids' in body")
    
    results = db.get_image_extraction_results_by_ids(extraction_ids, user_id)
    if not results:
        raise HTTPException(status_code=404, detail="Extraction results not found")

    return [result.to_dict() for result in results]



@router.put("/api/image-extraction-result/update-category/{extraction_id}/{user_id}")
def update_image_extraction_result_category(
    extraction_id: str,
    user_id: str,
    body: Dict[str, str] = Body(...)
):
    category = body.get("new_category")
    if not category:
        raise HTTPException(status_code=422, detail="Missing 'new_category' in body")
    result = db.update_extraction_results_category(category, extraction_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Extraction result not found or update failed")
    return {"message": "Category updated successfully"}

@router.get("/api/image-extraction-results/category/{category}/{user_id}")
def get_extraction_results_by_category(category: str, user_id: str):
    results = db.get_extraction_results_by_category(category, user_id)
    if not results:
        raise HTTPException(status_code=404, detail="No extraction results found for this category")
    
    return [result.to_dict() for result in results]


    