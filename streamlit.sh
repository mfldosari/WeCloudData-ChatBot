#!/bin/bash
 
 # Color functions
info() { echo -e "\033[34m$1\033[0m"; }  # Blue
success() { echo -e "\033[32m$1\033[0m"; }  # Green
 
source /home/azureuser/env/bin/activate
 
CURRENT_DIR=$(pwd)
LOGS_DIR="$CURRENT_DIR/logs"
CHATBOT_SCRIPT="$CURRENT_DIR/chatbot.py"
 
 
 # Ensure logs directory exists
mkdir -p "$LOGS_DIR"
info "Logs will be stored in: $LOGS_DIR"
 
 
 # Start Streamlit chatbot
info "Starting Streamlit chatbot..."
streamlit run "$CHATBOT_SCRIPT" --server.address 0.0.0.0 --server.port 8501 > "$LOGS_DIR/streamlit.log" 2>&1 &  # Run in background
CHATBOT_PID=$!
success "Streamlit chatbot started at: http://:8501"
 
 # Prevent the script from exiting
tail -f /dev/null
