import os
import json
import logging
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from dotenv import load_dotenv
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader
from codex_agent.kernel_agent import execute_terminal_command
from codex_agent.models import TaskState, CommandEntry
from codex_agent.azure_queue import AzureQueueManager

# Configure logging to print to terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Print to terminal
        logging.FileHandler('codex_agent.log')  # Also save to file
    ],
    force=True  # Force the configuration
)

# Create a logger that will print to stdout
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ensure the logger's handlers are properly configured
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Load environment variables from codex_core directory
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)
print(f"\n[INFO] Loading .env from: {env_path}")

# Initialize OpenAI client
client = OpenAI()
print("[INFO] OpenAI client initialized")

# Initialize Jinja environment
template_dir = Path(__file__).parent
env = Environment(loader=FileSystemLoader(template_dir))
template = env.get_template('codex_core_prompt.jinja')
print("[INFO] Jinja template loaded")

def get_container_type() -> str:
    """Ask user whether to use local or Azure container instance"""
    while True:
        container_type = input("\nDo you want to use (1) Local container or (2) Azure container instance? [1/2]: ").strip()
        if container_type in ['1', '2']:
            return 'local' if container_type == '1' else 'azure'
        print("Please enter 1 for local or 2 for Azure container instance")

def initialize_azure_queue() -> Optional[AzureQueueManager]:
    """Initialize Azure Queue Manager if Azure storage connection string is available"""
    connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    if not connection_string:
        print("[WARNING] Azure Storage connection string not found. Azure container instance will not be available.")
        return None
    return AzureQueueManager(connection_string)

