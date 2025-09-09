# main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import router as api_router
from contextlib import asynccontextmanager
from database import db
import logging


# configure the root logger to show INFO+ messages
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
logging.getLogger("azure").setLevel(logging.WARNING)

app = FastAPI()

# Startup event: DB check
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    db.ping_database()
    yield
    
app = FastAPI(lifespan=lifespan)

# Register all routes from app.routes
app.include_router(api_router)

# Serve static files (like audio output)
app.mount("/static", StaticFiles(directory="static"), name="static")
