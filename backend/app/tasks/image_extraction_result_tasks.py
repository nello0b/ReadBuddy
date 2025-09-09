# app/tasks/image_extraction_subtasks.py

from celery import shared_task, chord, chain
from azure.ai.documentintelligence.models import AnalyzeResult
from app.utils.celery_helpers import update_super_task_state, abort_if_revoked
from celery_app import celery_app
from config import MIN_DIMENSION, MAX_DIMENSION
from app.utils.ocr import extract_text_from_image
from app.utils.language import detect_language_from_text
from app.utils.tts import synthesize_speech_from_analyzeresult
from app.utils.gpt import classify_text
from app.utils.resize_image import smart_resize_image
from app.models.image_extraction_result import ImageExtractionResult
from app.models.task_status import TaskStatus
from typing import List
from database import db
from PIL import Image
import os
import logging
import asyncio

logger = logging.getLogger(__name__)

state_info = [
    {"description": "Setting Up Image Extraction Flow"},
    {"description": "Resizing Image (if needed)"},
    {"description": "Extracting text"},
    {"description": "Detecting Language"},
    {"description": "Synthesizing Audio and Classifying Text"},
    {"description": "Saving Result and Cleaning Up"}
]

out_of_steps = len(state_info) - 1  # Total number of steps in the workflow

RETRIES = 3  # Number of retries for each task
DELEYS = 0  # Default retry delay in seconds

class ImageExtractionContext:
    def __init__(
        self,
        user_id: str = None,
        temp_file_path: str = None,
        super_task_id: str = None,
        ocr_result: AnalyzeResult = None,
        content: str = None,
        lang: str = None,
        category: str = None,
        audio_zip_paths: List[str] = None,
        step: int = 1
    ):
        self.user_id = user_id
        self.temp_file_path = temp_file_path
        self.super_task_id = super_task_id
        self.ocr_result = ocr_result
        self.content = content
        self.lang = lang
        self.category = category
        self.audio_zip_paths = audio_zip_paths
        self.step = step
    
    # Set attributes in out object if they are not already set and are set in the context variable
    def mass_set(self, context: 'ImageExtractionContext'):
        for attr, value in context.__dict__.items():
            if not hasattr(self, attr) or getattr(self, attr) is None:
                setattr(self, attr, value)

def _mark_workflow_failure(context: ImageExtractionContext, error_message: str):
    """Helper function to mark workflow as failed and cleanup"""
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
        
        # Clean up temp file
        try:
            if context.temp_file_path and os.path.exists(context.temp_file_path):
                os.remove(context.temp_file_path)
                logger.info(f"[User {context.user_id}] Cleaned up temp file: {context.temp_file_path}")
        except Exception as cleanup_error:
            logger.warning(f"[User {context.user_id}] Failed to cleanup temp file: {cleanup_error}")
            
    except Exception as handler_error:
        logger.error(f"Error in workflow failure marker: {handler_error}")


@celery_app.task(bind=True)
def create_and_save_image_extraction_result(self, user_id: str, temp_file_path: str):
    """
    Create and save an image extraction result by orchestrating multiple subtasks.
    This function orchestrates the workflow of OCR, language detection, audio synthesis,
    text classification, and saving the final result.
    
    :param user_id: The ID of the user who initiated the task.
    :param temp_file_path: The path to the temporary image file to be processed.
    :return: The ID of the ImageExtractionResult created.
    """
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
    
    context = ImageExtractionContext(
        user_id=user_id,
        temp_file_path=temp_file_path,
        super_task_id=task_id
    )

    # Step 3a and 3b run in parallel via chord
    parallel_tasks = [
        classify_extracted_text.s(),
        synthesize_audio.s()
    ]

    # Combine everything
    full_workflow = chain(
        resize_image.s(context),
        ocr_image.s(),
        detect_language.s(),
        update_state.s(),
        chord(parallel_tasks, unify_context.s()),
        save_result_and_cleanup.s()
    )
    
    # The global failure handler is already assigned to this task
    # No need for additional error linking
    
    self.replace(full_workflow)

