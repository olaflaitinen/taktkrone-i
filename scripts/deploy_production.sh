#!/bin/bash
# Production Deployment Script for TAKTKRONE-I
set -euo pipefail

echo "TAKTKRONE-I Production Deployment"
echo "====================================="

# Configuration
IMAGE_TAG=${1:-"latest"}
NAMESPACE="taktkrone-prod"
CLUSTER="production-cluster"
REGISTRY="registry.taktkrone.ai"

# Pre-deployment checks
echo "[INFO] Running pre-deployment checks..."

# Check kubectl connection
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "[ERROR] Cannot connect to Kubernetes cluster"
    exit 1
fi

# Check namespace
if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
    echo "[INFO] Creating namespace $NAMESPACE..."
    kubectl create namespace "$NAMESPACE"
fi

# Check Docker registry access
echo "[INFO] Checking registry access..."
if ! docker pull "$REGISTRY/taktkrone/occlm-api:$IMAGE_TAG" >/dev/null 2>&1; then
    echo "[ERROR] Cannot pull image from registry"
    exit 1
fi

# Deploy infrastructure components
echo "[INFO] Deploying infrastructure components..."

kubectl apply -f configs/deployment/redis.yaml -n "$NAMESPACE"
kubectl apply -f configs/deployment/vector-store.yaml -n "$NAMESPACE"

# Wait for dependencies
echo "[INFO] Waiting for dependencies to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n "$NAMESPACE" --timeout=120s
kubectl wait --for=condition=ready pod -l app=qdrant -n "$NAMESPACE" --timeout=120s

# Deploy main application
echo "[INFO] Deploying TAKTKRONE-I API..."

# Update image tag in deployment
sed -i "s|image: .*taktkrone/occlm-api:.*|image: $REGISTRY/taktkrone/occlm-api:$IMAGE_TAG|g" configs/deployment/production.yaml

kubectl apply -f configs/deployment/production.yaml -n "$NAMESPACE"

# Wait for deployment
echo "[INFO] Waiting for deployment to complete..."
kubectl rollout status deployment/occlm-api -n "$NAMESPACE" --timeout=300s

# Health checks
echo "[INFO] Running health checks..."

# Get service URL
if kubectl get service occlm-api-lb -n "$NAMESPACE" >/dev/null 2>&1; then
    SERVICE_URL=$(kubectl get service occlm-api-lb -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    HEALTH_URL="http://$SERVICE_URL:8000/health"

    # Wait for health check to pass
    for i in {1..30}; do
        if curl -f "$HEALTH_URL" >/dev/null 2>&1; then
            echo "[SUCCESS] Health check passed"
            break
        fi
        echo "[INFO] Waiting for health check... ($i/30)"
        sleep 10
    done
else
    echo "[WARN] LoadBalancer service not found, using port-forward for testing"
    kubectl port-forward service/occlm-api 8080:8000 -n "$NAMESPACE" &
    PF_PID=$!
    sleep 5

    if curl -f "http://localhost:8080/health" >/dev/null 2>&1; then
        echo "[SUCCESS] Health check passed"
    else
        echo "[ERROR] Health check failed"
        exit 1
    fi

    kill $PF_PID 2>/dev/null || true
fi

# Performance test
echo "[INFO] Running basic performance test..."
if command -v hey >/dev/null 2>&1; then
    hey -n 100 -c 10 "$HEALTH_URL" > /dev/null
    echo "[SUCCESS] Performance test completed"
else
    echo "[WARN] 'hey' not found, skipping performance test"
fi

echo ""
echo "[SUCCESS] Deployment completed successfully!"
echo "[INFO] Dashboard: https://grafana.taktkrone.ai"
echo "[INFO] Metrics: https://prometheus.taktkrone.ai"
echo "[INFO] Logs: kubectl logs -f deployment/occlm-api -n $NAMESPACE"
echo ""
echo "[ENDPOINTS] API Endpoints:"
echo "   Health: $HEALTH_URL"
echo "   API: ${HEALTH_URL%/health}/v1/chat"
echo ""
