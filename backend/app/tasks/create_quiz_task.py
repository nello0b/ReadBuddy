# app/tasks/create_quiz_task.py

from celery import shared_task, chain
from celery_app import celery_app
from typing import List
import logging

from database import db
from app.utils.celery_helpers import update_super_task_state, abort_if_revoked
from app.services import gpt_service
from app.models.task_status import TaskStatus
from app.models.question import Question
from app.models.glossary import Glossary
from app.models.quiz import Quiz
from app.utils.tts import synthesize_question_speech
from app.utils.gpt import extract_glossary
import asyncio

logger = logging.getLogger(__name__)

state_info = [
    {"description": "Setting Up Quiz Creation Flow"},
    {"description": "Extracting Glossary"},
    {"description": "Generating Questions"},
    {"description": "Saving Quiz"},
]

out_of_steps = len(state_info) - 1

RETRIES = 3  # Number of retries for each task


class QuizCreationContext:
    def __init__(
        self,
        user_id: str = None,
        articles: List[str] = None,
        number_of_questions: int = 0,
        lang: str = "auto",
        category: str = None,
        with_audio: bool = True,
        with_evaluation: bool = True,
        super_task_id: str = None,
        glossary:Glossary=None,
        questions: List[Question] = None,
        quiz: Quiz = None,
        step: int = 1,
    ):
        self.user_id = user_id
        self.articles = articles or []
        self.number_of_questions = number_of_questions
        self.lang = lang
        self.category = category
        self.with_audio = with_audio
        self.with_evaluation = with_evaluation
        self.super_task_id = super_task_id
        self.glossary = glossary
        self.questions = questions or []
        self.quiz = quiz
        self.step = step


@celery_app.task(bind=True)
def create_quiz_from_articles_task(
    self,
    user_id: str,
    articles: List[str],
    number_of_questions: int,
    lang: str = "auto",
    category: str = None,
    with_audio: bool = True,
    with_evaluation: bool = True,
):
    """Orchestrate quiz creation from articles."""
    abort_if_revoked(self.request.id)
    task_id = self.request.id
    
    update_super_task_state(
            task_id,
            state="STARTED",
            meta=TaskStatus.get_meta(
                user_id=user_id,
                step=0,
                out_of=out_of_steps,
                description=state_info[0]["description"],
                attempt=self.request.retries + 1,
            ),
        )
    
    logger.info(f"[User {user_id}] with_evaluation: {with_evaluation}")
    
    context = QuizCreationContext(
        user_id=user_id,
        articles=articles,
        number_of_questions=number_of_questions,
        lang=lang,
        category=category,
        with_audio=with_audio,
        with_evaluation=with_evaluation,
        super_task_id=task_id,
    )
    
    

    workflow = chain(
        extract_glossary_task.s(context),
        generate_questions_task.s(),
        save_quiz_task.s(),
    )

    self.replace(workflow)

