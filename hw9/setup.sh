#!/bin/bash

set -e

PROJECT_ID="direct-electron-486319-t6"
REGION="us-central1"
ZONE="us-central1-a"
SERVICE_ACCOUNT="file-service-account@${PROJECT_ID}.iam.gserviceaccount.com"
BUCKET_NAME="san_yan_bucket"
IMAGE="us-central1-docker.pkg.dev/${PROJECT_ID}/hw9-repo/web-server:v1"

echo "setting up hw9 infrastructure..."
echo "project: $PROJECT_ID"
echo ""

# ensure kubectl and gke auth plugin are installed
echo "installing kubectl and gke auth plugin..."
gcloud components install kubectl gke-gcloud-auth-plugin --quiet
echo ""

# add gcloud bin to PATH for this session
export PATH="$PATH:$(gcloud info --format='value(installation.sdk_root)')/bin"
echo "PATH updated: kubectl at $(which kubectl)"
echo ""

# enable required apis
echo "enabling apis..."
gcloud services enable container.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
echo ""

# create artifact registry repo
echo "creating artifact registry repo..."
gcloud artifacts repositories create hw9-repo \
  --repository-format=docker \
  --location=us-central1 \
  --project=$PROJECT_ID || echo "repo already exists"
echo ""

# configure docker auth
echo "configuring docker auth..."
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
echo ""

# build and push container image using cloud build (no local docker needed)
echo "building and pushing container image..."
gcloud builds submit --tag $IMAGE .
echo ""

# create gke cluster (e2-medium, try multiple zones in case of quota issues)
echo "creating gke cluster..."
CLUSTER_CREATED=false
for TRY_ZONE in us-central1-a us-central1-b us-central1-c us-east1-b; do
  echo "trying zone: $TRY_ZONE"
  if gcloud container clusters create hw9-cluster \
    --zone=$TRY_ZONE \
    --num-nodes=1 \
    --machine-type=e2-medium \
    --service-account=$SERVICE_ACCOUNT \
    --scopes=cloud-platform \
    --project=$PROJECT_ID 2>/dev/null; then
    ZONE=$TRY_ZONE
    CLUSTER_CREATED=true
    echo "cluster created in zone: $ZONE"
    break
  else
    echo "zone $TRY_ZONE failed, trying next..."
  fi
done

if [ "$CLUSTER_CREATED" = false ]; then
  echo "ERROR: could not create cluster in any zone. check quota."
  exit 1
fi
echo ""

# get cluster credentials
echo "getting cluster credentials..."
gcloud container clusters get-credentials hw9-cluster --zone=$ZONE --project=$PROJECT_ID
echo ""

# deploy to kubernetes
echo "deploying to kubernetes..."
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
echo ""

# wait for deployment
echo "waiting for deployment to be ready..."
kubectl rollout status deployment/web-server
echo ""

# get external ip (may take a minute)
echo "waiting for external ip..."
echo "run this to check: kubectl get service web-server-service"
echo ""

# create subscriber vm (same as hw4)
echo "creating subscriber vm..."
gcloud compute instances create subscriber-vm \
  --zone=$ZONE \
  --machine-type=e2-micro \
  --image-family=debian-11 \
  --image-project=debian-cloud \
  --service-account=$SERVICE_ACCOUNT \
  --scopes=cloud-platform \
  --project=$PROJECT_ID || echo "subscriber-vm already exists"
echo ""

# upload subscriber code to gcs
echo "uploading subscriber code to gcs..."
gsutil cp subscriber.py gs://${BUCKET_NAME}/subscriber/subscriber.py
echo ""

# create http client vm (e2-small, ubuntu 24.04 for glibc compatibility)
echo "creating http client vm..."
gcloud compute instances create http-client-vm \
  --zone=$ZONE \
  --machine-type=e2-small \
  --image-family=ubuntu-2404-lts-amd64 \
  --image-project=ubuntu-os-cloud \
  --service-account=$SERVICE_ACCOUNT \
  --scopes=cloud-platform \
  --project=$PROJECT_ID || echo "http-client-vm already exists"
echo ""

echo "============================================"
echo "setup complete!"
echo "============================================"
echo "get your external ip:"
echo "  kubectl get service web-server-service"
echo ""
echo "start subscriber (ssh into subscriber-vm):"
echo "  gcloud compute ssh subscriber-vm --zone=$ZONE"
echo "  gsutil cp gs://$BUCKET_NAME/subscriber/subscriber.py ."
echo "  pip3 install google-cloud-pubsub google-cloud-storage --break-system-packages"
echo "  python3 subscriber.py"
echo "============================================"