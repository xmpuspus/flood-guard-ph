import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api import chat, news, search
from backend.config import settings
from backend.services.llm_service import LLMService
from backend.services.news_service import NewsService
from backend.services.project_service import ProjectService
from backend.services.vector_service import VectorService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FloodGuard PH API",
    description="AI-powered Philippine flood control project explorer",
    version="1.0.0",
)

# CORS
origins = settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services (initialized on startup)
project_service: ProjectService = None
vector_service: VectorService = None
news_service: NewsService = None
llm_service: LLMService = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global project_service, vector_service, news_service, llm_service

    logger.info("Starting FloodGuard PH API...")

    try:
        # Initialize services
        logger.info("Initializing project service...")
        project_service = ProjectService()

        logger.info("Initializing vector service...")
        vector_service = VectorService()
        vector_service.get_or_create_projects_collection()
        vector_service.get_or_create_news_collection()

        logger.info("Initializing news service...")
        news_service = NewsService(vector_service)

        logger.info("Initializing LLM service...")
        llm_service = LLMService(
            project_service=project_service,
            vector_service=vector_service,
            news_service=news_service,
        )

        # Store in app state
        app.state.project_service = project_service
        app.state.vector_service = vector_service
        app.state.news_service = news_service
        app.state.llm_service = llm_service

        logger.info("✓ All services initialized successfully")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise


# Include routers
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(news.router)

# Serve static files
app.mount(
    "/assets",
    StaticFiles(directory="demo_ui/assets"),
    name="assets",
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FloodGuard PH API",
        "version": "1.0.0",
        "docs": "/docs",
        "demo": "/demo_ui",
    }


@app.get("/demo_ui")
async def serve_ui():
    """Serve demo UI"""
    return FileResponse("demo_ui/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "projects_loaded": len(project_service.df)
        if project_service and project_service.df is not None
        else 0,
        "vector_db_ready": vector_service is not None,
    }