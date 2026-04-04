#!/bin/bash

set -e

PROJECT_ID="direct-electron-486319-t6"
ZONE="us-central1-a"
REGION="us-central1"
BUCKET="san_yan_bucket"
VM_NAME="ml-models-vm"
SERVICE_ACCOUNT="file-service-account@${PROJECT_ID}.iam.gserviceaccount.com"

echo "starting hw6 ml models automation..."
echo ""

echo "starting cloud sql database..."
gcloud sql instances patch hw5-db --activation-policy=ALWAYS --quiet
echo "waiting for database to be ready..."
sleep 60

echo ""
echo "creating ml models vm..."
gcloud compute instances create $VM_NAME --zone=$ZONE --machine-type=e2-medium --service-account=$SERVICE_ACCOUNT --scopes=cloud-platform --metadata-from-file=startup-script=startup-ml.sh

echo ""
echo "waiting for vm to start and run models (this takes 5-10 minutes)..."
sleep 300

echo ""
echo "checking if models completed..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="cat /tmp/models_done.flag" 2>/dev/null || echo "models still running, waiting..."

sleep 60

echo ""
echo "retrieving results from gcs..."
echo ""
echo "=== MODEL 1 RESULTS (IP → Country) ==="
gsutil cat gs://${BUCKET}/ml-models/model1_results.txt
echo ""
echo "=== MODEL 2 RESULTS (Income Prediction) ==="
gsutil cat gs://${BUCKET}/ml-models/model2_results.txt
echo ""

echo "stopping database..."
gcloud sql instances patch hw5-db --activation-policy=NEVER --quiet

echo ""
echo "deleting vm..."
gcloud compute instances delete $VM_NAME --zone=$ZONE --quiet

echo ""
echo "============================================"
echo "hw6 automation complete!"
echo "============================================"
echo "results stored in gs://${BUCKET}/ml-models/"
echo "============================================"