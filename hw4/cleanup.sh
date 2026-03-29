#!/bin/bash

set -e  # exit on error

REGION="us-central1"
ZONE="us-central1-a"

echo "cleaning up hw4 infrastructure..."
echo ""

# delete vms
echo "deleting vms..."
gcloud compute instances delete web-server --zone=$ZONE --quiet || echo "web-server already deleted"
gcloud compute instances delete http-client-vm --zone=$ZONE --quiet || echo "http-client-vm already deleted"
gcloud compute instances delete subscriber-vm --zone=$ZONE --quiet || echo "subscriber-vm already deleted"
echo ""

# release static ip
echo "releasing static ip..."
gcloud compute addresses delete web-server-ip --region=$REGION --quiet || echo "static ip already deleted"
echo ""

# delete firewall rule
echo "deleting firewall rule..."
gcloud compute firewall-rules delete allow-http --quiet || echo "firewall rule already deleted"
echo ""

# delete code from gcs
echo "deleting code from gcs..."
gsutil rm gs://san_yan_bucket/web-server/server.py || true
gsutil rm gs://san_yan_bucket/web-server/requirements.txt || true
gsutil rm gs://san_yan_bucket/subscriber/subscriber.py || true
echo ""

echo "============================================"
echo "cleanup complete!"
echo "============================================"
echo "note: service account, pub/sub, and bucket retained from hw3"
echo "============================================"