@shared_task(bind=True, max_retries=RETRIES, default_retry_delay=10)
def extract_glossary_task(self, context: QuizCreationContext):
    """Extract glossary from the articles."""
    abort_if_revoked(self.request.id, context.super_task_id)
    try:
        update_super_task_state(
            context.super_task_id,
            state="PROGRESS",
            meta=TaskStatus.get_meta(
                user_id=context.user_id,
                step=context.step,
                out_of=out_of_steps,
                description=state_info[context.step]["description"],
                attempt=self.request.retries + 1,
            ),
        )

        glossary: Glossary = extract_glossary(
            articles=context.articles,
            lang=context.lang,
            category=context.category
        )
        logger.info(f"[User {context.user_id}] Glossary extraction completed successfully")
        
        context.glossary = glossary
        context.step += 1
        return context
    except Exception as e:
        logger.error(f"[User {context.user_id}] Glossary extraction failed: {e}", exc_info=True)
        if self.request.retries >= self.max_retries:
            # Final failure - mark workflow as failed
            _mark_workflow_failure(context, str(e))
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=RETRIES, default_retry_delay=10)
def generate_questions_task(self, context: QuizCreationContext):
    """Generate questions based on the articles and glossary."""
    abort_if_revoked(self.request.id, context.super_task_id)
    try:
        update_super_task_state(
            context.super_task_id,
            state="PROGRESS",
            meta=TaskStatus.get_meta(
                user_id=context.user_id,
                step=context.step,
                out_of=out_of_steps,
                description=state_info[context.step]["description"],
                attempt=self.request.retries + 1,
            ),
        )

        questions_dict = gpt_service.generate_questions(
            article_texts=context.articles,
            glossary=context.glossary,
            number_of_questions=context.number_of_questions,
            lang=context.lang,
            with_evaluation=context.with_evaluation,
        )

        questions: List[Question] = [
            Question.from_dict(user_id=context.user_id, data=q_dict)
            for q_dict in questions_dict if isinstance(q_dict, dict)
        ]

        context.questions = questions
        context.step += 1
        return context
    except Exception as e:
        logger.warning(f"[User {context.user_id}] Question generation failed: {e}")
        if self.request.retries >= self.max_retries:
            # Final failure - mark workflow as failed
            _mark_workflow_failure(context, str(e))
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=RETRIES, default_retry_delay=10)
def save_quiz_task(self, context: QuizCreationContext):
    """Save the generated quiz to the database."""
    abort_if_revoked(self.request.id, context.super_task_id)
    try:
        update_super_task_state(
            context.super_task_id,
            state="PROGRESS",
            meta=TaskStatus.get_meta(
                user_id=context.user_id,
                step=context.step,
                out_of=out_of_steps,
                description=state_info[context.step]["description"],
                attempt=self.request.retries + 1,
            ),
        )

        category = context.glossary.category if context.glossary else context.category
        title = f"Quiz on {category}"
        if context.lang == "Hebrew":
            title = f"שאלון בנושא {category}"

        quiz = Quiz(
            user_id=context.user_id,
            title=title,
            category=category,
            question_ids=[q.id for q in context.questions],
        )

        db.save_questions(context.questions, user_id=context.user_id)
        db.save_quiz(quiz)

        context.quiz = quiz
        if context.with_audio:
            for question in context.questions:
                create_audio_and_update_question.delay(question, context.lang)

        db.save_task_state(
            task_id=context.super_task_id,
            state="SUCCESS",
            meta=quiz.id,
        )
        return quiz.id
    except Exception as e:
        logger.warning(f"[User {context.user_id}] Saving quiz failed: {e}")
        if self.request.retries >= self.max_retries:
            # Final failure - mark workflow as failed
            _mark_workflow_failure(context, str(e))
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=RETRIES, default_retry_delay=10) 
def create_audio_and_update_question(self, question: Question, lang: str) -> None:
    """
    Helper function to create audio files for the questions and save it to the database.
    """
    abort_if_revoked(self.request.id)
    try:
        zip_paths: List[str] = asyncio.run(synthesize_question_speech(
            question=question,
            lang=lang,
            ))
        
        if zip_paths:
            # zip_paths contains the audio zip file paths for the question and
            # its answers. ``Question`` and ``Answer`` models expect the
            # ``audio_zip_urls`` attribute to be a list of file paths, so wrap
            # each path in a list before assigning.
            question.audio_zip_urls = [zip_paths[0]]
            for j, answer in enumerate(question.answers):
                if j < len(zip_paths) - 1:
                    answer.audio_zip_urls = [zip_paths[j + 1]]
            # Save the question with the audio URLs
            db.update_question(question, question.user_id)
            logger.info(f"[User {question.user_id}] Audio synthesized for question {question.id}")
        else:
            raise ValueError(f"No audio generated for question {question.id}")
    except Exception as e:
        logger.warning(f"[User {question.user_id}] Error synthesizing audio for question {question.id}: {e}")
        if self.request.retries >= self.max_retries:
            # Final failure - mark workflow as failed
            _mark_workflow_failure(QuizCreationContext(), str(e))
        raise self.retry(exc=e)

def _mark_workflow_failure(context: QuizCreationContext, error_message: str):
    """Helper function to mark workflow as failed and cleanup."""
    try:
        logger.error(f"[User {context.user_id}] 🛑 Workflow failed: {error_message}")
        
        # Update the main task state to FAILURE
        update_super_task_state(
            context.super_task_id,
            state="FAILURE", 
            meta=TaskStatus.get_meta(
                step=0,
                out_of=0,
                description=f"Workflow failed: {error_message}",
                user_id=context.user_id,
                attempt=1
            )
        )
        
        # Save failure state to database
        db.save_task_state(
            task_id=context.super_task_id,
            state="FAILURE",
            meta=error_message,
        )
    except Exception as handler_error:
        logger.error(f"Error in workflow failure marker: {handler_error}")
