#!/bin/bash

set -e  # exit on error

# get project id dynamically
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
ZONE="us-central1-a"
SERVICE_ACCOUNT="file-service-account@${PROJECT_ID}.iam.gserviceaccount.com"
BUCKET_NAME="san_yan_bucket"

echo "setting up hw4 infrastructure..."
echo "project: $PROJECT_ID"
echo ""

# enable compute engine api
echo "enabling compute engine api..."
gcloud services enable compute.googleapis.com
echo ""

# upload code to gcs
echo "uploading code to gcs..."
gsutil cp server.py gs://${BUCKET_NAME}/web-server/
gsutil cp requirements.txt gs://${BUCKET_NAME}/web-server/
gsutil cp subscriber.py gs://${BUCKET_NAME}/subscriber/
echo ""

# reserve static ip
echo "reserving static ip..."
gcloud compute addresses create web-server-ip --region=$REGION || echo "static ip already exists"
STATIC_IP=$(gcloud compute addresses describe web-server-ip --region=$REGION --format='value(address)')
echo "static ip: $STATIC_IP"
echo ""

# create firewall rule
echo "creating firewall rule..."
gcloud compute firewall-rules create allow-http \
  --allow tcp:80 \
  --target-tags http-server \
  --source-ranges 0.0.0.0/0 \
  --description "allow http traffic to web server" || echo "firewall rule already exists"
echo ""

# create vm 1: web server
echo "creating web server vm..."
gcloud compute instances create web-server \
  --zone=$ZONE \
  --machine-type=e2-micro \
  --service-account=$SERVICE_ACCOUNT \
  --scopes=cloud-platform \
  --address=$STATIC_IP \
  --metadata-from-file=startup-script=startup-web-server.sh \
  --tags=http-server
echo ""

# create vm 2: http client
echo "creating http client vm..."
gcloud compute instances create http-client-vm \
  --zone=$ZONE \
  --machine-type=e2-small \
  --service-account=$SERVICE_ACCOUNT \
  --scopes=cloud-platform
echo ""

# create vm 3: subscriber
echo "creating subscriber vm..."
gcloud compute instances create subscriber-vm \
  --zone=$ZONE \
  --machine-type=e2-micro \
  --service-account=$SERVICE_ACCOUNT \
  --scopes=cloud-platform \
  --metadata-from-file=startup-script=startup-subscriber.sh
echo ""

echo "============================================"
echo "setup complete!"
echo "============================================"
echo "web server: http://$STATIC_IP"
echo "test: curl http://$STATIC_IP/graph_data/0.html"
echo ""
echo "vms created:"
gcloud compute instances list
echo "============================================"