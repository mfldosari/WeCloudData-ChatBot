#!/bin/bash
set -e

date
echo "Updating applications on VM..."

APP_DIR="/home/azureuser/WeCloudData-ChatBot"
GIT_REPO="github.com/mfldosari/WeCloudData-ChatBot.git"
BRANCH="main"

# Update code
if [ -d "$APP_DIR" ]; then
    sudo -u azureuser bash -c "cd $APP_DIR && git pull origin $BRANCH"
else
    sudo -u azureuser git clone -b $BRANCH "https://$GITHUB_TOKEN@$GIT_REPO" "$APP_DIR"
fi
source /home/azureuser/env/bin/activate
# Install dependencies
sudo -u azureuser /home/azureuser/env/bin/pip install --upgrade pip
sudo -u azureuser /home/azureuser/env/bin/pip install -r "$APP_DIR/requirements.txt"

# Restart the service
sudo systemctl restart uvicorn.service
sudo systemctl restart streamlit.service
echo "Applications update completed!"

