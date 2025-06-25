from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.kernel import Kernel
import os
import json
import logging
from typing import Optional, Dict, Any
import asyncio
from dotenv import load_dotenv

from .tools import OrchestratorTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Orchestrator:
    """
    Simplified orchestrator agent class using Semantic Kernel to manage browser sessions for documentation collection.
    """
    
    def __init__(self):
        """Initialize the orchestrator with Semantic Kernel setup"""
        self.kernel = Kernel()
        self.credentials = os.getenv("OPENAI_API_KEY")
        if not self.credentials:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Add the OpenAIChatCompletion service to the kernel
        self.service = OpenAIChatCompletion(
            service_id="orchestrator_agent", 
            api_key=self.credentials, 
            ai_model_id="gpt-4o"
        )
        self.kernel.add_service(self.service)
        
        # Add the orchestrator tools
        self.orchestrator_tools = OrchestratorTools()
        self.kernel.add_plugin(self.orchestrator_tools, plugin_name="orchestrator_tools")
        
        # Create the orchestrator agent
        self.agent = ChatCompletionAgent(
            service=self.service,
            kernel=self.kernel,
            name="orchestrator_agent",
            instructions=self._get_system_prompt()
        )
        
        logger.info("Orchestrator agent initialized successfully")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the orchestrator agent"""
        return """You are a simple orchestrator agent designed to manage browser sessions for documentation collection.

**Your Core Workflow:**

1. **Receive Task & Browser Count:** Get the task description and number of browsers to use
2. **Start Browser Sessions:** Launch multiple browser sessions for documentation collection
3. **Return Live View URLs:** Immediately return browser URLs to frontend
4. **Monitor Progress:** Track documentation collection in background
5. **Return Results:** Send collected documentation to frontend when complete

**Available Tools:**

1. `start_multiple_browser_sessions(task: str, browser_count: int, user_name: str = None)`: Start multiple browser sessions for documentation collection
2. `get_browser_session_status(session_id: str)`: Get the status and results of browser sessions

**Input Format:**
- task_name: The description of the task to perform
- repo_info: Repository information object (for context only)
- browser_count: Number of browser sessions to use for the task
- github_token: GitHub access token (for context only)

**Output Requirements:**
Your response should include:
1. Browser session information with live view URLs
2. Session ID for tracking progress
3. Simple confirmation that browsers are starting

**Example Response Format:**
```
BROWSER SESSIONS STARTED:
[Browser session information with live view URLs]

SESSION ID: [session_id]
STATUS: [running/starting]

The browsers are now collecting documentation for your task.
```

**Important Notes:**
- Always start browser sessions first for documentation collection
- Return live view URLs immediately to the frontend
- Focus only on documentation collection, not task completion
- Each browser should visit 1-2 high-quality sources
- Keep the response simple and focused on browser management"""

    async def orchestrate_task(
        self, 
        task_name: str, 
        repo_info: Dict[str, Any], 
        browser_count: int,
        github_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate a task using the orchestrator agent with browser distribution.
        
        Args:
            task_name (str): The name/description of the task to perform
            repo_info (Dict[str, Any]): Repository information object from frontend
            browser_count (int): Number of browser sessions to use
            github_token (Optional[str]): GitHub access token for repository operations
            
        Returns:
            Dict[str, Any]: The orchestrator's response with browser URLs
        """
        try:
            logger.info(f"Starting orchestration for task: {task_name}")
            logger.info(f"Repository info: {repo_info}")
            logger.info(f"Browser count: {browser_count}")
            logger.info(f"GitHub token: {'Present' if github_token else 'Not provided'}")
            
            # Directly call the browser tool instead of using the agent
            logger.info("Directly calling browser tool")
            browser_result = await self.orchestrator_tools.start_multiple_browser_sessions(
                task=task_name,
                browser_count=browser_count,
                user_name=None
            )
            
            logger.info(f"Browser tool result (raw): {browser_result}")
            browser_data = self._extract_full_response(browser_result)
            browser_info = browser_data.get("browsers", {})
            session_id = browser_data.get("session_id", "")
            logger.info(f"Browser tool result (parsed): {browser_data}")
            
            logger.info("Orchestration completed successfully")
            return {
                "message": "Orchestrator completed successfully",
                "result": browser_result,
                "browsers": browser_info,
                "session_id": session_id,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error in orchestrate_task: {str(e)}")
            return {
                "message": f"Error orchestrating task: {str(e)}",
                "status": "error",
                "browsers": {}
            }
    
    def _extract_full_response(self, response: str) -> Dict[str, Any]:
        """Extract full response data including session_id and browsers"""
        try:
            # First, try to parse the entire response as JSON
            try:
                browser_data = json.loads(response)
                return browser_data
            except json.JSONDecodeError:
                pass
            
            # If not JSON, look for JSON-like structures in the response
            import re
            json_pattern = r'\{[^{}]*"(session_id|browsers)"[^{}]*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            if matches:
                # Try to parse the first match
                browser_data = json.loads(matches[0])
                return browser_data
            
            # If no JSON found, return empty dict
            return {}
            
        except Exception as e:
            logger.error(f"Error extracting response data: {str(e)}")
            return {}

    def _extract_browser_info(self, response: str) -> Dict[str, Any]:
        """Extract browser session information from the agent response"""
        full_data = self._extract_full_response(response)
        return full_data.get("browsers", {})
    
    async def _invoke_agent(
        self, 
        input_text: str, 
        thread: ChatHistoryAgentThread
    ) -> Optional[str]:
        """
        Invoke the orchestrator agent with the given input.
        
        Args:
            input_text (str): The input text for the agent
            thread (ChatHistoryAgentThread): The conversation thread
            
        Returns:
            Optional[str]: The agent's response, or None if no valid response
        """
        if not input_text.strip():
            return None

        logger.info(f"Orchestrator Input: {input_text}")

        response = ""
        try:
            async for content in self.agent.invoke(messages=input_text, thread=thread):
                if content.content is not None:
                    logger.info(f"Orchestrator: {content.content}")
                    response += str(content.content) + " "
        except Exception as e:
            logger.error(f"Error invoking orchestrator agent: {e}")
            raise

        return response.strip() if response else None

# Convenience function for easy usage
async def run_orchestrator(task_name: str, repo_info: Dict[str, Any], browser_count: int, github_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to run the orchestrator for a given task.
    
    Args:
        task_name (str): The name/description of the task to perform
        repo_info (Dict[str, Any]): Repository information object from frontend
        browser_count (int): Number of browser sessions to use
        github_token (Optional[str]): GitHub access token for repository operations
        
    Returns:
        Dict[str, Any]: The orchestrator's response with browser URLs
    """
    orchestrator = Orchestrator()
    return await orchestrator.orchestrate_task(task_name, repo_info, browser_count, github_token)
