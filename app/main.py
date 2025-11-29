"""FilePulse - Secure file sharing with automatic expiry."""
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import upload, download
from app.utils.scheduler import FileCleanupScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize cleanup scheduler
scheduler = FileCleanupScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting FilePulse application...")
    
    # Log configuration
    logger.info(f"Configuration loaded:")
    logger.info(f"  - Upload directory: {settings.upload_dir}")
    logger.info(f"  - Max file size: {settings.max_file_size:,} bytes ({settings.max_file_size / 1024 / 1024:.1f} MB)")
    logger.info(f"  - File expiry: {settings.file_expiry_days} days")
    logger.info(f"  - Debug mode: {settings.debug}")
    logger.info(f"  - Docs enabled: {settings.enable_docs}")
    
    # Create upload directory
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Upload directory: {upload_dir.absolute()}")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Start cleanup scheduler
    scheduler.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down FilePulse application...")
    scheduler.shutdown()


# Create FastAPI app
app = FastAPI(
    title="FilePulse",
    description="Secure file sharing with automatic expiry",
    version="2.0.0",
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    lifespan=lifespan
)

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Setup templates - pointing to static directory
templates = Jinja2Templates(directory="app/static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (CSS, JS only - no HTML)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API routers
app.include_router(upload.router)
app.include_router(download.router)


# Template routes with config injection
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render homepage with server config injected."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "max_file_size": settings.max_file_size,
            "file_expiry_days": settings.file_expiry_days
        }
    )


@app.get("/download.html", response_class=HTMLResponse)
async def download_page(request: Request):
    """Render download page."""
    return templates.TemplateResponse(
        request=request,
        name="download.html",
        context={}
    )


# Legacy static file routes (redirects)
@app.get("/index.html", response_class=HTMLResponse)
async def index_redirect(request: Request):
    """Redirect to homepage."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "max_file_size": settings.max_file_size,
            "file_expiry_days": settings.file_expiry_days
        }
    )

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "FilePulse"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False
    )
