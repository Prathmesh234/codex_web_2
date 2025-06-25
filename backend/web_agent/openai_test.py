from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

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
# Import the streaming function - will be passed as parameter to avoid circular import

# Load environment variables
load_dotenv()

# Initialize Gemini API
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError('GEMINI_API_KEY is not set')

# Initialize LLM
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

async def run_search(user_task: str, cdp_url: str, user_name: Optional[str] = None, session_id: Optional[str] = None, publish_thought_func=None):
    """
    Run the browser automation task with the given parameters.
    
    Args:
        user_task (str): The task to perform
        cdp_url (str): The CDP URL for browser connection
        user_name (Optional[str]): The user name. Defaults to None.
        session_id (Optional[str]): The session id for streaming. Defaults to None.
    """
    try:
        # COMMENTED OUT: Memory agent functionality
        # Get the master agent's reply
        # master_reply = await master_agent(user_task, user_name)
        # print(f"CDP URL: {cdp_url}")
        # print(f"Master Agent Reply: {master_reply}")

        # COMMENTED OUT: Update the task with the master agent's response
        # updated_task = f"{user_task}. Master Agent says: {master_reply}"
        
        # Use the original task directly without memory processing
        updated_task = user_task
        print(f"CDP URL: {cdp_url}")
        print(f"Task: {updated_task}")
        
        # Add simple prompt for documentation collection
        documentation_prompt = f"""You are a helpful agent that collects documentation for the user to complete the specific task.

TASK: {user_task}

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

        await agent.run(
            on_step_start=stream_steps,
            max_steps=15
        )
    except Exception as e:
        print(f"Error in run_search: {str(e)}")
        if session_id and publish_thought_func:
            await publish_thought_func(session_id, f"Error: {str(e)}")
        raise


