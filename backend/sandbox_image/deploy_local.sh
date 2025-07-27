#!/bin/bash

# Exit on error
set -e

# Configuration
CONTAINER_NAME="local-sandbox"
STORAGE_ACCOUNT="codexstorage123"
RESOURCE_GROUP="codex_rg"
FILE_SHARE="code-repos"

echo "=== Creating Azure File Share ==="
# Get storage connection string
STORAGE_KEY=$(az storage account keys list \
    --account-name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --query '[0].value' \
    --output tsv)

# Create file share if it doesn't exist
echo "Creating file share..."
az storage share create \
    --name $FILE_SHARE \
    --account-name $STORAGE_ACCOUNT \
    --account-key $STORAGE_KEY \
    --quota 100

# Get storage connection string
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --query connectionString \
    --output tsv)

echo "=== Building Docker Image ==="
# Build the image
docker build -t local-sandbox .

echo "=== Creating Container with Storage Mount ==="
# Stop and remove existing container if it exists
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Create and start the container
docker run -d \
    --name $CONTAINER_NAME \
    -p 3000:3000 \
    --mount type=volume,source=$FILE_SHARE,target=/projects \
    -e AZURE_STORAGE_CONNECTION_STRING="$STORAGE_CONNECTION_STRING" \
    -e COMMAND_QUEUE="commandqueue" \
    -e RESPONSE_QUEUE="responsequeue" \
    -e GITHUB_TOKEN="$GITHUB_TOKEN" \
    -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    local-sandbox

echo "=== Container Started ==="
echo "Container name: $CONTAINER_NAME"
echo "Projects directory mounted at: /projects"
echo "To access the container shell: docker exec -it $CONTAINER_NAME /bin/bash" 