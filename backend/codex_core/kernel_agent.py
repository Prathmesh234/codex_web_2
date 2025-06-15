import requests
import sys
from pathlib import Path
import json
import logging
import subprocess
import os
from typing import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
SANDBOX_URL = "http://localhost:3000"
PROJECTS_DIR = Path("./projects")
PROJECTS_DIR.mkdir(exist_ok=True)

def check_container_health():
    """
    Check if the sandbox container is healthy and responding
    """
    try:
        response = requests.get(f"{SANDBOX_URL}/health")
        logger.info(f"Container health check response: {response.status_code}")
        logger.info(f"Response content: {response.text}")
        return response.ok
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return False

def ensure_container_running():
    """
    Ensure the local container is running with proper volume mounts
    """
    try:
        # Check if container is already running
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=sandbox-container", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        if "sandbox-container" not in result.stdout:
            # Container not running, start it
            logger.info("Starting local container...")
            subprocess.run([
                "docker", "run", "-d",
                "--name", "sandbox-container",
                "-v", f"{os.path.abspath(PROJECTS_DIR)}:/projects",
                "-p", "3000:3000",
                "sandbox-image"
            ], check=True)
            logger.info("Local container started successfully")
        else:
            logger.info("Local container is already running")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start container: {str(e)}")
        raise

def execute_terminal_command(command: str) -> Dict:
    """
    Execute a terminal command in the local container and return the result.
    
    Args:
        command (str): The command to execute
        
    Returns:
        Dict: A dictionary containing:
            - success (bool): Whether the command executed successfully
            - stdout (str): Standard output
            - stderr (str): Standard error
            - error (str): Error message if any
    """
    try:
        # Ensure container is running
        ensure_container_running()
        
        # Execute the command in the container
        process = subprocess.Popen(
            f"docker exec sandbox-container {command}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Get output and error
        stdout, stderr = process.communicate()
        
        # Check if command was successful
        if process.returncode == 0:
            return {
                "success": True,
                "stdout": stdout,
                "stderr": stderr
            }
        else:
            error_msg = f"Command failed with return code {process.returncode}"
            if stderr:
                error_msg += f"\nError details: {stderr}"
            return {
                "success": False,
                "stdout": stdout,
                "stderr": stderr,
                "error": error_msg
            }
            
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "error": str(e)
        }

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Execute command: python kernel_agent.py execute <command> [project_name]")
        sys.exit(1)
        
    action = sys.argv[1]
    
    if action == "execute":
        if len(sys.argv) < 3:
            print("Usage: python kernel_agent.py execute <command> [project_name]")
            sys.exit(1)
        command = sys.argv[2]
        project_name = sys.argv[3] if len(sys.argv) > 3 else None
        result = execute_terminal_command(command)
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
        
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 