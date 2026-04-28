#!/bin/bash

set -e

PROJECT_ID="direct-electron-486319-t6"
REGION="us-central1"
ZONE="us-central1-a"

echo "cleaning up hw9 infrastructure..."
echo ""

# delete kubernetes resources
echo "deleting kubernetes resources..."
kubectl delete service web-server-service || echo "service already deleted"
kubectl delete deployment web-server || echo "deployment already deleted"
echo ""

# delete gke cluster
echo "deleting gke cluster..."
gcloud container clusters delete hw9-cluster --zone=$ZONE --quiet || echo "cluster already deleted"
echo ""

# delete artifact registry image
echo "deleting container image..."
gcloud artifacts repositories delete hw9-repo --location=us-central1 --quiet || echo "repo already deleted"
echo ""

# delete vms
echo "deleting vms..."
gcloud compute instances delete subscriber-vm --zone=$ZONE --quiet || echo "subscriber-vm already deleted"
gcloud compute instances delete http-client-vm --zone=$ZONE --quiet || echo "http-client-vm already deleted"
echo ""

echo "============================================"
echo "cleanup complete!"
echo "============================================"
echo "note: bucket, pub/sub, and service account retained"
echo "============================================"