def execute_command(command: str, project_name: Optional[str], container_type: str, azure_queue: Optional[AzureQueueManager]) -> Dict:
    """Execute command either locally or via Azure queue"""
    if container_type == 'azure' and azure_queue:
        try:
            return azure_queue.execute_command(command, project_name)
        except Exception as e:
            print(f"\n[ERROR] Azure queue operation failed: {str(e)}")
            logger.error(f"Azure queue operation failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    else:
        return execute_terminal_command(command)

def complete_task(task_name: str, repo_url: str, project_name: str) -> List[Tuple[str, str]]:
    """
    Execute a task using GPT-4 to generate and execute Linux commands.
    
    Args:
        task_name (str): Description of the task to complete
        repo_url (str): GitHub repository URL to clone
        project_name (str): Name of the project/repository
        
    Returns:
        List[Tuple[str, str]]: List of (command, output) tuples executed during the session
    """
    command_history = []
    task_state = TaskState(
        task_name=task_name,
        current_directory="/projects"  # Default directory
    )
    
    # Determine container type
    container_type = get_container_type()
    azure_queue = initialize_azure_queue() if container_type == 'azure' else None
    
    if container_type == 'azure' and not azure_queue:
        print("\n[ERROR] Azure container instance selected but Azure Queue Manager initialization failed.")
        print("Falling back to local container...")
        container_type = 'local'
    
    print(f"\n[INFO] Starting task: {task_name}")
    print(f"[INFO] Using {container_type} container instance")
    logger.info(f"Starting task: {task_name} with {container_type} container")
    
    # Clone repository first
    clone_command = f"git clone {repo_url} /projects/{project_name}"
    print(f"\n[INFO] Cloning repository: {repo_url}")
    logger.info(f"Cloning repository: {repo_url}")
    
    result = execute_command(clone_command, None, container_type, azure_queue)
    if not result["success"]:
        error_msg = result.get("error", "Unknown error")
        print(f"\n[ERROR] Failed to clone repository: {error_msg}")
        logger.error(f"Failed to clone repository: {error_msg}")
        return command_history
    
    # Update current directory to the cloned repository
    task_state.current_directory = f"/projects/{project_name}"
    print(f"\n[INFO] Repository cloned successfully. Working directory: {task_state.current_directory}")
    
    while True:
        try:
            # Render the template with current state
            prompt = template.render(**task_state.to_dict())
            
            print("\n[INFO] Generated prompt:")
            print("-" * 50)
            print(prompt)
            print("-" * 50)
            
            # Get command from GPT-4
            print("\n[INFO] Calling OpenAI API...")
            response = client.responses.create(
                model="o4-mini",
                input=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "input_text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                text={
                    "format": {
                        "type": "text"
                    }
                },
                reasoning={
                    "effort": "medium",
                    "summary": "auto"
                },
                tools=[],
                store=True
            )
            
            command = response.output_text.strip()
            print(f"\n[INFO] Generated command: {command}")
            logger.info(f"Generated command: {command}")
            
            # Check if task is complete
            if command == "TASK_COMPLETED":
                print("\n[INFO] Task completed successfully")
                logger.info("Task completed successfully")
                return command_history
            
            # Execute the command
            print(f"\n[INFO] Executing command: {command}")
            logger.info(f"Executing command: {command}")
            result = execute_command(command, task_state.current_directory, container_type, azure_queue)
            
            if not result["success"]:
                error_msg = result.get("error", "Unknown error")
                print(f"\n[ERROR] Command execution failed: {error_msg}")
                logger.error(f"Command execution failed: {error_msg}")
                
                # Update task state with error
                output = f"Error: {error_msg}"
                task_state.add_command(command, output, success=False, error=error_msg)
                command_history.append((command, output))
                
                # Check if we should retry
                if not task_state.should_retry():
                    print(f"\n[ERROR] Maximum retry attempts ({task_state.max_retries}) reached. Stopping task.")
                    logger.error(f"Maximum retry attempts ({task_state.max_retries}) reached. Stopping task.")
                    return command_history
                
                print(f"\n[INFO] Retry attempt {task_state.retry_count} of {task_state.max_retries}")
                continue
            
            # Reset retry counter on successful command
            task_state.reset_retry_count()
            
            # Update task state with success
            output = result.get("stdout", "") + result.get("stderr", "")
            task_state.add_command(command, output, success=True)
            command_history.append((command, output))
            
            print("\n[INFO] Command output:")
            print("-" * 50)
            print(output)
            print("-" * 50)
            logger.info(f"Command output: {output}")
            
            # Ask user if they want to continue
            while True:
                user_input = input("\nDo you want to continue with the next command? (y/n): ").strip().lower()
                if user_input in ['y', 'n']:
                    break
                print("Please enter 'y' or 'n'")
            
            if user_input == 'n':
                print("\n[INFO] Task stopped by user")
                logger.info("Task stopped by user")
                return command_history
            
        except Exception as e:
            print(f"\n[ERROR] Error in task execution: {str(e)}")
            logger.error(f"Error in task execution: {str(e)}", exc_info=True)
            return command_history
    
    return command_history

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Codex Core Agent - Execute tasks using local or Azure container instance")
    
    # Add arguments with defaults
    parser.add_argument(
        "--repo", 
        default="https://github.com/Prathmesh234/RFT_OpenAI.git",
        help="GitHub repository URL to clone"
    )
    parser.add_argument(
        "--task",
        default="go into this project folder, list all the files and mention what each file is doing",
        help="Task to execute"
    )
    parser.add_argument(
        "--container",
        choices=["local", "azure"],
        default="azure",
        help="Container type to use (local or azure)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    print("\nWelcome to Codex Core Agent!")
    print("This agent can help you execute tasks using either a local or Azure container instance.")
    
    # Extract project name from repository URL
    project_name = args.repo.split('/')[-1].replace('.git', '')
    
    print(f"\nExecuting task: {args.task}")
    print(f"Repository: {args.repo}")
    print(f"Project name: {project_name}")
    print(f"Container type: {args.container}")
    
    # Override the get_container_type function to use the argument
    def get_container_type() -> str:
        return args.container
    
    # Execute the task
    command_history = complete_task(args.task, args.repo, project_name)
    
    # Print summary
    print("\nTask Summary:")
    print("-" * 50)
    for command, output in command_history:
        print(f"\nCommand: {command}")
        print(f"Output: {output}")
        print("-" * 50)
