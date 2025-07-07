# Codex Sandbox Image

This directory contains the Docker image, scripts, and templates for the Codex sandbox environment. The sandbox can be run **locally** (using Docker) or **in the cloud** (using Azure ARM templates).

---

## Table of Contents
- [Local Sandbox (Docker)](#local-sandbox-docker)
- [Cloud Sandbox (Azure)](#cloud-sandbox-azure)
- [Troubleshooting](#troubleshooting)
- [Usage in Codex Web](#usage-in-codex-web)

---

## Local Sandbox (Docker)

### Prerequisites
- **Docker** must be installed and running on your machine.
- Port **3000** must be available (the sandbox will listen on this port).

### Building the Sandbox Image
```bash
docker build -t sandbox-image .
```

### Running the Sandbox Container
```bash
docker run -d \
  --name sandbox-container \
  -v $(pwd)/../../projects:/projects \
  -p 3000:3000 \
  sandbox-image
```
- `-v $(pwd)/../../projects:/projects` mounts the `projects` directory from the repo root into the container for persistent storage.
- `-p 3000:3000` exposes the sandbox API on port 3000.

### Health Check
```bash
curl http://localhost:3000/health
```
You should see a JSON response like:
```json
{"status": "ok", "shell": "bash"}
```

### Stopping and Removing the Container
```bash
docker stop sandbox-container
docker rm sandbox-container
```

### Rebuilding the Image
```bash
docker build -t sandbox-image .
```

---

## Cloud Sandbox (Azure)

You can deploy a sandbox environment to Azure using the provided ARM template (`sandbox_template.json`) and the deployment script (`deploy_sandbox.py`).

### Prerequisites
- **Azure CLI** must be installed and you must be logged in (`az login`).
- You need permission to create resource groups and deploy resources in your Azure subscription.
- Environment variable `GITHUB_TOKEN` must be set to a GitHub personal access token for repository access.

### Deployment Script
- The script `deploy_sandbox.py` will deploy the resources defined in `sandbox_template.json` to Azure.

### Usage

Before deploying, ensure you have set a GitHub personal access token with appropriate scopes:

```bash
export GITHUB_TOKEN=<your_github_personal_access_token>
```

Run the deployment script from the `backend/sandbox_image` directory:

```bash
python deploy_sandbox.py <resource_group> <location>
```

- `<resource_group>`: The name of the Azure resource group to deploy to (will be created if it doesn't exist)
- `<location>`: The Azure region (e.g., `eastus`, `westeurope`)

#### Example
```bash
python deploy_sandbox.py codex-sandbox-rg eastus
```

This will:
- Deploy the ARM template to the specified resource group and location
- Output connection information (such as storage connection string) if successful

### What it does
- Uses the Azure CLI to run:
  ```bash
  az deployment group create \
    --resource-group <resource_group> \
    --name <deployment_name> \
    --template-file sandbox_template.json \
    --parameters location=<location>
  ```
- Provisions all resources defined in `sandbox_template.json` (VMs, storage, etc. as specified)

---

## Troubleshooting
- Make sure Docker or Azure CLI is installed and you have permission to run the commands.
- Ensure port 3000 is not in use by another process (for local Docker).
- For Azure, ensure your account has sufficient permissions and the resource group/location are valid.
- If you encounter issues, check logs:
  - Docker: `docker logs sandbox-container`
  - Azure: Azure Portal or CLI output

---

## Usage in Codex Web
- The backend will automatically build and start the **local** sandbox container if it is not running when required.
- For **cloud** deployments, use the deployment script as described above. You may need to configure the backend to use the Azure sandbox (see backend documentation for details).

---

## Summary Table
| Deployment Type | How to Run | File(s) Used | Prerequisites |
|----------------|------------|--------------|---------------|
| Local (Docker) | `docker build` + `docker run` | Dockerfile, start.sh, index.js | Docker |
| Cloud (Azure)  | `python deploy_sandbox.py <resource_group> <location>` | deploy_sandbox.py, sandbox_template.json | Azure CLI, Azure account | 