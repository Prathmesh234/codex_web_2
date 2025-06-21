from langchain_google_genai import ChatGoogleGenerativeAI
import os 
from dotenv import load_dotenv
from pydantic import SecretStr
from browser_use import Agent, BrowserConfig, Browser
import asyncio
# COMMENTED OUT: Memory agent import to prevent Azure API key errors
# from .master_agent import master_agent
import platform
from typing import Optional

# Load environment variables
load_dotenv()

# Initialize Gemini API
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError('GEMINI_API_KEY is not set')

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=SecretStr(api_key),
)

async def run_search(user_task: str, cdp_url: str, user_name: Optional[str] = None):
    """
    Run the browser automation task with the given parameters.
    
    Args:
        user_task (str): The task to perform
        cdp_url (str): The CDP URL for browser connection
        user_name (Optional[str]): The user name. Defaults to None.
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
        config = BrowserConfig(
            cdp_url=cdp_url,
            headless=False,
        )
        browser = Browser(config=config)
        
        # Initialize and run agent
        agent = Agent(
            browser=browser,
            task=documentation_prompt,
            llm=llm,
            use_vision=True,
            save_conversation_path="logs/conversation"
        )
        
        await agent.run()
        
    except Exception as e:
        print(f"Error in run_search: {str(e)}")
        raise


