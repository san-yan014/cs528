#!/bin/bash

set -e

PROJECT_ID="direct-electron-486319-t6"
REGION="us-central1"
ZONE="us-central1-a"
INSTANCE_NAME="hw5-db"

echo "cleaning up hw5 infrastructure..."
echo ""

echo "stopping cloud sql instance (not deleting)..."
gcloud sql instances patch $INSTANCE_NAME --activation-policy=NEVER --quiet 2>/dev/null || echo "database already stopped"
echo ""

echo "deleting vms..."
gcloud compute instances delete web-server --zone=$ZONE --quiet 2>/dev/null || echo "web-server already deleted"
gcloud compute instances delete http-client-vm --zone=$ZONE --quiet 2>/dev/null || echo "http-client-vm already deleted"
gcloud compute instances delete subscriber-vm --zone=$ZONE --quiet 2>/dev/null || echo "subscriber-vm already deleted"
echo ""

echo "releasing static ip..."
gcloud compute addresses delete web-server-ip --region=$REGION --quiet 2>/dev/null || echo "static ip already deleted"
echo ""

echo "deleting firewall rule..."
gcloud compute firewall-rules delete allow-http --quiet 2>/dev/null || echo "firewall rule already deleted"
echo ""

echo "============================================"
echo "cleanup complete!"
echo "============================================"
echo "note: database $INSTANCE_NAME is STOPPED (not deleted)"
echo ""
echo "to start database again:"
echo "  gcloud sql instances patch $INSTANCE_NAME --activation-policy=ALWAYS"
echo ""
echo "to delete database completely (if needed):"
echo "  gcloud sql instances delete $INSTANCE_NAME"
echo "============================================"