# app/tasks/summarise_articles_task.py

from celery import shared_task, chain
from celery_app import celery_app
from typing import List
import logging
import asyncio

from database import db
from app.services import gpt_service
from app.utils.celery_helpers import update_super_task_state, abort_if_revoked
from app.utils.language import detect_language_from_text
from app.utils.tts import synthesize_summary_speech
from app.utils.text import split_text_into_paragraphs
from app.models.summary import Summary
from app.models.task_status import TaskStatus


logger = logging.getLogger(__name__)


state_info = [
    {"description": "Setting Up Summary Creation Flow"},
    {"description": "Detecting Language"},
    {"description": "Generating Summary"},
    {"description": "Saving Summary"},
    {"description": "Synthesizing Audio"},
]

out_of_steps = len(state_info) - 1

RETRIES = 3  # Number of retries for each task


class SummaryCreationContext:
    def __init__(
        self,
        user_id: str = None,
        articles: List[str] = None,
        source_ids: List[str] = None,
        lang: str = "auto",
        with_audio: bool = True,
        super_task_id: str = None,
        summary: Summary = None,
        paragraphs: List[str] = None,
        step: int = 1,
    ):
        self.user_id = user_id
        self.articles = articles or []
        self.source_ids = source_ids or []
        self.lang = lang
        self.with_audio = with_audio
        self.super_task_id = super_task_id
        self.summary = summary
        self.paragraphs = paragraphs or []
        self.step = step


@celery_app.task(bind=True)
def summarise_articles(
    self,
    user_id: str,
    articles: List[str],
    source_ids: List[str] = None,
    lang: str = "auto",
    with_audio: bool = True,
):
    """Orchestrate the creation of a summary from articles."""
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

    context = SummaryCreationContext(
        user_id=user_id,
        articles=articles,
        source_ids=source_ids or [],
        lang=lang,
        with_audio=with_audio,
        super_task_id=task_id,
    )

    workflow = chain(
        detect_language.s(context),
        generate_summary.s(),
        save_summary.s(),
        synthesize_audio_and_update.s(),
    )

    self.replace(workflow)


@shared_task(bind=True, max_retries=RETRIES, default_retry_delay=10)
def detect_language(self, context: SummaryCreationContext):
    """Detect the language of the provided articles."""
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

        if context.lang == "auto":
            context.lang = detect_language_from_text(" ".join(context.articles))
        context.step += 1
        return context
    except Exception as e:
        logger.warning(f"[User {context.user_id}] Language detection failed: {e}")
        if self.request.retries >= self.max_retries:
            # Final failure - mark workflow as failed
            _mark_workflow_failure(context, str(e))
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=RETRIES, default_retry_delay=10)
def generate_summary(self, context: SummaryCreationContext):
    """Generate a summary from the provided articles."""
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

        attempts = 3
        while True:
            try:
                content = gpt_service.create_summary(
                    article_texts=context.articles,
                    lang=context.lang,
                )
                break
            except Exception as e:
                logger.warning(
                    f"[User {context.user_id}] Error generating summary: {e}"
                )
                attempts -= 1
                if attempts <= 0:
                    raise RuntimeError(
                        "Failed to create summary after multiple attempts."
                    )

        context.paragraphs = split_text_into_paragraphs(content)
        context.step += 1
        return context
    except Exception as e:
        logger.warning(f"[User {context.user_id}] Summary generation failed: {e}")
        if self.request.retries >= self.max_retries:
            # Final failure - mark workflow as failed
            _mark_workflow_failure(context, str(e))
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=RETRIES, default_retry_delay=10)
def save_summary(self, context: SummaryCreationContext):
    """Save the generated summary to the database."""
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

        summary = Summary(source_ids=context.source_ids, content=context.paragraphs)
        db.save_summary(summary, context.user_id)
        context.summary = summary
        context.step += 1
        return context
    except Exception as e:
        logger.warning(f"[User {context.user_id}] Saving summary failed: {e}")
        if self.request.retries >= self.max_retries:
            # Final failure - mark workflow as failed
            _mark_workflow_failure(context, str(e))
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=RETRIES, default_retry_delay=10)
def synthesize_audio_and_update(self, context: SummaryCreationContext):
    """Synthesize audio for the summary and update the database."""
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

        if context.with_audio:
            audio_paths = asyncio.run(
                synthesize_summary_speech(context.paragraphs, lang=context.lang)
            )
            if audio_paths:
                context.summary.audio_zip_urls = audio_paths
                db.update_summary(context.summary, context.user_id)

        # cache the task state to indicate completion
        db.save_task_state(
            task_id=context.super_task_id,
            state="SUCCESS",
            meta=context.summary.id,
        )
        return context.summary.id
    except Exception as e:
        logger.warning(f"[User {context.user_id}] Audio synthesis failed: {e}")
        if self.request.retries >= self.max_retries:
            # Final failure - mark workflow as failed
            _mark_workflow_failure(context, str(e))
        raise self.retry(exc=e)


def _mark_workflow_failure(context: SummaryCreationContext, error_message: str):
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
                attempt=1,
            ),
        )

        # Save failure state to database
        db.save_task_state(
            task_id=context.super_task_id,
            state="FAILURE",
            meta=error_message,
        )
    except Exception as handler_error:
        logger.error(f"Error in workflow failure marker: {handler_error}")
