import asyncio
import platform
import os
import sys
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends, Body, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import json
import requests
from codex_agent.repository_manager import clone_repository
from codex_agent.kernel_agent import execute_terminal_command, ensure_container_running, check_container_health
from codex_agent.codex_core_agent import complete_task
from codex_agent.azure_queue import AzureQueueManager
from fastapi import Cookie
from starlette.websockets import WebSocketState
from contextlib import contextmanager
import time

# Will be set to the Azure storage connection string upon sandbox deployment
azure_connection_string: Optional[str] = None


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Reduce Azure SDK logging verbosity
azure_logger = logging.getLogger("azure.core.pipeline.policies.http_logging_policy")
azure_logger.setLevel(logging.WARNING)
azure_storage_logger = logging.getLogger("azure.storage")
azure_storage_logger.setLevel(logging.WARNING)

# Load environment variables
load_dotenv()

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

# Add CORS middleware with logging
logger.info("Setting up CORS middleware for FastAPI app")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
SANDBOX_URL = "http://localhost:3000"

# GitHub OAuth configuration
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = os.getenv(
    "GITHUB_REDIRECT_URI",
    "http://localhost:8000/auth/github/callback",
)

# Request Models
class CloneRequest(BaseModel):
    git_url: str
    project_name: str

class CommandRequest(BaseModel):
    task: str
    repo_url: str
    project_name: Optional[str] = None
    container_type: Optional[str] = "azure"  # "local" or "azure", defaults to "azure"

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

class OrchestratorRequest(BaseModel):
    task: str
    browser_count: Optional[int] = None
    repo_info: dict
    github_token: Optional[str] = None
    documentation: Optional[str] = None
    pullRequestMessage: Optional[str] = None
    pullRequestDescription: Optional[str] = None

# Active tasks dictionary for browser automation
active_tasks = {}

# Global dict to hold queues for streaming web agent outputs per session
web_agent_stream_queues = {}

# Remove the queue-based streaming and use direct WebSocket send for each session
web_agent_websockets = {}  # session_id -> websocket

# Add a global dict to store session parameters
web_agent_session_params = {}  # session_id -> {user_task, user_name, cdp_url}

