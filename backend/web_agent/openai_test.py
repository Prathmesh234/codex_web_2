from browser_use.llm import ChatOpenAI 

import os 
from dotenv import load_dotenv
from pydantic import SecretStr
from browser_use import Agent, BrowserConfig, Browser, BrowserSession
import asyncio
# COMMENTED OUT: Memory agent import to prevent Azure API key errors
# from .master_agent import master_agent
import platform
from typing import Optional
from datetime import datetime
from .models import WebAgentResponse
# Import the streaming function - will be passed as parameter to avoid circular import

# Load environment variables
load_dotenv()

# Initialize Gemini API
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError('GEMINI_API_KEY is not set')

'''
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=SecretStr(api_key),
)
'''


llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.0,
    max_retries=2,
    timeout=None,
)


async def run_search(user_task: str, cdp_url: str, user_name: Optional[str] = None, session_id: Optional[str] = None, publish_thought_func=None) -> dict:
    """
    Run the browser automation task with the given parameters.
    
    Args:
        user_task (str): The task to perform
        cdp_url (str): The CDP URL for browser connection
        user_name (Optional[str]): The user name. Defaults to None.
        session_id (Optional[str]): The session id for streaming. Defaults to None.
        
    Returns:
        dict: Structured response containing the task result and timestamp
    """
    try:
   
        updated_task = user_task
        print(f"CDP URL: {cdp_url}")
        print(f"Task: {updated_task}")
        
        # Add simple prompt for documentation collection
        documentation_prompt = f"""You are a helpful agent that collects documentation for the user to complete the specific task.

TASK: {user_task}

IMPORTANT: If the task contains \"--testing\" anywhere in the text, do NOT proceed with any web navigation or research. Simply return the following blurb of a poem about Batman and nothing else:

"In Gotham's night, a shadow flies,
A cape, a cowl, two watchful eyes.
Justice glides on silent wings,
The Bat, the hope that darkness brings."

Your goal is to:
1. Research and collect relevant documentation
2. Visit 1-2 high-quality sources
3. Gather comprehensive information needed to complete the task
4. Focus on official documentation, tutorials, and best practices
5. Do NOT complete the task yourself - only collect the documentation

Please proceed with collecting the necessary documentation for this task."""
        
        print(f"Documentation Task: {documentation_prompt}")
        
        # Configure and initialize browser
        browser =BrowserSession(cdp_url=cdp_url)
        
        # Initialize and run agent
        agent = Agent(
            browser_session=browser,
            task=documentation_prompt,
            llm=llm,
            use_vision=True,
            save_conversation_path="logs/conversation"
        )

        async def stream_steps(agent):
            page = await agent.browser_session.get_current_page()
            current_url = page.url
            history = agent.state.history
            model_thoughts = history.model_thoughts()
            model_actions = history.model_actions()
            print("[DEBUG] model_thoughts:", model_thoughts)
            print("[DEBUG] model_actions:", model_actions)
            timestamp = datetime.now().strftime("%H:%M:%S")
            step_num = len(model_actions)
            msg_lines = [
                f"🔄 [{timestamp}] Step {step_num}",
                f"🌐 URL: {current_url}",
            ]
            if model_thoughts:
                msg_lines.append(f"💭 Thought: {model_thoughts[-1]}")
            if model_actions:
                action = model_actions[-1]
                # Use dict access for action fields
                action_type = action.get('action', str(action)) if isinstance(action, dict) else getattr(action, 'action', str(action))
                msg_lines.append(f"⚡ Action: {action_type}")
                params = action.get('params') if isinstance(action, dict) else getattr(action, 'params', None)
                if params:
                    msg_lines.append(f"📝 Params: {params}")
            msg_lines.append("-" * 60)
            msg = "\n".join(msg_lines)
            print("[DEBUG] Streaming message:", msg)
            if session_id and publish_thought_func:
                await publish_thought_func(session_id, msg)

        # Run the agent and get history
        history = await agent.run(
            on_step_start=stream_steps,
            max_steps=2
        )
        
        # Get the final result from browser_use
        final_result = history.final_result()
        
        # Return structured response as dict for API
        return WebAgentResponse(response=final_result).dict()
        
    except Exception as e:
        error_msg = f"Error in run_search: {str(e)}"
        print(error_msg)
        if session_id and publish_thought_func:
            await publish_thought_func(session_id, f"Error: {str(e)}")
        
        # Return error response in structured format
        return WebAgentResponse(response=f"Task failed: {error_msg}").dict()


