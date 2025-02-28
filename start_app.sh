#!/bin/bash

# Inform the user about prerequisites
echo "Before running the application, ensure you have created a .env file in the repository root with the following required settings:"
echo "  - DATABASE_CRED: Your database connection creds e.g:" 
echo " 1. DB_NAME"
echo " 2. DB_USER"
echo " 3. DB_PASSWORD"
echo " 4. DB_HOST"
echo " 5. DB_PORT"
echo "  - OPENAI_API_KEY: Your OpenAI API key."
echo ""

# Get the current directory (expected to be the repo's root)
CURRENT_DIR=$(pwd)
echo "Current directory: $CURRENT_DIR"

# Check if .env file exists in the current directory
if [ ! -f "$CURRENT_DIR/.env" ]; then
  echo "Error: .env file not found in $CURRENT_DIR. Please create a .env file with the necessary environment variables."
  exit 1
fi

# Load environment variables from .env file
set -a
source "$CURRENT_DIR/.env"
set +a

# Verify that the required environment variables are set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY is not set in the .env file. Please set your OpenAI API key."
    exit 1
fi

if [ -z "DB_NAME" ]; then
    echo "Error: DATABASE_URL is not set in the .env file. Please set your database connection details."
    exit 1
fi

# Define paths based on the current directory (repo root)
REPO_DIR="$CURRENT_DIR"
CHATBOT_SCRIPT="$REPO_DIR/chatbot_streamlit.py"
CHROMA_DB_PATH="$CURRENT_DIR/chromadb"  # Directory for ChromaDB data
REQUIREMENTS_FILE="$REPO_DIR/requirments.txt"

# Check if running inside a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
  echo "Warning: It appears that you are not using a virtual environment."
  echo "Please activate your virtual environment before running this script."
  exit 1
else
  echo "Virtual environment is active: $VIRTUAL_ENV"
fi

# Check if the requirements file exists
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "Error: Requirements file not found at $REQUIREMENTS_FILE"
    exit 1
fi

# Install requirements
echo "Installing dependencies from $REQUIREMENTS_FILE..."
pip install -r "$REQUIREMENTS_FILE"

# Verify that all dependencies are installed
echo "Verifying installed packages..."
MISSING_REQS=$(python - <<EOF
import pkg_resources
with open("$REQUIREMENTS_FILE") as f:
    required = [line.strip() for line in f if line.strip() and not line.startswith("#")]
installed = {pkg.key for pkg in pkg_resources.working_set}
missing = [req for req in required if req.split("==")[0].lower() not in installed]
if missing:
    print("\n".join(missing))
EOF
)

if [ -n "$MISSING_REQS" ]; then
    echo "The following requirements are missing:"
    echo "$MISSING_REQS"
    exit 1
else
    echo "All dependencies are installed."
fi

# Start ChromaDB
echo "Starting ChromaDB..."
chroma run --path "$CHROMA_DB_PATH" > /dev/null 2>&1 &
CHROMA_PID=$!
echo "ChromaDB started with PID $CHROMA_PID"

# Start FastAPI backend with Uvicorn
echo "Starting FastAPI backend..."
uvicorn chatbot_fastapi:app --host 0.0.0.0 --port 5000 > /dev/null 2>&1 &
BACKEND_PID=$!
echo "FastAPI backend started with PID $BACKEND_PID"

# Wait until FastAPI is ready (check port 5000) with timeout
echo "Waiting for FastAPI to start..."
TIMEOUT=60  # seconds
SECONDS_WAITED=0
while ! nc -z 127.0.0.1 5000; do
  sleep 1
  SECONDS_WAITED=$((SECONDS_WAITED+1))
  if [ $SECONDS_WAITED -ge $TIMEOUT ]; then
      echo "Error: FastAPI backend did not start within $TIMEOUT seconds. Exiting."
      exit 1
  fi
  echo "Waiting for FastAPI..."
done
echo "FastAPI is up and running!"

# Start Streamlit chatbot
echo "Starting Streamlit chatbot..."
streamlit run "$CHATBOT_SCRIPT" > /dev/null 2>&1 &
CHATBOT_PID=$!
echo "Streamlit chatbot started with PID $CHATBOT_PID"

# Wait for processes to complete
wait $CHROMA_PID $BACKEND_PID $CHATBOT_PID