async def publish_web_agent_thought(session_id: str, message: str):
    websocket = web_agent_websockets.get(session_id)
    if websocket:
        try:
            if websocket.application_state == WebSocketState.CONNECTED:
                await websocket.send_text(message)
        except Exception as e:
            # Remove disconnected websocket
            if session_id in web_agent_websockets:
                del web_agent_websockets[session_id]

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
    global azure_connection_string
    try:
        print("\n[INFO] Received execute request:")
        print(f"Task: {request.task}")
        print(f"Repo URL: {request.repo_url}")
        print(f"Project name: {request.project_name}")
        print(f"Container type: {request.container_type}")
        
        # Extract project name from repo URL if not provided
        if not request.project_name:
            project_name = request.repo_url.split('/')[-1].replace('.git', '')
        else:
            project_name = request.project_name
        
        print(f"Using project name: {project_name}")
        
        # Check container status only for local container type
        container_running = True  # Default to true for Azure
        
        if request.container_type == "local":
            container_running = False
            
            try:
                # Check if container is running
                container_running = ensure_container_running()
                
                # Wait a bit for container to be ready
                await asyncio.sleep(2)
                
                # Check health
                if not check_container_health():
                    container_running = False
                    
            except Exception as e:
                print(f"[ERROR] Container check failed: {str(e)}")
                container_running = False
            
            print(f"[INFO] Local container running: {container_running}")
            
            if not container_running:
                return {
                    "success": False,
                    "container_running": container_running,
                    "message": "Local container is not running. Cannot execute task."
                }
        else:
            print(f"[INFO] Using {request.container_type} container - skipping local container check")
        
        # For Azure container, deploy sandbox and get connection string
        connection_string = None
        if request.container_type == "azure":
            print("\n[INFO] Deploying Azure sandbox...")
            try:
                from sandbox_image.deploy_sandbox import deploy_sandbox
                deployment_result = deploy_sandbox()
                
                if deployment_result.get("status") == "success":
                    connection_string = deployment_result.get("storage_connection_string")
                    # Store connection string for WebSocket streaming
                    azure_connection_string = connection_string
                    print(f"[INFO] Azure sandbox deployed successfully")
                    print(f"[INFO] Deployment ID: {deployment_result.get('id')}")
                else:
                    print(f"[ERROR] Failed to deploy Azure sandbox: {deployment_result.get('message')}")
                    return {
                        "success": False,
                        "message": f"Failed to deploy Azure sandbox: {deployment_result.get('message')}"
                    }
            except Exception as e:
                print(f"[ERROR] Error deploying Azure sandbox: {str(e)}")
                return {
                    "success": False,
                    "message": f"Error deploying Azure sandbox: {str(e)}"
                }
        
        # Start task in background for real-time streaming
        print("\n[INFO] Starting codex core agent...")
        
        # Store connection string for websocket access
        azure_connection_string = connection_string
        
        # Start the task in background
        task_id = f"task_{int(time.time())}"
        
        def run_task_in_background():
            try:
                command_history = complete_task(request.task, request.repo_url, project_name, request.container_type, connection_string)
                print(f"[INFO] Task {task_id} completed with {len(command_history)} commands")
            except Exception as e:
                print(f"[ERROR] Task {task_id} failed: {str(e)}")
        
        # Start in background thread
        import threading
        threading.Thread(target=run_task_in_background, daemon=True).start()
        
        print(f"[INFO] Task {task_id} started in background")
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "Task started. Commands will stream in real-time.",
            "should_stream": True,
            "task_completed": False
        }
    except Exception as e:
        print(f"\n[ERROR] Error in execute endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Browser Automation Endpoints
@app.post("/api/run-browser-task", response_model=BrowserTaskResponse)
async def run_browser_task(request: BrowserTaskRequest):
    """
    Run a browser automation task and return immediately with the session information.
    The actual browser automation will be started when the WebSocket connects.
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

        # Store session parameters for use by the WebSocket handler
        web_agent_session_params[session_id] = {
            'user_task': request.user_question,
            'user_name': request.user_name,
            'cdp_url': cdp_url
        }

        # Return immediately with the session information
        return BrowserTaskResponse(
            live_view_url=live_view_url,
            session_id=session_id,
            status="running",
            message="Browser session started. Task will run when WebSocket connects."
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



@app.get("/api/container/status")
def container_status():
    """Check if Azure container is initialized and connection string is available"""
    return JSONResponse({
        "initialized": azure_connection_string is not None,
        "connection_available": azure_connection_string is not None
    })

@app.get("/api/user/github-connected")
def github_connected(request: Request):
    # TODO: Check Appwrite session for GitHub connection status
    # Placeholder: always return False (implement with Appwrite session check)
    return JSONResponse({"connected": False})

@app.get("/api/appwrite-test")
def appwrite_test():
    try:
        # Try to get the current user (will fail if no session cookie, but proves connectivity)
        result = account.get()
        return {"status": "success", "user": result}
    except Exception as e:
        logger.error(f"Appwrite test error: {str(e)}")
        return {"status": "error", "error": str(e)}


@app.websocket("/ws/commands")
async def websocket_commands(websocket: WebSocket):
    """Stream commands from the Azure queue and their responses over WebSocket."""
    await websocket.accept()
    conn_str = azure_connection_string or os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if not conn_str:
        await websocket.close(code=1008)
        return
    queue_mgr = AzureQueueManager(conn_str)
    task_completed = False
    consecutive_empty_polls = 0
    max_empty_polls = 30  # Stop after 30 consecutive empty polls (30 seconds)
    processed_ids = set()
    
    try:
        while not task_completed:
            cmd = await asyncio.to_thread(queue_mgr.peek_command)
            if not cmd:
                consecutive_empty_polls += 1
                if consecutive_empty_polls >= max_empty_polls:
                    logger.info("No commands received for 30 seconds, stopping polling")
                    break
                await asyncio.sleep(1)
                continue

            message_id = cmd.get("message_id")
            if message_id in processed_ids:
                await asyncio.sleep(1)
                continue
            processed_ids.add(message_id)

            consecutive_empty_polls = 0  # Reset counter when we get a command
            await websocket.send_json({"type": "command", "data": cmd})

            try:
                if message_id is None:
                    logger.warning("Command has no message_id, skipping response wait")
                    continue
                resp = await asyncio.to_thread(queue_mgr.wait_for_response, message_id)
                await websocket.send_json({"type": "response", "data": resp})
                
                # Check if this indicates task completion
                if resp.get("status") == "completed" or resp.get("task_completed") == True:
                    task_completed = True
                    logger.info("Task completed, stopping command polling")
                    break
                    
            except TimeoutError:
                logger.warning(f"Timeout waiting for response to command {cmd.get('message_id')}")
                await websocket.send_json({"type": "error", "data": {"message": "Command timeout"}})
                break
            except Exception as e:
                logger.error(f"Error processing command response: {str(e)}")
                await websocket.send_json({"type": "error", "data": {"message": str(e)}})
                break
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in websocket_commands: {str(e)}")
    finally:
        logger.info("Closing WebSocket connection")

@app.post("/api/orchestrator")
async def orchestrator_endpoint(request: OrchestratorRequest):
    """
    Orchestrate a task using the orchestrator agent.
    """
    try:
        logger.info(f"[Orchestrator] Task: {request.task}")
        logger.info(f"[Orchestrator] Browser Count: {request.browser_count}")
        logger.info(f"[Orchestrator] Repo Info: {request.repo_info}")
        logger.info(f"[Orchestrator] GitHub Token: {'Present' if request.github_token else 'Not provided'}")
        
        # Prioritize environment token over passed token
        github_token = os.getenv("GITHUB_TOKEN") or request.github_token
        logger.info(f"[Orchestrator] Using GitHub Token: {'Environment token' if os.getenv('GITHUB_TOKEN') else 'Passed token' if github_token else 'None'}")
        
        # Import and use the orchestrator
        from orchestrator.orchestrator import run_orchestrator
        
        # Run the orchestrator
        browser_count = request.browser_count if request.browser_count is not None else 1
        result = await run_orchestrator(
            task_name=request.task,
            repo_info=request.repo_info,
            browser_count=browser_count,
            github_token=github_token,
            documentation=request.documentation,
            pull_request_message=request.pullRequestMessage,
            pull_request_description=request.pullRequestDescription
        )
        
        logger.info(f"[Orchestrator] Completed orchestration: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"[Orchestrator] Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in orchestrator: {str(e)}"
        )

@app.get("/api/browser-session/{session_id}")
async def get_browser_session_status(session_id: str):
    """
    Get the status and results of browser sessions.
    """
    try:
        from orchestrator.tools import browser_sessions
        
        if session_id not in browser_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = browser_sessions[session_id]
        return {
            "session_id": session_id,
            "status": session["status"],
            "browsers": session["browsers"],
            "task": session["task"]
        }
        
    except Exception as e:
        logger.error(f"Error getting browser session status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting browser session status: {str(e)}"
        )


@app.websocket("/ws/web-agent/{session_id}")
async def websocket_web_agent_stream(websocket: WebSocket, session_id: str):
    await websocket.accept()
    web_agent_websockets[session_id] = websocket
    # Send initial connection confirmation
    await websocket.send_text("🔗 WebSocket connection established")
    
    # Retrieve session parameters
    params = web_agent_session_params.get(session_id)
    agent_bg_task = None
    if params:
        from web_agent.openai_test import run_search
        await websocket.send_text("🚀 Starting web agent task...")
        # Start the agent as a background task
        agent_bg_task = asyncio.create_task(run_search(
            user_task=params['user_task'],
            cdp_url=params['cdp_url'],
            user_name=params['user_name'],
            session_id=session_id,
            publish_thought_func=publish_web_agent_thought
        ))
    else:
        await websocket.send_text("❌ No session parameters found - agent will not start")

    try:
        while True:
            await asyncio.sleep(1)
            if websocket.application_state != WebSocketState.CONNECTED:
                break
    except WebSocketDisconnect:
        pass
    finally:
        if session_id in web_agent_websockets:
            del web_agent_websockets[session_id]
        if session_id in web_agent_session_params:
            del web_agent_session_params[session_id]
        if agent_bg_task:
            agent_bg_task.cancel()

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    logger.info("Combined API Server is starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    logger.info("Combined API Server is shutting down...")

@contextmanager
def stream_print_to_web_agent(session_id):
    class Streamer:
        def __init__(self, orig_stdout):
            self.orig_stdout = orig_stdout
            self.buffer = ''
        def write(self, s):
            self.orig_stdout.write(s)
            self.buffer += s
            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                if line.strip():
                    # Schedule the coroutine to run in the event loop
                    asyncio.create_task(publish_web_agent_thought(session_id, line.strip()))
        def flush(self):
            self.orig_stdout.flush()
    orig_stdout = sys.stdout
    streamer = Streamer(orig_stdout)
    sys.stdout = streamer
    try:
        yield
    finally:
        sys.stdout = orig_stdout

if __name__ == "__main__":
    import uvicorn
    print("\n[INFO] Starting FastAPI server...")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
