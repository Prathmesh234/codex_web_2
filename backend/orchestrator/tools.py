from semantic_kernel.functions.kernel_function_decorator import kernel_function
from typing import Annotated, Dict, Any, List, Optional
import asyncio
import logging
import json
import uuid
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Global storage for browser sessions
browser_sessions = {}

class OrchestratorTools:
    """
    Simplified Semantic Kernel tools for the orchestrator agent to manage browser sessions for documentation collection.
    """
    
    @kernel_function(description="Start multiple browser sessions for documentation collection")
    async def start_multiple_browser_sessions(
        self,
        task: Annotated[str, "The main task to collect documentation for"],
        browser_count: Annotated[int, "Number of browser sessions to start"],
        user_name: Annotated[str, "The user name for the sessions"] = None
    ) -> Annotated[str, "Browser session information with live view URLs"]:
        """Start multiple browser sessions for documentation collection"""
        try:
            logger.info(f"Starting {browser_count} browser sessions for task: {task}")
            
            session_id = str(uuid.uuid4())
            browser_sessions[session_id] = {
                "status": "starting",
                "browsers": {},
                "task": task,
                "user_name": user_name or "Anonymous User"
            }
            
            logger.info(f"Created session {session_id} for task: {task}")
            
            # Start browser sessions in parallel
            async def start_single_browser(browser_index: int):
                try:
                    logger.info(f"Starting browser {browser_index} for session {session_id}")
                    
                    # Try to start Anchor browser session
                    try:
                        from web_agent.anchor_browser.session_management.anchor_session_start import start_anchor_session
                        
                        # Start the browser session
                        session_info = start_anchor_session()
                        cdp_url = session_info['data']['cdp_url']
                        live_view_url = session_info['data']['live_view_url']
                        browser_session_id = session_info['data']['id']
                        
                        logger.info(f"Browser {browser_index} started - Session ID: {browser_session_id}, Live View: {live_view_url}")
                        
                    except Exception as anchor_error:
                        logger.error(f"Anchor browser failed: {str(anchor_error)}.")
                        raise  # Propagate the error instead of using a mock session
                    
                    # Create subtask for this browser
                    subtask = self._create_subtask(task, browser_index, browser_count)
                    
                    # Store session parameters for WebSocket handler using the main session_id, not browser_session_id
                    import sys
                    if 'app' in sys.modules:
                        app_module = sys.modules['app']
                        if hasattr(app_module, 'web_agent_session_params'):
                            app_module.web_agent_session_params[session_id] = {
                                'user_task': subtask,
                                'user_name': user_name or "Anonymous User",
                                'cdp_url': cdp_url
                            }
                            logger.info(f"Stored session params for WebSocket handler: {session_id}")
                        else:
                            logger.warning("web_agent_session_params not found in app module")
                    else:
                        logger.warning("app module not loaded, cannot store session params")
                    
                    logger.info(f"Browser {browser_index} subtask: {subtask}")
                    
                    # Start documentation collection in background
                    asyncio.create_task(self._run_documentation_collection(
                        subtask, cdp_url, user_name, session_id, browser_index
                    ))
                    
                    return {
                        "browser_index": browser_index,
                        "live_view_url": live_view_url,
                        "session_id": session_id,  # Use main session_id instead of browser_session_id
                        "cdp_url": cdp_url,
                        "subtask": subtask
                    }
                except Exception as e:
                    logger.error(f"Error starting browser {browser_index}: {str(e)}")
                    return {
                        "browser_index": browser_index,
                        "error": str(e)
                    }
            
            # Start all browser sessions concurrently
            logger.info(f"Starting {browser_count} browser tasks concurrently")
            browser_tasks = [start_single_browser(i) for i in range(browser_count)]
            browser_results = await asyncio.gather(*browser_tasks)
            
            logger.info(f"All browser tasks completed. Results: {browser_results}")
            
            # Update session info
            browser_sessions[session_id]["browsers"] = {}
            for result in browser_results:
                if "error" not in result:
                    browser_sessions[session_id]["browsers"][f"browser_{result['browser_index']}"] = result
            browser_sessions[session_id]["status"] = "running"
            
            # Prepare response with live view URLs
            browsers_info = {}
            for result in browser_results:
                if "error" not in result:
                    browsers_info[f"browser_{result['browser_index']}"] = {
                        "live_view_url": result["live_view_url"],
                        "session_id": session_id,  # Use main session_id consistently
                        "subtask": result["subtask"]
                    }
            
            response_data = {
                "session_id": session_id,
                "browsers": browsers_info,
                "status": "running"
            }
            
            logger.info(f"Returning browser session data: {response_data}")
            logger.info(f"Browser results: {browser_results}")
            logger.info(f"Browsers info: {browsers_info}")
            
            return json.dumps(response_data)
            
        except Exception as e:
            logger.error(f"Error starting multiple browser sessions: {str(e)}")
            return f"Error starting browser sessions: {str(e)}"
    
    def _create_subtask(self, main_task: str, browser_index: int, total_browsers: int) -> str:
        """Create a subtask for a specific browser based on the main task"""
        if total_browsers == 1:
            return f"Research and collect documentation for: {main_task}. Focus on official documentation, tutorials, and best practices. Visit 1-2 high-quality sources."
        elif total_browsers == 2:
            if browser_index == 0:
                return f"Research and collect documentation for: {main_task}. Focus on official documentation and API references. Visit 1-2 authoritative sources."
            else:
                return f"Research and collect documentation for: {main_task}. Focus on tutorials, examples, and community resources. Visit 1-2 practical sources."
        else:  # 3 browsers
            if browser_index == 0:
                return f"Research and collect documentation for: {main_task}. Focus on official documentation and API references. Visit 1-2 authoritative sources."
            elif browser_index == 1:
                return f"Research and collect documentation for: {main_task}. Focus on tutorials and practical examples. Visit 1-2 tutorial sources."
            else:
                return f"Research and collect documentation for: {main_task}. Focus on community resources and best practices. Visit 1-2 community sources."
    
    async def _run_documentation_collection(
        self, 
        subtask: str, 
        cdp_url: str, 
        user_name: Optional[str], 
        session_id: str, 
        browser_index: int
    ):
        """Run documentation collection in the background"""
        try:
            # Check if this is a mock session
            if cdp_url.startswith("ws://mock-browser.com"):
                logger.error(f"Mock browser session detected for browser {browser_index}, but mock sessions are disabled.")
                raise RuntimeError("Mock browser sessions are disabled. Failed to start real browser session.")
            
            # Real browser session - use the actual run_search
            from web_agent.openai_test import run_search
            
            # Run the documentation collection
            web_agent_response = await run_search(
                user_task=subtask,
                user_name=user_name,
                cdp_url=cdp_url
            )
            
            print(f"Orchestrator received response from web_agent_{browser_index}: {web_agent_response}")
            logger.info(f"Orchestrator received response from web_agent_{browser_index}: {web_agent_response}")
            
            # Update session with results - store the dict directly
            if session_id in browser_sessions:
                browser_sessions[session_id]["browsers"][f"browser_{browser_index}"]["documentation"] = web_agent_response
                browser_sessions[session_id]["browsers"][f"browser_{browser_index}"]["status"] = "completed"
                print(f"Orchestrator stored results for browser_{browser_index} in session {session_id}")
            
            logger.info(f"Documentation collection completed for browser {browser_index}")
            
        except Exception as e:
            logger.error(f"Error in documentation collection for browser {browser_index}: {str(e)}")
            if session_id in browser_sessions:
                browser_sessions[session_id]["browsers"][f"browser_{browser_index}"]["error"] = str(e)
                browser_sessions[session_id]["browsers"][f"browser_{browser_index}"]["status"] = "failed"
    
    @kernel_function(description="Get the status and results of browser sessions")
    async def get_browser_session_status(
        self,
        session_id: Annotated[str, "The session ID to check"]
    ) -> Annotated[str, "Session status and browser information"]:
        """Get the status and results of browser sessions"""
        try:
            if session_id not in browser_sessions:
                return json.dumps({"error": "Session not found"})
            
            session = browser_sessions[session_id]
            return json.dumps(session)
            
        except Exception as e:
            logger.error(f"Error getting session status: {str(e)}")
            return json.dumps({"error": str(e)})
    
    @kernel_function(description="Execute a task using a container instance (local or Azure)")
    async def container_tool(
        self,
        task_name: Annotated[str, "Description of the task to complete"],
        repo_url: Annotated[str, "GitHub repository URL to clone"],
        project_name: Annotated[str, "Name of the project/repository"],
        container_type: Annotated[str, "Container type: 'local' or 'azure'"] = "local"
    ) -> Annotated[str, "Task execution results and command history"]:
        """Execute a task using a container instance similar to codex agent"""
        try:
            logger.info(f"Starting container tool for task: {task_name}")
            logger.info(f"Repository: {repo_url}, Project: {project_name}, Container: {container_type}")
            
            # Import the codex agent functionality
            try:
                from codex_agent.codex_core_agent import complete_task
                from codex_agent.azure_queue import AzureQueueManager
                import os
            except ImportError as e:
                error_msg = f"Failed to import codex agent components: {str(e)}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})
            
            # Initialize Azure queue if needed
            azure_queue = None
            if container_type == "azure":
                connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
                if connection_string:
                    azure_queue = AzureQueueManager(connection_string)
                else:
                    logger.warning("Azure container requested but connection string not found, falling back to local")
                    container_type = "local"
            
            # Override the interactive container type selection
            def get_container_type():
                return container_type
            
            # Temporarily replace the function in the codex_core_agent module
            import codex_agent.codex_core_agent as codex_module
            original_get_container_type = codex_module.get_container_type
            codex_module.get_container_type = get_container_type
            
            try:
                # Execute the task
                command_history = complete_task(task_name, repo_url, project_name)
                
                # Format the response
                response_data = {
                    "task_name": task_name,
                    "repo_url": repo_url,
                    "project_name": project_name,
                    "container_type": container_type,
                    "status": "completed",
                    "command_history": [
                        {
                            "command": cmd,
                            "output": output
                        }
                        for cmd, output in command_history
                    ]
                }
                
                logger.info(f"Container tool completed successfully for task: {task_name}")
                return json.dumps(response_data)
                
            finally:
                # Restore the original function
                codex_module.get_container_type = original_get_container_type
                
        except Exception as e:
            error_msg = f"Error in container tool: {str(e)}"
            logger.error(error_msg)
            return json.dumps({
                "error": error_msg,
                "task_name": task_name,
                "status": "failed"
            })
   