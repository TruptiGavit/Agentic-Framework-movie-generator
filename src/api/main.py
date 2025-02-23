from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path
import asyncio
import uuid

from src.core.system_integrator import SystemIntegrator
from .models import (
    ProjectCreate, ProjectStatus, ProjectUpdate,
    ExportSettings, BackupCreate, SystemMetrics
)
from .dependencies import get_system
from .auth import get_current_user
from .websocket import websocket_manager
from .error_handling import ErrorManager, MovieGeneratorError

app = FastAPI(
    title="Movie Generator API",
    description="API for the Movie Generator Agentic Framework",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("movie_generator.api")

# Initialize error manager
error_manager = ErrorManager()

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    system = await get_system()
    await system.initialize_system()

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown system."""
    system = await get_system()
    await system.shutdown_system()

# Project endpoints
@app.post("/projects/", response_model=Dict[str, str])
async def create_project(
    project: ProjectCreate,
    background_tasks: BackgroundTasks,
    system: SystemIntegrator = Depends(get_system)
):
    """Create a new movie generation project."""
    try:
        project_id = await system.create_project(project.dict())
        return {"project_id": project_id}
    except ValidationError as e:
        raise
    except Exception as e:
        raise ProcessingError(
            message="Failed to create project",
            stage="project_creation",
            details={"error": str(e)}
        )

@app.get("/projects/{project_id}/status", response_model=ProjectStatus)
async def get_project_status(
    project_id: str,
    system: SystemIntegrator = Depends(get_system)
):
    """Get project status."""
    try:
        status = await system.get_project_status(project_id)
        return ProjectStatus(**status)
    except KeyError:
        raise ResourceNotFoundError("Project", project_id)
    except Exception as e:
        raise ProcessingError(
            message="Failed to get project status",
            stage="status_check",
            details={"project_id": project_id, "error": str(e)}
        )

@app.post("/projects/{project_id}/export")
async def export_project(
    project_id: str,
    settings: ExportSettings,
    system: SystemIntegrator = Depends(get_system)
):
    """Export project in specified format."""
    try:
        result = await system.export_project(
            project_id,
            format=settings.format,
            output_path=Path(settings.output_path)
        )
        return result
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Backup endpoints
@app.post("/projects/{project_id}/backup")
async def create_backup(
    project_id: str,
    backup: BackupCreate,
    system: SystemIntegrator = Depends(get_system)
):
    """Create project backup."""
    try:
        result = await system.backup_manager.create_backup(
            project_id,
            backup_type=backup.type
        )
        return result
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# System monitoring endpoints
@app.get("/system/metrics", response_model=SystemMetrics)
async def get_system_metrics(
    system: SystemIntegrator = Depends(get_system)
):
    """Get current system metrics."""
    try:
        metrics = await system.system_monitor.get_system_metrics()
        return SystemMetrics(**metrics)
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add WebSocket endpoints
@app.websocket("/ws/projects/{project_id}")
async def project_websocket(
    websocket: WebSocket,
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """WebSocket endpoint for project updates."""
    channel = f"projects_{project_id}"
    
    try:
        await websocket_manager.connect(websocket, channel)
        
        while True:
            try:
                # Receive and process messages
                data = await websocket.receive_json()
                
                # Handle client messages if needed
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
            except WebSocketDisconnect:
                websocket_manager.disconnect(websocket, channel)
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()

@app.websocket("/ws/system")
async def system_websocket(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user)
):
    """WebSocket endpoint for system metrics updates."""
    try:
        await websocket_manager.connect(websocket, "system")
        
        # Start metrics broadcasting
        while True:
            try:
                metrics = await get_system().system_monitor.get_system_metrics()
                await websocket.send_json({
                    "type": "metrics",
                    "data": metrics
                })
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except WebSocketDisconnect:
                websocket_manager.disconnect(websocket, "system")
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()

# Add exception handlers
@app.exception_handler(MovieGeneratorError)
async def movie_generator_error_handler(request: Request, exc: MovieGeneratorError):
    return await error_manager.handle_error(request, exc)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return await error_manager.handle_error(request, exc)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return await error_manager.handle_error(request, exc)

# Add middleware to attach request ID
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response 