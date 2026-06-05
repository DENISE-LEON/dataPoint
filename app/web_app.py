from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.file_router import router as file_router
from app.api.report_router import router as report_router
from app.core.report_manager import scheduler, generate_scheduled_reports

print("[TRACE] web_app module import started")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize resources here (e.g., database connections, schedulers)
    print("[TRACE] FastAPI lifespan startup: starting scheduler")
    scheduler.start()  # Start the scheduler when the app starts
    generate_scheduled_reports()  # Schedule the reports
    yield  # This is where the application runs
    # Clean up resources here (e.g., close database connections, stop schedulers)
    print("[TRACE] FastAPI lifespan shutdown: stopping scheduler")
    scheduler.shutdown()  # Stop the scheduler when the app shuts down


app = FastAPI(lifespan=lifespan)
app.include_router(file_router, prefix="/files")
app.include_router(report_router, prefix="/reports")
print("[TRACE] Routers registered: /files and /reports")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],
)
print("[TRACE] CORS middleware configured")