#!/bin/bash

# startup script for subscriber vm
# auto-installs dependencies and starts the subscriber

# check if already ran
if [ -f /var/log/startup_already_done ]; then
    echo "startup already ran, skipping installation"
    # just start the subscriber
    cd /app
    python3 subscriber.py &
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
gsutil cp gs://san_yan_bucket/subscriber/subscriber.py /app/

# install dependencies
python3 -m pip install --upgrade pip
python3 -m pip install google-cloud-pubsub google-cloud-storage --break-system-packages

# create lock file
touch /var/log/startup_already_done

# start subscriber
python3 subscriber.py