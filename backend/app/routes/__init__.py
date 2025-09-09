from fastapi import APIRouter
from app.routes.auth_routes import router as auth_router
from app.routes.image_upload import router as image_router
from app.routes.delete import router as delete_router
from app.routes.get_history import router as history_router
from app.routes.get_image_extraction_result import router as image_extraction_result_router
from app.routes.category import router as category_router
from app.routes.quizzes import router as create_quiz_router
from app.routes.glossary import router as glossary_router
from app.routes.summaries import router as summaries_router
from app.routes.task_routes import router as task_router


router = APIRouter()
router.include_router(auth_router)
router.include_router(image_router)
router.include_router(delete_router)
router.include_router(history_router)
router.include_router(image_extraction_result_router)
router.include_router(category_router)
router.include_router(create_quiz_router)
router.include_router(glossary_router)
router.include_router(summaries_router)
router.include_router(task_router)
