#!/bin/bash

# startup script for web server vm
# auto-installs dependencies and starts the web server

# check if already ran
if [ -f /var/log/startup_already_done ]; then
    echo "startup already ran, skipping installation"
    # just start the server
    cd /app
    python3 server.py &
    exit 0
fi

# update system
apt-get update

# install python and pip
apt-get install -y python3 python3-pip

# create app directory
mkdir -p /app
cd /app

# download code from gcs
gsutil cp gs://san_yan_bucket/web-server/server.py /app/
gsutil cp gs://san_yan_bucket/web-server/requirements.txt /app/

# install dependencies
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt --break-system-packages

# create lock file
touch /var/log/startup_already_done

# start web server on port 80
python3 server.py