@shared_task(bind=True, max_retries=RETRIES, default_retry_delay=DELEYS)
def resize_image(self, context: ImageExtractionContext):
    abort_if_revoked(self.request.id, context.super_task_id)
    try:
        update_super_task_state(
            context.super_task_id, 
            state="PROGRESS", 
            meta=TaskStatus.get_meta(
                step=context.step, 
                out_of=out_of_steps, 
                description=state_info[context.step]["description"],
                user_id=context.user_id, 
                attempt=self.request.retries + 1
            )
        )
        
        with Image.open(context.temp_file_path) as img:
            width, height = img.size
            
        if width < MIN_DIMENSION or height < MIN_DIMENSION or width > MAX_DIMENSION or height > MAX_DIMENSION:
            logger.info(f"[User {context.user_id}] Resizing image from {width}x{height} to max {MAX_DIMENSION}x{MAX_DIMENSION}")
            
            # Resize the image if it is out of bounds
            resized_path = smart_resize_image(context.temp_file_path, MAX_DIMENSION, MIN_DIMENSION)
            
            # Verify the resized file was created successfully
            if not os.path.exists(resized_path):
                raise ValueError(f"Resized image was not created at {resized_path}")
            
            # Only delete original after confirming resize worked
            try:
                os.remove(context.temp_file_path)
                context.temp_file_path = resized_path
                logger.info(f"[User {context.user_id}] Successfully resized and replaced image")
            except OSError as e:
                # If we can't delete original, clean up the resized file
                try:
                    os.remove(resized_path)
                except:
                    pass
                raise ValueError(f"Failed to replace original file: {e}")
        else:
            logger.info(f"[User {context.user_id}] Image dimensions {width}x{height} are within bounds, no resize needed")
            
        context.step += 1  # Update step to next
        return context
    except Exception as e:
        logger.warning(f"[User {context.user_id}] Resize failed: {e}")
        if self.request.retries >= self.max_retries:
            # Final failure - mark workflow as failed
            _mark_workflow_failure(context, str(e))
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=RETRIES, default_retry_delay=DELEYS)
def ocr_image(self, context: ImageExtractionContext):
    abort_if_revoked(self.request.id, context.super_task_id)
    try:
        update_super_task_state(
            context.super_task_id, 
            state="PROGRESS", 
            meta=TaskStatus.get_meta(
                step=context.step, 
                out_of=out_of_steps, 
                description=state_info[context.step]["description"],
                user_id=context.user_id, 
                attempt=self.request.retries + 1
            )
        )
        result = extract_text_from_image(context.temp_file_path)
        content = result.get("content", "")
        if not content:
            raise ValueError("⚠️No text extracted from image")
        
        print(f"📖Extracted content: #{content[:200]}#...")  # Log first 200 characters for debugging
        context.ocr_result = result
        context.content = content
        context.step += 1  # Update step to next
        return context
    except Exception as e:
        logger.warning(f"[User {context.user_id}] OCR failed: {e}")
        if self.request.retries >= self.max_retries:
            # Final failure - mark workflow as failed
            _mark_workflow_failure(context, str(e))
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=RETRIES, default_retry_delay=DELEYS)
def detect_language(self, context: ImageExtractionContext):
    abort_if_revoked(self.request.id, context.super_task_id)
    try:
        update_super_task_state(
            context.super_task_id, 
            state="PROGRESS",
            meta=TaskStatus.get_meta(
                step=context.step,
                out_of=out_of_steps,
                description=state_info[context.step]["description"],
                user_id=context.user_id,
                attempt=self.request.retries + 1
            )
        )
        lang = detect_language_from_text(context.content)
        print(f"🌐Detected language: {lang}")
        context.lang = lang
        context.step += 1  # Update step to next
        return context
    except Exception as e:
        logger.warning(f"[User {context.user_id}] Language detection failed: {e}")
        if self.request.retries >= self.max_retries:
            # Final failure - mark workflow as failed
            _mark_workflow_failure(context, str(e))
        raise self.retry(exc=e)

