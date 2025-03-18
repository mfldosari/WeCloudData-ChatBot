
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

# Start ChromaDB
info "Starting ChromaDB..."
chroma run --host 0.0.0.0 --path "$CHROMA_DB_PATH" > "$LOGS_DIR/chroma.log" 2>&1 &  # Run in background
CHROMA_PID=$!
success "ChromaDB started with PID $CHROMA_PID."

# Prevent the script from exiting
tail -f /dev/null

