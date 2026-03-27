#!/bin/bash

# TAKTKRONE-I Service Management Script
# Usage: ./scripts/serve/stop_services.sh

set -e

echo "Stopping TAKTKRONE-I services..."

# Function to stop a service by PID file
stop_service() {
    local service_name=$1
    local pid_file=$2

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping $service_name (PID: $pid)..."
            kill "$pid"

            # Wait for graceful shutdown
            local attempts=0
            while kill -0 "$pid" 2>/dev/null && [ $attempts -lt 10 ]; do
                sleep 1
                ((attempts++))
            done

            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "Force killing $service_name..."
                kill -9 "$pid" 2>/dev/null || true
            fi

            echo "[OK] $service_name stopped"
        else
            echo "[OK] $service_name was not running"
        fi

        rm -f "$pid_file"
    else
        echo "[OK] No PID file found for $service_name"
    fi
}

# Stop API server
stop_service "API Server" "logs/api.pid"

# Stop demo UI
stop_service "Demo UI" "logs/demo.pid"

# Kill any remaining occlm serve processes
echo "Cleaning up any remaining occlm serve processes..."
pkill -f "occlm serve" || true

echo ""
echo "All TAKTKRONE-I services stopped successfully!"
