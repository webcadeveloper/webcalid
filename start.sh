#!/bin/bash

# Enhanced startup script with better error handling and service management

# Source environment variables if they exist
if [ -f .env ]; then
    source .env
fi

# Default port values with fixed assignments to prevent conflicts
STREAMLIT_PORT=${STREAMLIT_PORT:-8502}
API_PORT=${API_PORT:-3000}
WEBRTC_PORT=${WEBRTC_PORT:-3001}

# Log file setup
LOGDIR="logs"
mkdir -p $LOGDIR
MAIN_LOG="$LOGDIR/startup.log"

# Enhanced logging function
log() {
    local level=$1
    shift
    local message=$@
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a $MAIN_LOG
}

# Error handling function
handle_error() {
    local service=$1
    local error_msg=$2
    log "ERROR" "Service $service failed: $error_msg"
    cleanup "Error in $service"
    exit 1
}

# New version of check_port using ss
check_port() {
    local port=$1
    local service=$2
    local timeout=30
    local start_time=$(date +%s)

    log "INFO" "Checking port $port for $service..."
    while ss -tuln | grep ":$port" >/dev/null 2>&1; do
        local current_time=$(date +%s)
        if [ $((current_time - start_time)) -gt $timeout ]; then
            handle_error "$service" "Port $port is still in use after ${timeout}s timeout"
        fi
        log "WARN" "Port $port is in use, attempting to free..."
        # Kill process using the port
        ss -tuln | grep ":$port" | awk '{print $5}' | cut -d':' -f1 | xargs kill -9
        sleep 2
    done
}

# Enhanced service readiness check
wait_for_service() {
    local port=$1
    local service=$2
    local max_attempts=30
    local attempt=1
    
    log "INFO" "Waiting for $service to be ready on port $port..."
    while ! nc -z localhost $port 2>/dev/null; do
        if [ $attempt -ge $max_attempts ]; then
            handle_error "$service" "Failed to start after $max_attempts attempts"
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    log "INFO" "$service is ready on port $port"
}

# Cleanup function with reason logging
cleanup() {
    local reason=$1
    log "INFO" "Cleaning up services... Reason: $reason"
    
    for pid in $API_PID $WEBRTC_PID $STREAMLIT_PID; do
        if [ ! -z "$pid" ] && kill -0 $pid 2>/dev/null; then
            kill $pid 2>/dev/null || log "WARN" "Failed to kill process $pid"
        fi
    done
}

# Initialize services
initialize_services() {
    # Force kill any existing processes using our ports
    for port in $API_PORT $WEBRTC_PORT $STREAMLIT_PORT; do
        if ss -tuln | grep ":$port" >/dev/null 2>&1; then
            log "WARN" "Killing existing process on port $port"
            ss -tuln | grep ":$port" | awk '{print $5}' | cut -d':' -f1 | xargs kill -9
        fi
    done
    
    sleep 2  # Wait for ports to be released
    
    # Check all required ports first
    check_port $API_PORT "API Server"
    check_port $WEBRTC_PORT "WebRTC Signaling"
    check_port $STREAMLIT_PORT "Streamlit"

    # 1. Start API Server (Primary backend service)
    log "INFO" "Starting API Server on port $API_PORT..."
    python3 api_server.py > "$LOGDIR/api_server.log" 2>&1 &
    API_PID=$!
    wait_for_service $API_PORT "API Server"

    # 2. Start WebRTC Signaling Server
    log "INFO" "Starting WebRTC Signaling Server on port $WEBRTC_PORT..."
    python3 webrtc_signaling.py > "$LOGDIR/webrtc.log" 2>&1 &
    WEBRTC_PID=$!
    wait_for_service $WEBRTC_PORT "WebRTC Signaling"

    # 3. Start Streamlit (Frontend application)
    log "INFO" "Starting Streamlit App on port $STREAMLIT_PORT..."
    streamlit run main.py \
        --server.port $STREAMLIT_PORT \
        --server.address 0.0.0.0 \
        --server.baseUrlPath="" \
        --server.headless true \
        > "$LOGDIR/streamlit.log" 2>&1 &
    STREAMLIT_PID=$!
}

# Signal handlers
trap 'cleanup "Received SIGINT"; exit 1' SIGINT
trap 'cleanup "Received SIGTERM"; exit 1' SIGTERM

# Main execution
log "INFO" "Starting application deployment..."
initialize_services

# Monitor services with enhanced error detection
while true; do
    for service in "API Server:$API_PID" "WebRTC Signaling:$WEBRTC_PID" "Streamlit App:$STREAMLIT_PID"; do
        IFS=: read name pid <<< "$service"
        if ! kill -0 $pid 2>/dev/null; then
            handle_error "$name" "Service stopped unexpectedly"
        fi
    done
    sleep 5
done
