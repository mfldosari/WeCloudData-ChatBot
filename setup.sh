#!/bin/bash

# Color functions
info() { echo -e "\033[34m$1\033[0m"; }
success() { echo -e "\033[32m$1\033[0m"; }
error() { echo -e "\033[31m$1\033[0m"; }

# Inform the user about prerequisites
info "Setting up the environment..."
info "Ensure you have created a .env file in the repository root with the following settings:"
info "  - DATABASE_CRED: Your database connection credentials (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)"
info "  - OPENAI_API_KEY: Your OpenAI API key."
echo ""

# Get the current directory (expected to be the repo's root)
CURRENT_DIR=$(pwd)
info "Current directory: $CURRENT_DIR"

# Check if .env file exists in the current directory
if [ ! -f "$CURRENT_DIR/.env" ]; then
  error "Error: .env file not found in $CURRENT_DIR. Please create a .env file with the necessary environment variables."
  exit 1
fi

# Load environment variables from .env file
set -a
source "$CURRENT_DIR/.env"
set +a

# Verify that the required environment variables are set
REQUIRED_VARS=("OPENAI_API_KEY" "DB_NAME" "DB_USER" "DB_PASSWORD" "DB_HOST" "DB_PORT")

for VAR in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!VAR}" ]; then
    error "Error: $VAR is not set in the .env file. Please add it and try again."
    exit 1
  fi
done

success ".env file loaded successfully."

# Define paths
REQUIREMENTS_FILE="$CURRENT_DIR/requirements.txt"


# Check if the requirements file exists
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    error "Error: Requirements file not found at $REQUIREMENTS_FILE"
    exit 1
fi

# Install dependencies
info "Installing dependencies from $REQUIREMENTS_FILE..."
pip install -r "$REQUIREMENTS_FILE"

# Verify that all dependencies are installed
info "Verifying installed packages..."
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
    error "The following requirements are missing:"
    error "$MISSING_REQS"
    exit 1
else
    success "All dependencies are installed."
fi

success "Setup completed successfully!"

