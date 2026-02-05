#!/bin/bash
#
# Deploy AO World Engine Frontend to Cloud Run
#

set -e

# Configuration
PROJECT_ID="wandern-project-startup"
REGION="us-central1"
SERVICE_NAME="ao-world-engine"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(dirname "$SCRIPT_DIR")/frontend"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     AO World Engine - Frontend Cloud Run Deployment       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check gcloud
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI not found"
    exit 1
fi

echo -e "${YELLOW}Building and deploying frontend...${NC}"
echo "  Project: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo ""

cd "$FRONTEND_DIR"

# Build and push with Cloud Build
echo -e "${CYAN}Building Docker image with Cloud Build...${NC}"
gcloud builds submit --tag "$IMAGE_NAME" --project "$PROJECT_ID"

# Deploy to Cloud Run
echo -e "${CYAN}Deploying to Cloud Run...${NC}"
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --platform managed \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --port 8080 \
    --min-instances 0 \
    --max-instances 10

# Get the URL
URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --project "$PROJECT_ID" --format 'value(status.url)')

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Deployment Complete!                   ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Frontend URL:${NC} $URL"
echo ""
echo -e "${YELLOW}Features:${NC}"
echo "  • 800 NPCs loaded from JSON"
echo "  • Live AO data polling"
echo "  • Mobile responsive UI"
echo "  • Graph, Explore, NPCs, Chat pages"
echo ""
