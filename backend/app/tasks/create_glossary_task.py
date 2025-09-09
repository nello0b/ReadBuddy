import logging
from celery import shared_task
from celery_app import celery_app
from app.models.glossary import Glossary
from app.models.glossary_entry import GlossaryEntry
from app.utils.gpt import extract_glossary
from app.utils.celery_helpers import update_super_task_state, abort_if_revoked
from app.models.task_status import TaskStatus
from database import db
from typing import List
from celery import chain
import asyncio

logger = logging.getLogger(__name__)

state_info = [
    {"description": "Setting Up Glossary Creation Flow"},
    {"description": "Extracting Glossary"},
    {"description": "Saving Glossary"},
]

out_of_steps = len(state_info) - 1

RETRIES = 3  # Number of retries for each task

class GlossaryCreationContext:
    def __init__(
        self,
        user_id: str = None,
        articles: List[str] = None,
        lang: str = "auto",
        category: str = None,
        super_task_id: str = None,
        glossary: Glossary = None,
        with_audio: bool = True,
        step: int = 1,
    ):
        self.user_id = user_id
        self.articles = articles or []
        self.lang = lang
        self.category = category
        self.super_task_id = super_task_id
        self.glossary = glossary
        self.with_audio = with_audio
        self.step = step
        
@celery_app.task(bind=True)
def create_glossary_task(
    self, 
    user_id: str, 
    articles: List[str], 
    lang: str = "auto", 
    category: str = None,
    with_audio: bool = True
    ):
    """Set up and run the glossary creation flow."""
    context = GlossaryCreationContext(
        user_id=user_id,
        articles=articles,
        lang=lang,
        category=category,
        super_task_id=self.request.id,
        with_audio=with_audio,
    )

    # Define the workflow chain
    workflow = chain(
        extract_glossary_task.s(context),
        save_glossary_task.s(),
    )

    # Replace the current task with the workflow
    self.replace(workflow)

def _mark_workflow_failure(context: GlossaryCreationContext, error_message: str):
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

@shared_task(bind=True, max_retries=RETRIES, default_retry_delay=10)
def extract_glossary_task(self, context: GlossaryCreationContext):
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
def save_glossary_task(self, context: GlossaryCreationContext):
    """Save the extracted glossary to the database."""
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

        db.save_glossary(context.glossary, context.user_id)
        logger.info(f"[User {context.user_id}] Glossary saved successfully")
        
        db.save_task_state(
            task_id=context.super_task_id,
            state="SUCCESS",
            meta=context.glossary.id,
        )
        return context.glossary.id
    except Exception as e:
        logger.error(f"[User {context.user_id}] Saving glossary failed: {e}", exc_info=True)
        if self.request.retries >= self.max_retries:
            # Final failure - mark workflow as failed
            _mark_workflow_failure(context, str(e))
        raise self.retry(exc=e)