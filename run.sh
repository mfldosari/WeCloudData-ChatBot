#!/bin/bash

# Color functions
info() { echo -e "\033[34m$1\033[0m"; }  # Blue
success() { echo -e "\033[32m$1\033[0m"; }  # Green
error() { echo -e "\033[31m$1\033[0m"; }  # Red

# Get the current directory (expected to be the repo's root)
CURRENT_DIR=$(pwd)
LOGS_DIR="$CURRENT_DIR/logs"

# Ensure logs directory exists
mkdir -p "$LOGS_DIR"
info "Logs will be stored in: $LOGS_DIR"

# Define paths
CHROMA_DB_PATH="$CURRENT_DIR/chromadb"
CHATBOT_SCRIPT="$CURRENT_DIR/chatbot.py"
# Get the server's IP address dynamically
SERVER_IP=$(hostname -I | awk '{print $1}')

# Start ChromaDB
info "Starting ChromaDB..."
chroma run --path "$CHROMA_DB_PATH" > "$LOGS_DIR/chroma.log" 2>&1 &
CHROMA_PID=$!
success "ChromaDB started with PID $CHROMA_PID. Logs: $LOGS_DIR/chroma.log"

echo "================================================="
success "Chrmoa is up and running!"
success "Access Chrmoa at: http://127.0.0.1:8000/docs"
echo "================================================="

# Start FastAPI backend with Uvicorn
info "Starting FastAPI backend..."
uvicorn backend:app --host 0.0.0.0 --port 5000 > "$LOGS_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
success "FastAPI backend started with PID $BACKEND_PID. Logs: $LOGS_DIR/backend.log"

# Wait until FastAPI is ready (check port 5000) with timeout
info "Waiting for FastAPI to start..."
TIMEOUT=60  # seconds
SECONDS_WAITED=0
while ! nc -z 127.0.0.1 5000; do
  sleep 1
  SECONDS_WAITED=$((SECONDS_WAITED+1))
  if [ $SECONDS_WAITED -ge $TIMEOUT ]; then
      error "Error: FastAPI backend did not start within $TIMEOUT seconds. Check logs in $LOGS_DIR/backend.log"
      exit 1
  fi
  info "Waiting for FastAPI..."
done


echo "================================================="
success "FastAPI is up and running!"
success "Access FastAPI at: http://$SERVER_IP:5000/docs"
echo "================================================="
# Start Streamlit chatbot
info "Starting Streamlit chatbot..."
streamlit run "$CHATBOT_SCRIPT" --server.address $SERVER_IP --server.port 8502 > "$LOGS_DIR/streamlit.log" 2>&1 &
CHATBOT_PID=$!
echo "================================================="
success "Streamlit chatbot started with PID $CHATBOT_PID. Logs: $LOGS_DIR/streamlit.log"
success "Access Streamlit at: http://$SERVER_IP:8502"
echo "================================================="

# Wait for processes to complete
wait $CHROMA_PID $BACKEND_PID $CHATBOT_PID

