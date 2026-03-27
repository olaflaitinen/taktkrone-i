#!/bin/bash

# TAKTKRONE-I Serving Deployment Script
# Usage: ./scripts/serve/deploy_production.sh

set -e

echo "Deploying TAKTKRONE-I to production..."

# Configuration
MODEL_PATH="./checkpoints/sft-baseline"
API_PORT=8000
DEMO_PORT=7860
LOG_LEVEL="info"
WORKERS=4

# Load environment variables
if [ -f ".env.production" ]; then
    echo "Loading production environment..."
    source .env.production
fi

# Validate model
if [ ! -d "$MODEL_PATH" ]; then
    echo "Error: Model not found at $MODEL_PATH"
    exit 1
fi

echo "Model path: $MODEL_PATH"

# Create logs directory
mkdir -p logs/api logs/demo

# Health check function
check_health() {
    local port=$1
    local max_attempts=30
    local attempt=1

    echo "Checking health on port $port..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            echo "[OK] Service healthy on port $port"
            return 0
        fi

        echo "Attempt $attempt/$max_attempts: Service not ready, waiting..."
        sleep 2
        ((attempt++))
    done

    echo "[FAIL] Service failed to start on port $port"
    return 1
}

# Stop existing services
echo "Stopping existing services..."
pkill -f "occlm serve" || true
sleep 2

# Start API server
echo "Starting API server on port $API_PORT..."
nohup occlm serve api \
    --model-path "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port $API_PORT \
    --workers $WORKERS \
    --log-level $LOG_LEVEL \
    --log-dir logs/api \
    > logs/api/server.log 2>&1 &

API_PID=$!
echo "API server started with PID: $API_PID"

# Wait for API to be ready
if ! check_health $API_PORT; then
    echo "API server failed to start properly"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

# Start demo UI
echo "Starting demo UI on port $DEMO_PORT..."
nohup occlm serve demo \
    --model-path "$MODEL_PATH" \
    --api-url "http://localhost:$API_PORT" \
    --host 0.0.0.0 \
    --port $DEMO_PORT \
    --log-level $LOG_LEVEL \
    > logs/demo/ui.log 2>&1 &

DEMO_PID=$!
echo "Demo UI started with PID: $DEMO_PID"

# Save PIDs for later management
echo $API_PID > logs/api.pid
echo $DEMO_PID > logs/demo.pid

# Display service status
echo ""
echo "[SUCCESS] TAKTKRONE-I deployed successfully!"
echo ""
echo "Services:"
echo "  - API Server: http://localhost:$API_PORT"
echo "  - Demo UI:    http://localhost:$DEMO_PORT"
echo ""
echo "API Endpoints:"
echo "  - Health:     http://localhost:$API_PORT/health"
echo "  - Query:      POST http://localhost:$API_PORT/v1/query"
echo "  - Model Info: http://localhost:$API_PORT/v1/model/info"
echo ""
echo "Process IDs:"
echo "  - API Server: $API_PID"
echo "  - Demo UI:    $DEMO_PID"
echo ""
echo "Logs:"
echo "  - API Logs:   logs/api/server.log"
echo "  - Demo Logs:  logs/demo/ui.log"
echo ""

# Test API with sample query
echo "Testing API with sample query..."
API_RESPONSE=$(curl -s -X POST \
    "http://localhost:$API_PORT/v1/query" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "Signal failure at Station A on Line 1. What should OCC do?",
        "operator": "generic",
        "max_tokens": 100
    }' || echo "API test failed")

if [ "$API_RESPONSE" != "API test failed" ]; then
    echo "[OK] API test successful:"
    echo "$API_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$API_RESPONSE"
else
    echo "[WARN] API test failed - service may still be starting"
fi

echo ""
echo "Deployment complete!"
echo ""
echo "Management commands:"
echo "  Stop services: ./scripts/serve/stop_services.sh"
echo "  View logs:     tail -f logs/api/server.log"
echo "  Restart:       ./scripts/serve/restart_services.sh"