@shared_task(bind=True)
def update_state(self, context: ImageExtractionContext):
    """Update task progress state while passing through received context."""
    abort_if_revoked(self.request.id, context.super_task_id)
    update_super_task_state(
        context.super_task_id,
        state="PROGRESS",
        meta=TaskStatus.get_meta(
            step=context.step,
            out_of=out_of_steps,
            description=state_info[context.step]["description"],
            user_id=context.user_id,
            attempt=1,
        )
    )
    return context

@shared_task(bind=True, max_retries=RETRIES, default_retry_delay=DELEYS)
def synthesize_audio(self, context: ImageExtractionContext):
    """Generate audio from OCR results."""
    abort_if_revoked(self.request.id, context.super_task_id)
    try:
        audio_zip_paths = asyncio.run(
            synthesize_speech_from_analyzeresult(result=context.ocr_result, lang=context.lang)
        )
        context.audio_zip_paths = audio_zip_paths
        return context
    except Exception as e:
        logger.warning(f"[User {context.user_id}] Audio synthesis failed: {e}")
        if self.request.retries >= self.max_retries:
            # Final failure - mark workflow as failed
            _mark_workflow_failure(context, str(e))
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=RETRIES, default_retry_delay=DELEYS)
def classify_extracted_text(self, context: ImageExtractionContext):
    """Classify the extracted text according to the user's categories."""
    abort_if_revoked(self.request.id, context.super_task_id)
    try:
        categories = db.get_user_categories(context.user_id)
        category = classify_text(
            input_text=context.content, 
            categories=categories, 
            lang=context.lang
        )
        context.category = category
        return context
    except Exception as e:
        logger.warning(f"[User {context.user_id}] Text classification failed: {e}")
        if self.request.retries >= self.max_retries:
            # Final failure - mark workflow as failed
            _mark_workflow_failure(context, str(e))
        raise self.retry(exc=e)
    
@shared_task(bind=True)
def unify_context(self, contexts: List[ImageExtractionContext]):
    """Unify multiple contexts into a single context for the next step."""
    context = contexts[0]  # Assuming all contexts are the same for this step
    abort_if_revoked(self.request.id, context.super_task_id)
    for other_context in contexts[1:]:
        context.mass_set(other_context)  # Merge attributes from other contexts
    context.step += 1  # Increment step
    return context

@shared_task(bind=True, max_retries=RETRIES, default_retry_delay=DELEYS)
def save_result_and_cleanup(self, context: ImageExtractionContext):
    """Finalize the extraction result and clean up temporary files."""
    abort_if_revoked(self.request.id, context.super_task_id)
    try:
        update_super_task_state(
            context.super_task_id,
            state="PROGRESS",
            meta=TaskStatus.get_meta(
                step=context.step,
                out_of=out_of_steps,
                description=state_info[context.step]["description"],
                user_id=context.user_id,
                attempt=self.request.retries + 1,
            )
        )

        # Merge results into the main context
        context.category = context.category
        context.audio_zip_paths = context.audio_zip_paths

        result = ImageExtractionResult(
            text_data=context.ocr_result,
            audio_zip_urls=context.audio_zip_paths,
            file_path=context.temp_file_path,
            category=context.category,
        )
        db.save_image_extraction_result(result, context.user_id)
        
         # cache the task state to indicate completion
        db.save_task_state(
            task_id=context.super_task_id,
            state="SUCCESS",
            meta=result.id,
        )
    except Exception as e:
        logger.warning(f"[User {context.user_id}] Saving result failed: {e}")
        if self.request.retries >= self.max_retries:
            # Final failure - mark workflow as failed
            _mark_workflow_failure(context, str(e))
        raise self.retry(exc=e)

    try:
        os.remove(context.temp_file_path)
    except Exception as e:
        logger.warning(f"[User {context.user_id}] Failed to delete temp file: {e}")

    return result.id