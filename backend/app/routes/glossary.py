# app/routes/glossary.py

from fastapi import APIRouter, HTTPException, Body
from app.models.glossary import Glossary
from typing import Dict, List
from database import db
from app.tasks.create_glossary_task import create_glossary_task
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/api/glossary/create/{category}/{user_id}/{lang}")
async def create_glossary_by_category(category: str, user_id: str, lang: str, with_audio: bool = True):
    """
    Endpoint to create a glossary for a specific category and user.
    """
    # getting the documents with that category
    results = db.get_extraction_results_by_category(category, user_id)
    if not results:
        raise HTTPException(status_code=404, detail="No extraction results found for this category")

    # extract the text from the results
    articles = []
    for result in results:
        text_data = result.text_data
        if isinstance(text_data, dict):
            content = text_data.get("content")
        else:
            content = getattr(text_data, "content", None)
        if content:
            articles.append(content)
            
    try:
        async_result = create_glossary_task.delay(
            user_id=user_id,
            articles=articles,
            lang=lang,
            category=category,
            with_audio=with_audio
        )
        task_id = async_result.id

    except Exception as e:
        logger.exception(f"Failed to start glossary creation for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start glossary creation: {str(e)}")

    return {"task_id": str(task_id), "status": "Task entered the queue. Check the task status later."}

@router.post("/api/glossary/create-from-extractions/{user_id}/{lang}")
async def create_glossary_from_extractions(user_id: str, lang: str, body: Dict[str, List[str]] = Body(...), with_audio: bool = True):
    """Endpoint to create a glossary for a user based on extraction IDs provided in the request body."""
    extraction_ids = body.get("extraction_ids")
    if not extraction_ids:
        raise HTTPException(status_code=400, detail="No extraction IDs provided")
    
    # getting the documents with that category
    results = db.get_extraction_results_by_ids(extraction_ids, user_id)
    if not results:
        raise HTTPException(status_code=404, detail="No extraction results found for the provided IDs")

    # extract the text from the results
    articles = []
    for result in results:
        extraction_res = result[0] if isinstance(result, tuple) else result
        text_data = extraction_res.text_data
        if isinstance(text_data, dict):
            content = text_data.get("content")
        else:
            content = getattr(text_data, "content", None)
        if content:
            articles.append(content)
    
    try:
        async_result = create_glossary_task.delay(
            user_id=user_id,
            articles=articles,
            lang=lang,
            with_audio=with_audio
        )
        task_id = async_result.id

    except Exception as e:
        logger.exception(f"Failed to start glossary creation for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start glossary creation: {str(e)}")

    return {"task_id": str(task_id), "status": "Task entered the queue. Check the task status later."}

@router.get("/api/glossary/by-id/{glossary_id}/{user_id}")
async def get_glossary_by_id(glossary_id: str, user_id: str):
    """
    Retrieve a glossary by its ID for a specific user.
    """
    glossary = db.get_glossary_by_id(glossary_id, user_id)
    if not glossary:
        raise HTTPException(status_code=404, detail="Glossary not found")
    
    return {"glossary": glossary.to_dict()}

@router.get("/api/glossary/all/{user_id}")
async def get_all_glossaries(user_id: str):
    """
    Retrieve all glossaries for a specific user.
    """
    glossaries = db.get_all_glossaries(user_id)
    if not glossaries:
        raise HTTPException(status_code=404, detail="No glossaries found for this user")
    
    return {"glossaries": [glossary.to_dict() for glossary in glossaries]}

@router.delete("/api/glossary/{glossary_id}/{user_id}")
def delete_glossary(glossary_id: str, user_id: str):
    deleted = db.delete_glossary(glossary_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Glossary not found")
    return {"detail": "Glossary deleted"}
