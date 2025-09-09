# app/routes/quizzes.py

from fastapi import APIRouter, HTTPException, Body
from app.models.quiz import Quiz
from app.models.question import Question 
from typing import Dict, List
from database import db
from app.tasks.create_quiz_task import create_quiz_from_articles_task

from celery_app import celery_app
import logging


logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/api/quiz/create/{category}/{user_id}/{number_of_questions}/{lang}")
async def create_quiz_by_category(category: str, user_id: str,number_of_questions: str, lang: str, with_evaluation: bool = True):
    """
    Endpoint to create a quiz for a specific category and user.
    """
    number_of_questions = int(number_of_questions)
    if number_of_questions <= 0:
        raise HTTPException(status_code=400, detail="Number of questions must be greater than 0")
    
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
        async_result = create_quiz_from_articles_task.delay(
            user_id=user_id,
            articles=articles,
            number_of_questions=number_of_questions,
            lang=lang,
            category=category,
            with_evaluation=with_evaluation
        )
        task_id = async_result.id

        

    except Exception as e:
        logger.exception(f"Failed to start quiz creation for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start quiz creation: {str(e)}")

    return {"task_id": str(task_id), "status": "Task entered the queue. Check the task status later."}

@router.post("/api/quiz/create-from-extractions/{user_id}/{number_of_questions}/{lang}")
async def create_quiz_from_extractions(user_id: str, number_of_questions: str, lang: str, body: Dict[str, List[str]] = Body(...), with_evaluation: bool = True):
    """Endpoint to create a quiz for a user based on extraction IDs provided in the request body."""
    number_of_questions = int(number_of_questions)
    if number_of_questions <= 0:
        raise HTTPException(status_code=400, detail="Number of questions must be greater than 0")
        
    extraction_ids = body.get("extraction_ids")
    if not extraction_ids:
        raise HTTPException(status_code=400, detail="No extraction IDs provided")
    
    # getting the documents with that category
    results = db.get_extraction_results_by_ids(extraction_ids, user_id)
    if not results:
        raise HTTPException(status_code=404, detail="No extraction results found for this category")

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
        async_result = create_quiz_from_articles_task.delay(
            user_id=user_id,
            articles=articles,
            number_of_questions=number_of_questions,
            lang=lang,
            with_evaluation=with_evaluation
        )
        task_id = async_result.id

    except Exception as e:
        logger.exception(f"Failed to start quiz creation for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start quiz creation: {str(e)}")

    return {"task_id": str(task_id), "status": "Task entered the queue. Check the task status later.."}

@router.get("/api/question/{question_id}/{user_id}")
async def get_question(question_id: str, user_id: str):
    """
    Endpoint to retrieve a question by its ID for a specific user.
    """

    result : Question = db.get_question_by_id(question_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {"question": result.to_dict()}

@router.get("/api/quiz/{quiz_id}/{user_id}")
async def get_quiz_by_id(quiz_id: str, user_id: str):
    """
    Endpoint to retrieve a quiz by its ID for a specific user.
    """
    result: Quiz = db.get_quiz_by_id(quiz_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return {"quiz":  result.to_dict()}

@router.get("/api/quizzes/{user_id}")
async def get_quizzes(user_id: str):
    """
    Endpoint to retrieve all quizzes for a specific user.
    """
    results : List[Quiz] = db.get_quizzes_by_user_id(user_id)
    if not results:
        raise HTTPException(status_code=404, detail="No quizzes found for this user")
    
    return {"quizzes": [result.to_dict() for result in results]}

@router.post("/api/questions/batch/{user_id}")
async def get_questions(user_id: str, body: Dict[str, List[str]] = Body(...)):
    """
    Endpoint to retrieve multiple questions by their IDs for a specific user.
    """
    question_ids = body.get("question_ids")
    if not question_ids:
        raise HTTPException(status_code=400, detail="No question IDs provided")
    
    results: List[Question] = db.get_questions_by_ids(question_ids, user_id)
    if not results:
        raise HTTPException(status_code=404, detail="No questions found for the provided IDs")

    return {"questions": [result.to_dict() for result in results]}

@router.get("/api/quizzes/by-category/{category}/{user_id}")
async def get_quizzes_by_category(category: str, user_id: str):
    """
    Endpoint to retrieve a quizzes for a specific category and user.
    """
    results: List[Quiz] = db.get_quizzes_by_category(category, user_id)
    if not results:
        raise HTTPException(status_code=404, detail="No quizzes found for this category")

    return {"quizzes": [result.to_dict() for result in results]}
