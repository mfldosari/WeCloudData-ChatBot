
#!/bin/bash

# Color functions
info() { echo -e "\033[34m$1\033[0m"; }  # Blue
success() { echo -e "\033[32m$1\033[0m"; }  # Green
error() { echo -e "\033[31m$1\033[0m"; }  # Red

# Load environment variables from .env file
if [ -f .env ]; then
    source .env
else
    error ".env file not found!"
    exit 1
fi
source /home/azureuser/env/bin/activate

CURRENT_DIR=$(pwd)
LOGS_DIR="$CURRENT_DIR/logs"
CHROMA_DB_PATH="$CURRENT_DIR/chromadb"
BACKEND_SCRIPT="$CURRENT_DIR/backend.py"

# Ensure logs directory exists
mkdir -p "$LOGS_DIR"
info "Logs will be stored in: $LOGS_DIR"

# Start FastAPI backend
info "Starting FastAPI backend..."
uvicorn backend:app --host 0.0.0.0 --port 5000 > "$LOGS_DIR/backend.log" 2>&1 &  # Run in background
BACKEND_PID=$!
success "FastAPI backend started with PID $BACKEND_PID."

# Wait for FastAPI to be ready
info "Waiting for FastAPI to start..."
TIMEOUT=60
SECONDS_WAITED=0
while ! nc -z 127.0.0.1 5000; do
  sleep 1
  SECONDS_WAITED=$((SECONDS_WAITED+1))
  if [ $SECONDS_WAITED -ge $TIMEOUT ]; then
      error "FastAPI did not start within $TIMEOUT seconds."
      exit 1
  fi
done
success "FastAPI is running at: http://$SERVER_IP:5000/docs"

# Prevent the script from exiting
tail -f /dev/null

