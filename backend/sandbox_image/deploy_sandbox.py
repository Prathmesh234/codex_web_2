import subprocess
import json
import uuid
import os
from pathlib import Path

TEMPLATE_FILE = Path(__file__).parent / "sandbox_template.json"
RESOURCE_GROUP = "codex_rg"
LOCATION = "eastus"
REGISTRY_NAME = "registrycodex64425830"
IMAGE_NAME = "sandbox/sandbox-image:bashfix"

def deploy_sandbox(resource_group: str = RESOURCE_GROUP, location: str = LOCATION) -> dict:
    """Deploy the sandbox ARM template and return connection info.

    This function requires the Azure CLI to be installed and logged in.
    """
    deployment_name = f"deploy-sandbox-{uuid.uuid4().hex[:8]}"
    
    # Set GitHub token manually for ARM deployment
    env = os.environ.copy()
    env["GITHUB_TOKEN"] = ""  # <-- Set your token here
    
    try:
        # Run the deploy_arm.sh script with parameters
        script_path = Path(__file__).parent / "deploy_arm.sh"
        print(f"[DEBUG] Running deployment script: {script_path}")
        print(f"[DEBUG] Parameters: resource_group={resource_group}, location={location}")
        
        result = subprocess.run([str(script_path), resource_group, location], env=env, capture_output=True, text=True, check=False)
        
        print(f"[DEBUG] Deployment script exit code: {result.returncode}")
        if result.stdout:
            print(f"[DEBUG] Deployment stdout: {result.stdout}")
        if result.stderr:
            print(f"[DEBUG] Deployment stderr: {result.stderr}")
        
        if result.returncode != 0:
            return {
                "status": "error",
                "message": f"Deployment failed: {result.stderr}",
                "id": deployment_name
            }
        
        # Extract connection string from the output
        # Use the resource group passed to the script
        try:
            print(f"[DEBUG] Retrieving connection string from deployment...")
            connection_string = subprocess.check_output([
                "az", "deployment", "group", "show",
                "--resource-group", resource_group,
                "--name", "deploy-sandbox",
                "--query", "properties.outputs.storageConnectionString.value",
                "-o", "tsv"
            ], text=True).strip()
            
            print(f"[DEBUG] Retrieved connection string: {connection_string[:50]}...")
            
            if not connection_string or connection_string == "null" or len(connection_string) < 50:
                print(f"[ERROR] Invalid connection string retrieved: '{connection_string}'")
                return {
                    "status": "error",
                    "message": f"Invalid connection string retrieved: '{connection_string}'",
                    "id": deployment_name
                }
            
            # Extract and show storage account name for verification
            try:
                # Parse connection string to get storage account name
                import re
                account_match = re.search(r'AccountName=([^;]+)', connection_string)
                if account_match:
                    storage_account_name = account_match.group(1)
                    print(f"[DEBUG] 🎯 DEPLOYMENT VERIFICATION:")
                    print(f"[DEBUG] 🎯 Created/Using Storage Account: {storage_account_name}")
                    print(f"[DEBUG] 🎯 Check this account in Azure Portal!")
                    print(f"[DEBUG] 🎯 Queue names: commandqueue, responsequeue")
            except Exception as e:
                print(f"[DEBUG] Could not parse storage account name: {e}")
            
            return {
                "status": "success",
                "storage_connection_string": connection_string,
                "id": deployment_name
            }
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to retrieve connection string: {e}")
            return {
                "status": "error", 
                "message": f"Deployment completed but couldn't retrieve connection string: {e}",
                "id": deployment_name
            }
            

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to run deployment script: {str(e)}",
            "id": deployment_name
        }

def main():
    import sys
    if len(sys.argv) != 3:
        print("Usage: python deploy_sandbox.py <resource_group> <location>")
        sys.exit(1)
    resource_group = sys.argv[1]
    location = sys.argv[2]
    result = deploy_sandbox(resource_group, location)
    print("\nDeployment result:")
    print(result)
    if result.get("status") != "success":
        sys.exit(1)

if __name__ == "__main__":
    main()
