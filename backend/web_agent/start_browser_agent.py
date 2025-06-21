import sys
import os
import asyncio
from typing import Dict, Any, Optional
import time
import platform
import sys, asyncio, platform

if platform.system().startswith("Windows"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Add the necessary paths to system path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(current_dir)
sys.path.append(parent_dir)

# Import necessary modules
from .anchor_browser.session_management.anchor_session_start import start_anchor_session
from .anchor_browser.session_management.anchor_browser_end_all_sessions import end_all_anchor_sessions
from .openai_test import run_search

async def start_browser_agent(user_task: str, user_name: Optional[str] = None, end_all_sessions: bool = False) -> str:
    """
    Initiates the browser using anchor_session_start and calls run_search with the CDP URL.
    
    Args:
        user_task (str): The task to perform
        user_name (Optional[str]): The user name. Defaults to None.
        end_all_sessions (bool, optional): Whether to end all sessions after completion. Defaults to False.
        
    Returns:
        str: The live view URL for the browser session
    """
    try:
        # Start the anchor browser session
        print("Starting Anchor Browser session...")
        session_info = start_anchor_session()
        
        # Extract the CDP URL and live view URL
        cdp_url = session_info['data']['cdp_url']
        live_view_url = session_info['data']['live_view_url']
        session_id = session_info['data']['id']
        
        print(f"Session ID: {session_id}")
        print(f"CDP URL: {cdp_url}")
        print(f"Live View URL: {live_view_url}")
        
        # Call the run_search function with the CDP URL
        print(f"Executing task: {user_task}")
        time.sleep(5)  # Optional delay for better readability
        await run_search(user_task=user_task, user_name=user_name, cdp_url=cdp_url)
        
        print("\nTask execution complete!")
        print(f"You can view the browser session at: {live_view_url}")
        
        # End all sessions if requested
        if end_all_sessions:
            print("\nEnding all Anchor Browser sessions...")
            result = end_all_anchor_sessions()
            print(f"End all sessions result: {result}")
        
        return live_view_url
    
    except Exception as e:
        print(f"Error during browser agent execution: {str(e)}")
        # Try to end all sessions even if there was an error
        if end_all_sessions:
            try:
                print("\nEnding all Anchor Browser sessions due to error...")
                end_all_anchor_sessions()
            except Exception as end_error:
                print(f"Error ending sessions: {str(end_error)}")
        raise

async def main():
    """Main function to run the browser agent."""
    if len(sys.argv) > 1:
        user_task = sys.argv[1]
    else:
        user_task = input("Enter the task to perform: ")
    
    if len(sys.argv) > 2:
        user_name = sys.argv[2]
    else:
        user_name = input("Enter your name (or press Enter for default 'Pluto Albert'): ")
        if not user_name:
            user_name = "Pluto Albert"
    
    end_all = input("End all sessions after completion? (y/n, default: n): ").lower().strip() == 'y'
    
    await start_browser_agent(user_task, user_name, end_all)

if __name__ == "__main__":
    asyncio.run(main())