#!/bin/bash

# Source Python environment variables if they exist
if [ -f .env ]; then
    source .env
fi

# Default port values if not set in environment
STREAMLIT_PORT=${STREAMLIT_PORT:-8502}
API_PORT=${API_PORT:-3000}
WEBRTC_PORT=${WEBRTC_PORT:-3001}

# Function to check if a port is available
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "Warning: Port $port for $service is already in use"
        echo "Attempting to free port $port..."
        kill $(lsof -t -i:$port) 2>/dev/null || true
        sleep 2
    fi
}

# Function to wait for a service to be ready
wait_for_service() {
    local port=$1
    local service=$2
    local max_attempts=30
    local attempt=1
    
    echo "Waiting for $service to be ready on port $port..."
    while ! nc -z localhost $port; do
        if [ $attempt -ge $max_attempts ]; then
            echo "Error: $service failed to start on port $port"
            exit 1
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    echo "$service is ready on port $port"
}

# Check and free ports if needed
check_port $STREAMLIT_PORT "Streamlit"
check_port $API_PORT "API Server"
check_port $WEBRTC_PORT "WebRTC Signaling"

echo "Starting services..."

# 1. Start API Server
echo "Starting API Server on port $API_PORT..."
python3 api_server.py &
API_PID=$!
wait_for_service $API_PORT "API Server"

# 2. Start WebRTC Signaling Server
echo "Starting WebRTC Signaling Server on port $WEBRTC_PORT..."
python3 webrtc_signaling.py &
WEBRTC_PID=$!
wait_for_service $WEBRTC_PORT "WebRTC Signaling"

# 3. Start Streamlit
echo "Starting Streamlit App on port $STREAMLIT_PORT..."
streamlit run main.py --server.port $STREAMLIT_PORT --server.address 0.0.0.0 --server.baseUrlPath="" --server.headless true &
STREAMLIT_PID=$!

# Function to handle cleanup
cleanup() {
    echo "Stopping services..."
    kill $API_PID $WEBRTC_PID $STREAMLIT_PID 2>/dev/null
    exit 0
}

# Register cleanup handler
trap cleanup SIGINT SIGTERM

# Monitor services
while true; do
    if ! kill -0 $API_PID 2>/dev/null; then
        echo "API Server stopped unexpectedly"
        cleanup
    fi
    if ! kill -0 $WEBRTC_PID 2>/dev/null; then
        echo "WebRTC Signaling stopped unexpectedly"
        cleanup
    fi
    if ! kill -0 $STREAMLIT_PID 2>/dev/null; then
        echo "Streamlit App stopped unexpectedly"
        cleanup
    fi
    sleep 5
done
