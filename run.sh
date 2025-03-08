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

# Ensure that GitHub username and PAT are set in the .env file
if [ -z "$GITHUB_USERNAME" ] || [ -z "$GITHUB_PAT" ]; then
    error "GitHub username or PAT is missing in .env file!"
    exit 1
fi

# Set variables
REPO_URL="https://$GITHUB_USERNAME:$GITHUB_PAT@github.com/mfldosari/WeCloudData-ChatBot.git"
CURRENT_DIR=$(pwd)
LOGS_DIR="$CURRENT_DIR/logs"
CHROMA_DB_PATH="$CURRENT_DIR/chromadb"
CHATBOT_SCRIPT="$CURRENT_DIR/chatbot.py"
BACKEND_SCRIPT="$CURRENT_DIR/backend.py"
SERVER_IP=$(hostname -I | awk '{print $1}')

# Ensure logs directory exists
mkdir -p "$LOGS_DIR"
info "Logs will be stored in: $LOGS_DIR"

# Pull latest code from GitHub
info "Updating repository from GitHub..."
if [ ! -d ".git" ]; then
    error "This is not a Git repository. Cloning..."
    git clone $REPO_URL $CURRENT_DIR
else
    git pull origin main
fi
success "Repository updated successfully."

# Install dependencies
info "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    success "Python dependencies installed."
fi

# Start ChromaDB
info "Starting ChromaDB..."
chroma run --path "$CHROMA_DB_PATH" > "$LOGS_DIR/chroma.log" 2>&1 &  # Run in background
CHROMA_PID=$!
success "ChromaDB started with PID $CHROMA_PID."

# Start FastAPI backend
info "Starting FastAPI backend..."
uvicorn backend:app --host 0.0.0.0 --port 5000 > "$LOGS_DIR/backend.log" 2>&1 &  # Run in background
BACKEND_PID=$!
success "FastAPI backend started with PID $BACKEND_PID."

# Wait for FastAPI to be ready (optional, can be skipped if you don't need to check status)
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

# Start Streamlit chatbot
info "Starting Streamlit chatbot..."
streamlit run "$CHATBOT_SCRIPT" --server.address $SERVER_IP --server.port 8502 > "$LOGS_DIR/streamlit.log" 2>&1 &  # Run in background
CHATBOT_PID=$!
success "Streamlit chatbot started at: http://$SERVER_IP:8502"

# No need to wait for processes anymore as they are running in the background
success "All services are running in the background."

