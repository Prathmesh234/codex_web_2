from semantic_kernel.functions.kernel_function_decorator import kernel_function
from typing import Annotated, Dict, Any, List, Optional
import asyncio
import logging
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
import re
import requests, base64, time, re
from urllib.parse import urlparse

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
        user_name: Annotated[Optional[str], "The user name for the sessions"] = None
    ) -> Annotated[str, "Browser session information with live view URLs and documentation results"]:
        """Start multiple browser sessions for documentation collection and return documentation"""
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
            
            # Store documentation collection tasks
            documentation_tasks = []
            
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
                    
                    # Create documentation collection task (but don't start it yet)
                    doc_task = self._run_documentation_collection(
                        subtask, cdp_url, user_name, session_id, browser_index
                    )
                    documentation_tasks.append(doc_task)
                    
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
            
            # Prepare response with live view URLs (do NOT wait for documentation collection)
            browsers_info = {}
            for result in browser_results:
                if "error" not in result:
                    browser_key = f"browser_{result['browser_index']}"
                    browsers_info[browser_key] = {
                        "live_view_url": result["live_view_url"],
                        "session_id": session_id,  # Use main session_id consistently
                        "subtask": result["subtask"]
                    }
            
            response_data = {
                "session_id": session_id,
                "browsers": browsers_info,
                "status": "running"
            }
            
            logger.info(f"Returning browser session data immediately: {response_data}")
            
            # Start documentation collection in the background
            async def run_docs_bg():
                logger.info("Starting documentation collection for all browsers (background)")
                await asyncio.gather(*documentation_tasks)
                # Wait a moment for all results to be stored
                await asyncio.sleep(1)
                # Collect all documentation results
                all_documentation = {}
                for browser_index in range(browser_count):
                    browser_key = f"browser_{browser_index}"
                    if browser_key in browser_sessions[session_id]["browsers"]:
                        browser_data = browser_sessions[session_id]["browsers"][browser_key]
                        if "documentation" in browser_data:
                            all_documentation[browser_key] = browser_data["documentation"]
                browser_sessions[session_id]["documentation"] = all_documentation
                browser_sessions[session_id]["status"] = "completed"
                logger.info(f"Documentation collection completed and stored for session {session_id}")
            asyncio.create_task(run_docs_bg())
            
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
    
    @kernel_function(description="Create a pull request with documentation using the provided GitHub token")
    async def create_pull_request_tool(
        self,
        github_token: Annotated[str, "GitHub access token"],
        repo_url: Annotated[str, "https://github.com/<owner>/<repo>"],
        documentation: Annotated[str, "Markdown or JSON string"],
        commitMessage: Annotated[str, "PR title"],
        commitDescription: Annotated[str, "PR body"],
    ) -> Annotated[str, "Pull-request URL"]:
        """
        Pushes `documentation.md` to a new branch and opens a PR.
        Returns the PR URL (string) or raises an exception on error.
        """
        import requests
        import time
        import base64
        try:
            # --- derive API endpoints ---
            match = re.match(r"https://github\.com/([^/]+)/([^/]+)", repo_url)
            if not match:
                return "Error creating pull request: Invalid repo_url format. Expected https://github.com/<owner>/<repo>"
            owner, repo = match.groups()
            repo_api = f"https://api.github.com/repos/{owner}/{repo}"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            # --- get default branch SHA ---
            repo_resp = requests.get(repo_api, headers=headers)
            if not repo_resp.ok:
                logger.error(f"GitHub API error (repo): {repo_resp.status_code} - {repo_resp.text}")
                return f"Error fetching repo: {repo_resp.status_code} - {repo_resp.text}"
            default_branch = repo_resp.json()["default_branch"]
            sha_resp = requests.get(f"{repo_api}/git/ref/heads/{default_branch}", headers=headers)
            if not sha_resp.ok:
                logger.error(f"GitHub API error (sha): {sha_resp.status_code} - {sha_resp.text}")
                return f"Error fetching branch SHA: {sha_resp.status_code} - {sha_resp.text}"
            base_sha = sha_resp.json()["object"]["sha"]

            # --- create temp branch ---
            new_branch = f"auto-doc-{int(time.time())}"
            branch_resp = requests.post(f"{repo_api}/git/refs", headers=headers, json={
                "ref": f"refs/heads/{new_branch}",
                "sha": base_sha,
            })
            if not branch_resp.ok:
                logger.error(f"GitHub API error (branch): {branch_resp.status_code} - {branch_resp.text}")
                return f"Error creating branch: {branch_resp.status_code} - {branch_resp.text}"

            # --- add /documentation.md ---
            content_b64 = base64.b64encode(documentation.encode()).decode()
            file_resp = requests.put(f"{repo_api}/contents/documentation.md", headers=headers, json={
                "message": commitMessage,
                "content": content_b64,
                "branch": new_branch,
            })
            if not file_resp.ok:
                logger.error(f"GitHub API error (file): {file_resp.status_code} - {file_resp.text}")
                return f"Error creating file: {file_resp.status_code} - {file_resp.text}"

            # --- open PR ---
            pr_resp = requests.post(f"{repo_api}/pulls", headers=headers, json={
                "title": commitMessage,
                "head": new_branch,
                "base": default_branch,
                "body": commitDescription,
            })
            if not pr_resp.ok:
                logger.error(f"GitHub API error (PR): {pr_resp.status_code} - {pr_resp.text}")
                return f"Error creating pull request: {pr_resp.status_code} - {pr_resp.text}"

            pr = pr_resp.json()
            return pr["html_url"]
        except Exception as e:
            logger.error(f"Error creating pull request: {str(e)}")
            return f"Error creating pull request: {str(e)}"
    