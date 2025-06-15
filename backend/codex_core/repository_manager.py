import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
SANDBOX_URL = "http://localhost:3000"

def check_container_health():
    """
    Check if the sandbox container is healthy and responding
    """
    try:
        response = requests.get(f"{SANDBOX_URL}/health")
        logger.info(f"Container health check response: {response.status_code}")
        return response.ok
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return False

def clone_repository(git_url: str, project_name: str):
    """
    Clone a git repository into the sandbox container
    
    Args:
        git_url (str): URL of the git repository to clone
        project_name (str): Name of the project directory
        
    Returns:
        dict: Response containing success status and any error messages
    """
    try:
        if not check_container_health():
            return {"success": False, "error": "Container is not responding properly"}

        logger.info(f"Cloning repository: {git_url}")
        response = requests.post(
            f"{SANDBOX_URL}/clone",
            json={
                "repoUrl": git_url,
                "projectName": project_name
            }
        )
        
        logger.info(f"Clone response status: {response.status_code}")
        
        if not response.ok:
            logger.error("Error: Failed to clone repository")
            try:
                error_details = response.json()
                logger.error(f"Error details: {error_details}")
                return {"success": False, "error": error_details}
            except:
                logger.error(f"Raw response: {response.text}")
                return {"success": False, "error": response.text}
        
        logger.info("Repository cloned successfully!")
        return {"success": True, "message": "Repository cloned successfully"}
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Error: Could not connect to the sandbox container. Make sure it's running on port 3000")
        logger.error(f"Connection error details: {str(e)}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        return {"success": False, "error": str(e)} 