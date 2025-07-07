#!/bin/bash
set -e

# ─── Validate required env vars ────────────────────────────────────────────────
if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: \$GITHUB_TOKEN is not set"
  exit 1
fi

# ─── User & ACR configuration ─────────────────────────────────────────────────
RESOURCE_GROUP="${1:-codex_rg}"
LOCATION="${2:-eastus}"
CONTAINER_NAME="${3:-sandbox-container}"
STORAGE_ACCOUNT="${4:-}"
REGISTRY_NAME="registrycodex64425830"
IMAGE_NAME="sandbox/sandbox-image:bashfix"

# ─── Build & push multi-platform Linux image ──────────────────────────────────
docker buildx rm sbx-builder || true
docker buildx create --use --bootstrap --name sbx-builder
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ${REGISTRY_NAME}.azurecr.io/${IMAGE_NAME} \
  --push .

# ─── Retrieve ACR creds ───────────────────────────────────────────────────────
REGISTRY_USERNAME=$(az acr credential show -n $REGISTRY_NAME --query username -o tsv)
REGISTRY_PASSWORD=$(az acr credential show -n $REGISTRY_NAME --query "passwords[0].value" -o tsv)

# ─── Deploy via ARM ────────────────────────────────────────────────────────────
echo "=== Deploying container group '$CONTAINER_NAME' ==="

az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --name "deploy-sandbox" \
  --template-file sandbox_template.json \
  --parameters \
      registryName="$REGISTRY_NAME" \
      containerImage="${REGISTRY_NAME}.azurecr.io/${IMAGE_NAME}" \
      containerRegistryServer="${REGISTRY_NAME}.azurecr.io" \
      containerRegistryUsername="$REGISTRY_USERNAME" \
      containerRegistryPassword="$REGISTRY_PASSWORD" \
      location="$LOCATION" \
      fileShareName="projects" \
      containerName="$CONTAINER_NAME" \
      githubToken="$GITHUB_TOKEN" \
      ${STORAGE_ACCOUNT:+storageAccountName="$STORAGE_ACCOUNT"}

# ─── Output summary ────────────────────────────────────────────────────────────
IP=$(az container show -g $RESOURCE_GROUP -n $CONTAINER_NAME --query ipAddress.ip -o tsv)
STORAGE=$(az deployment group show -g $RESOURCE_GROUP -n deploy-sandbox \
           --query "properties.outputs.storageAccountName.value" -o tsv)
CONNECTION_STRING=$(az deployment group show -g $RESOURCE_GROUP -n deploy-sandbox \
           --query "properties.outputs.storageConnectionString.value" -o tsv)

echo "Deployment complete!"
echo " • Container: $CONTAINER_NAME @ $IP"
echo " • Storage Account: $STORAGE"
echo " • Connection String: $CONNECTION_STRING"