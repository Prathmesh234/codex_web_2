from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
import sys
import logging
from typing import Optional
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set the correct event loop policy for Windows
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Add the parent directory to sys.path to ensure imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import the start_browser_agent function
from start_browser_agent import start_browser_agent

# Create FastAPI app
app = FastAPI(title="Browser Agent API", description="API for running browser automation tasks")

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request model
class BrowserTaskRequest(BaseModel):
    user_question: str
    user_name: Optional[str] = "Pluto Albert"
    end_all_sessions: Optional[bool] = False

# Define response model
class BrowserTaskResponse(BaseModel):
    live_view_url: str
    session_id: str
    status: str = "success"
    message: Optional[str] = None

# Active tasks dictionary to keep track of running tasks
active_tasks = {}

@app.post("/api/run-browser-task", response_model=BrowserTaskResponse)
async def run_browser_task(request: BrowserTaskRequest, background_tasks: BackgroundTasks):
    """
    Run a browser automation task and return immediately with the session information.
    The actual browser automation continues in the background.
    """
    try:
        logger.info(f"Received browser task request: {request.user_question}")
        logger.info("Starting Anchor Browser session...")
        from anchor_browser.session_management.anchor_session_start import start_anchor_session

        # Start the browser session
        session_info = start_anchor_session()
        cdp_url = session_info['data']['cdp_url']
        live_view_url = session_info['data']['live_view_url']
        session_id = session_info['data']['id']

        logger.info(f"Session started - ID: {session_id}")
        logger.info(f"CDP URL: {cdp_url}")
        logger.info(f"Live View URL: {live_view_url}")

        # Add the task to run in background without waiting for completion
        async def run_search_background():
            try:
                from openai_test import run_search
                await run_search(
                    user_task=request.user_question,
                    user_name=request.user_name,
                    cdp_url=cdp_url
                )
                logger.info(f"Background task completed for session: {session_id}")
            except Exception as e:
                logger.error(f"Error in background task for session {session_id}: {str(e)}", exc_info=True)

        # Schedule the background task
        background_tasks.add_task(run_search_background)
        
        # Return immediately with the session information
        return BrowserTaskResponse(
            live_view_url=live_view_url,
            session_id=session_id,
            status="running",
            message="Browser session started. Task is running in the background."
        )
    except Exception as e:
        logger.error(f"Error starting browser task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error running browser task: {str(e)}"
        )

# Define a background task function to run browser agent
async def run_browser_task_background(task_id: str, request: BrowserTaskRequest):
    try:
        live_view_url = await start_browser_agent(
            user_task=request.user_question,
            user_name=request.user_name,
            end_all_sessions=request.end_all_sessions
        )
        
        # Update task status
        session_id = live_view_url.split("sessionId=")[-1] if "sessionId=" in live_view_url else "unknown"
        active_tasks[task_id] = {
            "status": "completed",
            "live_view_url": live_view_url,
            "session_id": session_id
        }
    except Exception as e:
        # Update task status with error
        active_tasks[task_id] = {
            "status": "error",
            "error": str(e)
        }

@app.post("/api/run-browser-task-async")
async def run_browser_task_async(request: BrowserTaskRequest, background_tasks: BackgroundTasks):
    """
    Run a browser automation task asynchronously.
    Returns a task ID that can be used to check the status of the task.
    """
    # Generate a unique task ID
    task_id = f"task_{len(active_tasks) + 1}"
    
    # Initialize task status
    active_tasks[task_id] = {"status": "running"}
    
    # Add the task to background tasks
    background_tasks.add_task(run_browser_task_background, task_id, request)
    
    return {"task_id": task_id, "status": "running"}

@app.get("/api/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a running or completed task.
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return active_tasks[task_id]

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    print("Browser Agent API is starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    print("Browser Agent API is shutting down...")


@app.post("/api/shutdown-all", response_model=dict)
def shutdown_all_browser_sessions():
    """
    End all active Anchor Browser sessions.
    
    Returns:
        A success message if all sessions were terminated successfully
    """
    try:
        logger.info("Received shutdown request for all sessions")
        from anchor_browser.session_management.anchor_browser_end_all_sessions import end_all_anchor_sessions
        
        result = end_all_anchor_sessions()
        logger.info("All sessions shutdown successful")
        
        return {"status": "success", "message": "All sessions terminated successfully", "result": result}
    except Exception as e:
        logger.error(f"Error shutting down all browser sessions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error shutting down all browser sessions: {str(e)}"
        )
