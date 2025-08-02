import os
import json
import logging
import sys
import argparse
import time
from datetime import datetime
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

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(
    api_key=openai_api_key
)
print("[INFO] OpenAI client initialized with gpt-4o-mini model")

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

async def complete_task_with_ws_streaming(task_name: str, repo_url: str, project_name: str, container_type: str, connection_string: str, broadcast_func, task_id: str) -> List[Tuple[str, str]]:
    """
    Complete task with WebSocket streaming - broadcasts commands/responses in real-time
    """
    import asyncio
    
    print(f"\n[INFO] Starting task: {task_name}")
    logger.info(f"Starting task: {task_name} with {container_type} container")
    
    # Initialize Azure queue if using azure container
    azure_queue = None
    if container_type == "azure" and connection_string:
        azure_queue = initialize_azure_queue(connection_string)
        if not azure_queue:
            raise Exception("Failed to initialize Azure queue")
        print("[INFO] Using azure container instance")
    else:
        print("[INFO] Using local container")
    
    # Clone repository first
    print(f"\n[INFO] Cloning repository: {repo_url}")
    logger.info(f"Cloning repository: {repo_url}")
    
    project_path = f"/projects/{project_name}"
    clone_command = f"git clone {repo_url} {project_path}"
    
    # Broadcast git clone command
    await broadcast_func("command", {
        "command": clone_command,
        "task_id": task_id,
        "timestamp": time.time(),
        "message_id": f"clone_{task_id}"
    })
    
    clone_result = execute_command(clone_command, None, container_type, azure_queue)
    
    # Broadcast git clone response
    await broadcast_func("response", {
        "task_id": task_id,
        "message_id": f"clone_{task_id}",
        "success": clone_result.get("success"),
        "stdout": clone_result.get("stdout", ""),
        "stderr": clone_result.get("stderr", ""),
        "output": clone_result.get("stdout", clone_result.get("stderr", ""))
    })
    
    if not clone_result.get("success"):
        error_msg = f"Failed to clone repository: {clone_result.get('error', 'Unknown error')}"
        await broadcast_func("error", {"task_id": task_id, "message": error_msg})
        raise Exception(error_msg)
    
    print(f"\n[INFO] Repository cloned successfully. Working directory: {project_path}")
    
    # Initialize command history
    command_history = []
    
    # Main task loop
    for iteration in range(50):  # Max 50 commands
        print(f"\n[INFO] === Iteration {iteration + 1} ===")
        
        # Generate command prompt
        prompt = template.render(
            task_name=task_name,
            command_history=command_history,
            current_time=datetime.now().isoformat(),
            total_commands=len(command_history)
        )
        
        print(f"\n[INFO] Generated prompt:")
        print("-" * 50)
        print(prompt)
        print("-" * 50)
        
        # Get command from OpenAI API
        print("\n[INFO] Calling OpenAI API...")
        logger.info("Making OpenAI API call with gpt-4o-mini model")
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
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
            print(f"[DEBUG] 🤖 OpenAI API Response:")
            print(f"[DEBUG] 🤖 Response ID: {getattr(response, 'id', 'No ID')}")
            print(f"[DEBUG] 🤖 Model used: {getattr(response, 'model', 'Unknown model')}")
            print(f"[DEBUG] 🤖 Choices count: {len(response.choices) if response.choices else 0}")
            print(f"[DEBUG] 🤖 Finish reason: {response.choices[0].finish_reason if response.choices and len(response.choices) > 0 else 'No finish reason'}")
            print(f"[DEBUG] 🤖 Message role: {response.choices[0].message.role if response.choices and len(response.choices) > 0 and response.choices[0].message else 'No role'}")
            print(f"[DEBUG] 🤖 Raw content: '{response.choices[0].message.content if response.choices and len(response.choices) > 0 and response.choices[0].message else 'No content'}'")
            print(f"[DEBUG] 🤖 Content length: {len(response.choices[0].message.content) if response.choices and len(response.choices) > 0 and response.choices[0].message and response.choices[0].message.content else 0}")
            
            if response.choices and len(response.choices) > 0:
                command = response.choices[0].message.content.strip()
            else:
                print("[ERROR] 🤖 No choices in OpenAI API response!")
                logger.error("No choices in OpenAI API response")
                command = ""
                
        except Exception as api_error:
            print(f"[ERROR] 🤖 OpenAI API call failed: {str(api_error)}")
            logger.error(f"OpenAI API call failed: {str(api_error)}")
            print("[INFO] Retrying with a simple fallback command...")
            command = "pwd"  # Simple fallback command
        
        print(f"\n[INFO] Generated command: '{command}'")
        logger.info(f"Generated command: '{command}'")
        
        # Log empty commands but continue execution
        if not command or command.strip() == "":
            print("\n[WARNING] 🤖 OpenAI API returned empty command - will attempt to execute anyway")
            logger.warning("OpenAI API returned empty command - will attempt to execute anyway")
            print("[INFO] This might be due to API rate limiting or model issues")
        
        print(f"\n[INFO] Executing command: {command}")
        logger.info(f"Executing command: {command}")
        
        # Check for completion signal
        if command == "TASK_COMPLETED":
            print("\n[INFO] ✅ Task completed successfully!")
            logger.info("Task completed successfully")
            await broadcast_func("completion", {
                "task_id": task_id,
                "status": "completed",
                "message": "Task completed - TASK_COMPLETED signal received"
            })
            break
        
        # Generate message ID for this command
        message_id = f"cmd_{task_id}_{iteration}"
        
        # Broadcast command before execution
        await broadcast_func("command", {
            "command": command,
            "task_id": task_id,
            "timestamp": time.time(),
            "message_id": message_id
        })
        
        # Execute command
        result = execute_command(command, project_path, container_type, azure_queue)
        
        # Extract output
        output = result.get("stdout") or result.get("output") or result.get("stderr") or "No output"
        
        # Broadcast response after execution
        await broadcast_func("response", {
            "task_id": task_id,
            "message_id": message_id,
            "success": result.get("success"),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "output": output
        })
        
        print(f"\n[INFO] Command output:")
        print("-" * 50)
        print(output)
        print("-" * 50)
        logger.info(f"Command output: {output}")
        
        # Add to command history
        command_history.append((command, output))
        
        # Simulated approval for streaming mode
        print("Do you want to continue with the next command? (y/n): y")
        print("[INFO] Auto-approved command for real-time streaming")
    
    return command_history

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
            
            # Get command from OpenAI API
            print("\n[INFO] Calling OpenAI API...")
            logger.info("Making OpenAI API call with gpt-4o-mini model")
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
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
                print(f"[DEBUG] 🤖 OpenAI API Response:")
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
                    print("[ERROR] 🤖 No choices in OpenAI API response!")
                    logger.error("No choices in OpenAI API response")
                    command = ""
                    
            except Exception as api_error:
                print(f"[ERROR] 🤖 OpenAI API call failed: {str(api_error)}")
                logger.error(f"OpenAI API call failed: {str(api_error)}")
                print("[INFO] Retrying with a simple fallback command...")
                command = "pwd"  # Simple fallback command
            
            print(f"\n[INFO] Generated command: '{command}'")
            logger.info(f"Generated command: '{command}'")
            
            # Log empty commands but continue execution
            if not command or command.strip() == "":
                print("\n[WARNING] 🤖 OpenAI API returned empty command - will attempt to execute anyway")
                logger.warning("OpenAI API returned empty command - will attempt to execute anyway")
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
