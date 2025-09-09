# app/routes/summaries.py

from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict
from database import db
from app.tasks.summarise_articles_task import summarise_articles

from celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


router = APIRouter()

# Summary from a single source
@router.get("/api/summary/from-source/{source_id}/{user_id}")
async def summary_from_source(source_id: str, user_id: str):
    result = db.get_image_extraction_result_by_id(source_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Source not found")
    content = result.text_data.get("content", "") if isinstance(result.text_data, dict) else getattr(result.text_data, "content", "")
    
    try:
        async_result = summarise_articles.delay(
            user_id=user_id,
            articles=[content], 
            source_ids=[source_id]
        )
        task_id = async_result.id

    except Exception as e:
        logger.exception(f"Failed to start summary creation for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start summary creation: {str(e)}")

    return {"task_id": str(task_id), "status": "Task entered the queue. Check the task status later."}

# Summary from multiple sources
@router.post("/api/summary/from-sources/{user_id}")
async def summary_from_sources(user_id: str, body: Dict[str, List[str]] = Body(...)):
    source_ids = body.get("source_ids")
    if not source_ids:
        raise HTTPException(status_code=400, detail="No source IDs provided")
    results = db.get_image_extraction_results_by_ids(source_ids, user_id)
    if not results:
        raise HTTPException(status_code=404, detail="Sources not found")
    articles = [
        res.text_data.get("content", "")
        if isinstance(res.text_data, dict)
        else getattr(res.text_data, "content", "")
        for res in results
    ]
    source_ids = [res.id for res in results]
    
    try:
        async_result = summarise_articles.delay(
            user_id=user_id,
            articles=articles, 
            source_ids=source_ids
        )
        task_id = async_result.id

    except Exception as e:
        logger.exception(f"Failed to start summary creation for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start summary creation: {str(e)}")

    return {"task_id": str(task_id), "status": "Task entered the queue. Check the task status later."}

# Summary from text input
@router.post("/api/summary/from-text/{user_id}")
async def summary_from_text(user_id: str, body: Dict[str, str] = Body(...)):
    text = body.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    try:
        async_result = summarise_articles.delay(
            user_id=user_id,
            articles=[text]
        )
        task_id = async_result.id

    except Exception as e:
        logger.exception(f"Failed to start summary creation for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start summary creation: {str(e)}")

    return {"task_id": str(task_id), "status": "Task entered the queue. Check the task status later."}


@router.get("/api/summaries/{user_id}")
async def get_summaries(user_id: str):
    """Retrieve all summaries for a user."""
    results = db.get_summaries_by_user_id(user_id)
    if not results:
        raise HTTPException(status_code=404, detail="No summaries found for this user")
    return {"summaries": [res.to_dict() for res in results]}

@router.get("/api/summary/{summary_id}/{user_id}")
async def get_summary_by_id(summary_id: str, user_id: str):
    """Retrieve a specific summary by its ID."""
    result = db.get_summary_by_id(summary_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Summary not found")
    return result.to_dict()

@router.get("/api/summaries/by-source/{source_id}/{user_id}")
async def get_summaries_by_source(source_id: str, user_id: str):
    """Retrieve summaries that reference a specific source."""
    results = db.get_summaries_by_source_id(source_id, user_id)
    if not results:
        raise HTTPException(status_code=404, detail="No summaries found for this source")
    return {"summaries": [res.to_dict() for res in results]}
