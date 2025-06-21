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
                        logger.warning(f"Anchor browser failed: {str(anchor_error)}. Using mock session.")
                        
                        # Create mock browser session for testing
                        browser_session_id = f"mock_session_{session_id}_{browser_index}"
                        live_view_url = f"https://mock-browser.com/session/{browser_session_id}"
                        cdp_url = f"ws://mock-browser.com/cdp/{browser_session_id}"
                        
                        logger.info(f"Mock browser {browser_index} created - Session ID: {browser_session_id}, Live View: {live_view_url}")
                    
                    # Create subtask for this browser
                    subtask = self._create_subtask(task, browser_index, browser_count)
                    
                    logger.info(f"Browser {browser_index} subtask: {subtask}")
                    
                    # Start documentation collection in background
                    asyncio.create_task(self._run_documentation_collection(
                        subtask, cdp_url, user_name, session_id, browser_index
                    ))
                    
                    return {
                        "browser_index": browser_index,
                        "live_view_url": live_view_url,
                        "session_id": browser_session_id,
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
                        "session_id": result["session_id"],
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
                logger.info(f"Mock browser session detected for browser {browser_index}, simulating documentation collection")
                
                # Simulate documentation collection for mock session
                import asyncio
                await asyncio.sleep(5)  # Simulate some processing time
                
                mock_documentation = f"""
                MOCK DOCUMENTATION COLLECTION COMPLETED
                
                Task: {subtask}
                Browser: {browser_index}
                Session: {session_id}
                
                Simulated documentation collected:
                - Official documentation sources
                - API references and examples
                - Best practices and tutorials
                - Community resources
                
                This is a mock result for testing purposes.
                """
                
                # Update session with mock results
                if session_id in browser_sessions:
                    browser_sessions[session_id]["browsers"][f"browser_{browser_index}"]["documentation"] = mock_documentation
                    browser_sessions[session_id]["browsers"][f"browser_{browser_index}"]["status"] = "completed"
                
                logger.info(f"Mock documentation collection completed for browser {browser_index}")
                return
            
            # Real browser session - use the actual run_search
            from web_agent.openai_test import run_search
            
            # Run the documentation collection
            result = await run_search(
                user_task=subtask,
                user_name=user_name,
                cdp_url=cdp_url
            )
            
            # Update session with results
            if session_id in browser_sessions:
                browser_sessions[session_id]["browsers"][f"browser_{browser_index}"]["documentation"] = result
                browser_sessions[session_id]["browsers"][f"browser_{browser_index}"]["status"] = "completed"
            
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
   