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
            
            # Now run documentation collection and wait for completion
            logger.info("Starting documentation collection for all browsers")
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
            
            # Prepare response with live view URLs and documentation
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
                "status": "completed",
                "documentation": all_documentation
            }
            
            logger.info(f"Returning browser session data with documentation: {response_data}")
            logger.info(f"Documentation collected: {all_documentation}")
            
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
        github_token: Annotated[str, "GitHub access token for authentication"],
        repo_url: Annotated[str, "GitHub repository URL to create the pull request in"],
        documentation: Annotated[str, "Extracted documentation to include in the pull request (as a string or JSON)"],
        commitMessage: Annotated[str, "Commit message for the pull request"],
        commitDescription: Annotated[str, "Description for the pull request"]
    ) -> Annotated[str, "Pull request result with PR URL as JSON string"]:
        """Create a pull request with documentation using the GitHub API"""
        import json
        import base64
        import requests
        import re
        from urllib.parse import urlparse
        
        try:
            logger.info(f"Starting create_pull_request_tool for repo: {repo_url}")
            logger.info(f"GitHub Token: {'Present' if github_token else 'Missing'}")
            logger.info(f"Commit Message: {commitMessage}")
            logger.info(f"Pull Request Description: {commitDescription}")
            logger.info(f"Documentation length: {len(documentation)} characters")
            
            if not github_token:
                raise ValueError("GitHub token is required")
            
            # Parse repository URL to get owner and repo name
            # Handle both GitHub URLs and API URLs
            if repo_url.startswith('https://api.github.com/repos/'):
                repo_api_url = repo_url
                # Extract owner/repo from API URL
                match = re.search(r'/repos/([^/]+)/([^/]+)', repo_url)
                if not match:
                    raise ValueError(f"Invalid GitHub API URL format: {repo_url}")
                owner, repo = match.groups()
            elif repo_url.startswith('https://github.com/'):
                # Convert GitHub URL to API URL
                parsed = urlparse(repo_url)
                path_parts = parsed.path.strip('/').split('/')
                if len(path_parts) < 2:
                    raise ValueError(f"Invalid GitHub URL format: {repo_url}")
                owner, repo = path_parts[0], path_parts[1]
                # Remove .git suffix if present
                if repo.endswith('.git'):
                    repo = repo[:-4]
                repo_api_url = f"https://api.github.com/repos/{owner}/{repo}"
            else:
                raise ValueError(f"Unsupported repository URL format: {repo_url}")
            
            logger.info(f"Repository API URL: {repo_api_url}")
            logger.info(f"Owner: {owner}, Repo: {repo}")
            
            headers = {
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # 1. Get latest SHA of main branch
            main_branch = 'main'
            try:
                main_ref_resp = requests.get(f'{repo_api_url}/git/ref/heads/{main_branch}', headers=headers)
                main_ref_resp.raise_for_status()
                main_sha = main_ref_resp.json()['object']['sha']
                logger.info(f"Main branch SHA: {main_sha}")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    # Try 'master' branch as fallback
                    main_branch = 'master'
                    main_ref_resp = requests.get(f'{repo_api_url}/git/ref/heads/{main_branch}', headers=headers)
                    main_ref_resp.raise_for_status()
                    main_sha = main_ref_resp.json()['object']['sha']
                    logger.info(f"Using master branch SHA: {main_sha}")
                else:
                    raise
            
            # 2. Create new branch
            import time
            timestamp = int(time.time())
            new_branch = f'auto-doc-update-{timestamp}'
            ref_payload = {
                "ref": f"refs/heads/{new_branch}",
                "sha": main_sha
            }
            
            logger.info(f"Creating branch: {new_branch}")
            ref_resp = requests.post(f'{repo_api_url}/git/refs', headers=headers, json=ref_payload)
            ref_resp.raise_for_status()
            logger.info(f"Branch created successfully: {new_branch}")
            
            # 3. Prepare file content
            file_path = 'documentation.md'
            content_b64 = base64.b64encode(documentation.encode('utf-8')).decode('utf-8')
            content_payload = {
                'message': f"{commitMessage}\n\n{commitDescription}",
                'content': content_b64,
                'branch': new_branch
            }
            
            logger.info(f"Committing file: {file_path}")
            put_resp = requests.put(f'{repo_api_url}/contents/{file_path}', headers=headers, json=content_payload)
            put_resp.raise_for_status()
            logger.info("File committed successfully")
            
            # 4. Create Pull Request
            pr_payload = {
                "title": commitMessage,
                "head": new_branch,
                "base": main_branch,
                "body": f"{commitDescription}\n\n---\n\nThis pull request was automatically generated with documentation collected from web research."
            }
            
            logger.info("Creating pull request")
            pr_resp = requests.post(f'{repo_api_url}/pulls', headers=headers, json=pr_payload)
            pr_resp.raise_for_status()
            
            pr_data = pr_resp.json()
            pr_url = pr_data['html_url']
            pr_number = pr_data['number']
            
            logger.info(f"Pull request created successfully: {pr_url}")
            
            response_data = {
                "repo_url": repo_url,
                "status": "success",
                "message": "Pull request created successfully",
                "pr_url": pr_url,
                "pr_number": pr_number,
                "branch_name": new_branch,
                "commitMessage": commitMessage,
                "pullRequestDescription": commitDescription
            }
            
            # Print the PR URL for the orchestrator to see
            print(f"🔗 Pull request created: {pr_url}")
            logger.info(f"Pull request tool completed successfully. PR URL: {pr_url}")
            
            return json.dumps(response_data)
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"GitHub API error: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            return json.dumps({
                "error": error_msg,
                "repo_url": repo_url,
                "status": "failed"
            })
        except Exception as e:
            error_msg = f"Error in create_pull_request_tool: {str(e)}"
            logger.error(error_msg)
            return json.dumps({
                "error": error_msg,
                "repo_url": repo_url,
                "status": "failed"
            })
   