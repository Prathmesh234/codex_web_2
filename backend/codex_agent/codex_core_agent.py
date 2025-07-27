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

# Also try loading from parent directory as backup
parent_env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=parent_env_path)
print(f"[INFO] Also loading .env from: {parent_env_path}")

# Initialize OpenRouter client
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_base_url = os.getenv("OPENROUTER_BASE_URL")

if not openrouter_api_key:
    raise ValueError("OPENROUTER_API_KEY environment variable is required")
if not openrouter_base_url:
    raise ValueError("OPENROUTER_BASE_URL environment variable is required")

client = OpenAI(
    api_key=openrouter_api_key,
    base_url=openrouter_base_url
)
print("[INFO] OpenRouter client initialized with o3-mini model")

# Initialize Jinja environment
template_dir = Path(__file__).parent
env = Environment(loader=FileSystemLoader(template_dir))
template = env.get_template('codex_core_prompt.jinja')
print("[INFO] Jinja template loaded")



def initialize_azure_queue(connection_string: str) -> Optional[AzureQueueManager]:
    """Initialize Azure Queue Manager with provided connection string"""
    print(f"[DEBUG] Using connection string: {connection_string[:50]}...")
    try:
        return AzureQueueManager(connection_string)
    except Exception as e:
        print(f"[ERROR] Failed to initialize Azure Queue Manager: {str(e)}")
        return None

def execute_command(command: str, project_name: Optional[str], container_type: str, azure_queue: Optional[AzureQueueManager]) -> Dict:
    """Execute command either locally or via Azure queue"""
    print(f"[DEBUG] execute_command called with: container_type={container_type}, azure_queue={azure_queue is not None}")
    
    if container_type == 'azure' and azure_queue:
        print(f"[DEBUG] Sending command to Azure queue: {command}")
        try:
            result = azure_queue.execute_command(command, project_name)
            print(f"[DEBUG] Azure queue response: {result}")
            return result
        except Exception as e:
            print(f"\n[ERROR] Azure queue operation failed: {str(e)}")
            logger.error(f"Azure queue operation failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    else:
        print(f"[DEBUG] Executing command locally: {command}")
        return execute_terminal_command(command)

def complete_task(task_name: str, repo_url: str, project_name: str, container_type: str = "azure", connection_string: Optional[str] = None) -> List[Tuple[str, str]]:
    """
    Execute a task using GPT-4 to generate and execute Linux commands.
    
    Args:
        task_name (str): Description of the task to complete
        repo_url (str): GitHub repository URL to clone
        project_name (str): Name of the project/repository
        container_type (str): Type of container to use ("local" or "azure"), defaults to "azure"
        connection_string (Optional[str]): Azure storage connection string for azure container type
        
    Returns:
        List[Tuple[str, str]]: List of (command, output) tuples executed during the session
    """
    command_history = []
    task_state = TaskState(
        task_name=task_name,
        current_directory="/projects"  # Default directory
    )
    
    # Use the provided container_type parameter
    azure_queue = None
    if container_type == 'azure':
        if connection_string:
            azure_queue = initialize_azure_queue(connection_string)
        else:
            print("[ERROR] Azure container type selected but no connection string provided")
            return command_history
    
    if container_type == 'azure' and not azure_queue:
        print("\n[ERROR] Azure container instance selected but Azure Queue Manager initialization failed.")
        print("[ERROR] Cannot proceed without Azure queue. Local container fallback is disabled.")
        return command_history
    
    print(f"\n[INFO] Starting task: {task_name}")
    print(f"[INFO] Using {container_type} container instance")
    logger.info(f"Starting task: {task_name} with {container_type} container")
    
    # Clone repository first
    clone_command = f"git clone {repo_url} /projects/{project_name}"
    print(f"\n[INFO] Cloning repository: {repo_url}")
    logger.info(f"Cloning repository: {repo_url}")
    
    print(f"[DEBUG] About to execute command: {clone_command}")
    print(f"[DEBUG] Container type: {container_type}")
    print(f"[DEBUG] Azure queue initialized: {azure_queue is not None}")
    
    result = execute_command(clone_command, None, container_type, azure_queue)
    print(f"[DEBUG] Command execution result: {result}")
    
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
            
            # Get command from OpenRouter API
            print("\n[INFO] Calling OpenRouter API...")
            logger.info("Making OpenRouter API call with o3-mini model")
            
            try:
                response = client.chat.completions.create(
                    model="o3-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                
                # Debug the full API response
                print(f"[DEBUG] 🤖 OpenRouter API Response:")
                print(f"[DEBUG] 🤖 Response ID: {getattr(response, 'id', 'No ID')}")
                print(f"[DEBUG] 🤖 Model used: {getattr(response, 'model', 'Unknown model')}")
                print(f"[DEBUG] 🤖 Choices count: {len(response.choices) if response.choices else 0}")
                
                if response.choices and len(response.choices) > 0:
                    choice = response.choices[0]
                    print(f"[DEBUG] 🤖 Finish reason: {getattr(choice, 'finish_reason', 'Unknown')}")
                    print(f"[DEBUG] 🤖 Message role: {getattr(choice.message, 'role', 'Unknown')}")
                    raw_content = choice.message.content
                    print(f"[DEBUG] 🤖 Raw content: '{raw_content}'")
                    print(f"[DEBUG] 🤖 Content length: {len(raw_content) if raw_content else 0}")
                    
                    command = raw_content.strip() if raw_content else ""
                else:
                    print("[ERROR] 🤖 No choices in OpenRouter API response!")
                    logger.error("No choices in OpenRouter API response")
                    command = ""
                    
            except Exception as api_error:
                print(f"[ERROR] 🤖 OpenRouter API call failed: {str(api_error)}")
                logger.error(f"OpenRouter API call failed: {str(api_error)}")
                print("[INFO] Retrying with a simple fallback command...")
                command = "pwd"  # Simple fallback command
            
            print(f"\n[INFO] Generated command: '{command}'")
            logger.info(f"Generated command: '{command}'")
            
            # Log empty commands but continue execution
            if not command or command.strip() == "":
                print("\n[WARNING] 🤖 OpenRouter API returned empty command - will attempt to execute anyway")
                logger.warning("OpenRouter API returned empty command - will attempt to execute anyway")
                print("[INFO] This might be due to API rate limiting or model issues")
            
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
            
            # Auto-approve all commands for real-time streaming
            print("\nDo you want to continue with the next command? (y/n): y")
            print("[INFO] Auto-approved command for real-time streaming")
            
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
    
    # Execute the task
    command_history = complete_task(args.task, args.repo, project_name, args.container)
    
    # Print summary
    print("\nTask Summary:")
    print("-" * 50)
    for command, output in command_history:
        print(f"\nCommand: {command}")
        print(f"Output: {output}")
        print("-" * 50)
