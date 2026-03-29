#!/bin/bash

set -e

PROJECT_ID="direct-electron-486319-t6"
REGION="us-central1"
ZONE="us-central1-a"
SERVICE_ACCOUNT="file-service-account@${PROJECT_ID}.iam.gserviceaccount.com"
BUCKET_NAME="san_yan_bucket"
DB_PASSWORD="hw5password123"
INSTANCE_NAME="hw5-db"

echo "setting up hw5 infrastructure..."
echo "project: $PROJECT_ID"
echo ""

gcloud services enable compute.googleapis.com
gcloud services enable sqladmin.googleapis.com

echo "checking if cloud sql instance exists..."
if gcloud sql instances describe $INSTANCE_NAME &>/dev/null; then
    echo "database instance exists, starting it..."
    gcloud sql instances patch $INSTANCE_NAME --activation-policy=ALWAYS --quiet
else
    echo "creating cloud sql instance (takes 5-10 minutes)..."
    gcloud sql instances create $INSTANCE_NAME --database-version=MYSQL_8_0 --tier=db-f1-micro --region=$REGION --root-password=$DB_PASSWORD --storage-type=HDD --storage-size=10GB
    
    echo "creating database..."
    gcloud sql databases create requests --instance=$INSTANCE_NAME
    
    echo "note: schema will be initialized by startup script on vm"
fi
echo ""

echo "granting service account cloud sql permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:${SERVICE_ACCOUNT}" --role="roles/cloudsql.client" 2>/dev/null || echo "permission already granted"
echo ""

echo "uploading code to gcs..."
gsutil cp server.py gs://${BUCKET_NAME}/web-server/
gsutil cp requirements.txt gs://${BUCKET_NAME}/web-server/
gsutil cp subscriber.py gs://${BUCKET_NAME}/subscriber/
gsutil cp setup_schema.py gs://${BUCKET_NAME}/scripts/
echo ""

echo "reserving static ip..."
gcloud compute addresses create web-server-ip --region=$REGION 2>/dev/null || echo "static ip already exists"
STATIC_IP=$(gcloud compute addresses describe web-server-ip --region=$REGION --format='value(address)')
echo "static ip: $STATIC_IP"
echo ""

echo "creating firewall rule..."
gcloud compute firewall-rules create allow-http --allow tcp:80 --target-tags http-server --source-ranges 0.0.0.0/0 --description "allow http traffic" 2>/dev/null || echo "firewall rule already exists"
echo ""

echo "creating web server vm..."
gcloud compute instances create web-server --zone=$ZONE --machine-type=e2-micro --service-account=$SERVICE_ACCOUNT --scopes=cloud-platform --address=$STATIC_IP --metadata-from-file=startup-script=startup.sh --tags=http-server
echo ""

echo "creating http client vm..."
gcloud compute instances create http-client-vm --zone=$ZONE --machine-type=e2-small --service-account=$SERVICE_ACCOUNT --scopes=cloud-platform --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud
echo ""

echo "creating subscriber vm..."
gcloud compute instances create subscriber-vm --zone=$ZONE --machine-type=e2-micro --service-account=$SERVICE_ACCOUNT --scopes=cloud-platform --metadata-from-file=startup-script=startup-subscriber.sh
echo ""

echo "============================================"
echo "setup complete!"
echo "============================================"
echo "web server: http://$STATIC_IP"
echo "database: $INSTANCE_NAME (running)"
echo ""
echo "wait 5-10 minutes for:"
echo "- vms to fully start"
echo "- startup scripts to complete"
echo "- database schema initialization"
echo ""
echo "verify with:"
echo "  gcloud compute instances list"
echo "  gcloud sql instances list"
echo "============================================"