# app/routes/get_history.py

from fastapi import APIRouter, HTTPException, Query
from app.models.extraction_result_summary import ExtractionResultSummary
from database import db
from typing import List

router = APIRouter()

# returns all the extraction results for a user in a summary format
@router.get("/history/{user_id}")
def get_user_history(user_id: str):
    history: List[ExtractionResultSummary] = db.get_all_extraction_results_summary(user_id)
    if history is None:
        raise HTTPException(status_code=404, detail="History not found")
    
    return {summary.extraction_id: summary.to_dict() for summary in history}


# returns the n most recent extraction results for a user in a summary format
@router.get("/history/recent/{user_id}")
def get_recent_user_history(
    user_id: str,
    n: int = Query(10, gt=0, description="Number of recent results to return")
):
    if n <= 0:
        raise HTTPException(status_code=400, detail="n must be a positive integer")
    
    history: List[ExtractionResultSummary] = db.get_all_extraction_results_summary(user_id)
    if history is None:
        raise HTTPException(status_code=404, detail="History not found")
    
    # Sort by created_at in descending order and take the first n results
    recent_history = sorted(history, key=lambda x: x.created_at, reverse=True)[:n]
    
    return {summary.extraction_id: summary.to_dict() for summary in recent_history}