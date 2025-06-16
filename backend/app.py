import asyncio
import platform
import os
import sys
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import json
import requests
from codex_agent.repository_manager import clone_repository
from codex_agent.kernel_agent import execute_terminal_command
from codex_agent.codex_core_agent import complete_task

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

# Initialize FastAPI app
app = FastAPI(
    title="Combined API Server",
    description="API server combining local sandbox and browser automation functionality"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
SANDBOX_URL = "http://localhost:3000"

# Request Models
class CloneRequest(BaseModel):
    git_url: str
    project_name: str

class CommandRequest(BaseModel):
    task: str
    project_name: Optional[str] = None

class AutoAgentRequest(BaseModel):
    git_url: str
    command: str
    project_name: str

class BrowserTaskRequest(BaseModel):
    user_question: str
    user_name: Optional[str] = "Pluto Albert"
    end_all_sessions: Optional[bool] = False

class BrowserTaskResponse(BaseModel):
    live_view_url: str
    session_id: str
    status: str = "success"
    message: Optional[str] = None

# Active tasks dictionary for browser automation
active_tasks = {}

# Helper function to check container health
def check_container_health():
    try:
        response = requests.get(f"{SANDBOX_URL}/health")
        return response.ok
    except:
        return False

# Clone Repository Endpoint
@app.post("/clone")
async def clone_repository_endpoint(request: CloneRequest):
    """
    Clone a git repository into the sandbox container
    """
    result = clone_repository(request.git_url, request.project_name)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

# Execute Command Endpoint
@app.post("/execute")
async def execute_command(request: CommandRequest):
    """
    Execute a task using the codex core agent
    """
    try:
        print("\n[INFO] Received execute request:")
        print(f"Task: {request.task}")
        print(f"Project name: {request.project_name}")
        
        # Use the complete_task function to execute the task
        print("\n[INFO] Starting codex core agent...")
        command_history = complete_task(request.task)
        
        if not command_history:
            print("\n[ERROR] No commands were executed successfully")
            raise HTTPException(status_code=500, detail="No commands were executed successfully")
            
        # Get the last command's output
        last_command, last_output = command_history[-1]
        
        print("\n[INFO] Task completed. Final output:")
        print("-" * 50)
        print(last_output)
        print("-" * 50)
        
        return {
            "success": True,
            "command_history": command_history,
            "stdout": last_output,
            "stderr": ""
        }
    except Exception as e:
        print(f"\n[ERROR] Error in execute endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Browser Automation Endpoints
@app.post("/api/run-browser-task", response_model=BrowserTaskResponse)
async def run_browser_task(request: BrowserTaskRequest, background_tasks: BackgroundTasks):
    """
    Run a browser automation task and return immediately with the session information.
    The actual browser automation continues in the background.
    """
    try:
        logger.info(f"Received browser task request: {request.user_question}")
        logger.info("Starting Anchor Browser session...")
        from web_agent.anchor_browser.session_management.anchor_session_start import start_anchor_session

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
                from web_agent.openai_test import run_search
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

@app.post("/api/shutdown-all", response_model=dict)
def shutdown_all_browser_sessions():
    """
    End all active Anchor Browser sessions.
    """
    try:
        logger.info("Received shutdown request for all sessions")
        from web_agent.anchor_browser.session_management.anchor_browser_end_all_sessions import end_all_anchor_sessions
        
        result = end_all_anchor_sessions()
        logger.info("All sessions shutdown successful")
        
        return {"status": "success", "message": "All sessions terminated successfully", "result": result}
    except Exception as e:
        logger.error(f"Error shutting down all browser sessions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error shutting down all browser sessions: {str(e)}"
        )

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    logger.info("Combined API Server is starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    logger.info("Combined API Server is shutting down...")

if __name__ == "__main__":
    import uvicorn
    print("\n[INFO] Starting FastAPI server...")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )