#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y python3 python3-pip

mkdir -p /app
cd /app

gsutil cp gs://san_yan_bucket/ml-models/model_ip_to_country.py /app/
gsutil cp gs://san_yan_bucket/ml-models/model_income_prediction.py /app/
gsutil cp gs://san_yan_bucket/ml-models/migrate_to_3nf.py /app/

pip3 install scikit-learn numpy mysql-connector-python --break-system-packages

curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.2/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy
mv cloud-sql-proxy /usr/local/bin/

nohup cloud-sql-proxy direct-electron-486319-t6:us-central1:hw5-db > /tmp/proxy.log 2>&1 &

echo "waiting for cloud sql proxy to start..."
sleep 30

python3 migrate_to_3nf.py

echo "running model 1: ip to country..."
python3 model_ip_to_country.py

echo "running model 2: income prediction..."
python3 model_income_prediction.py

gsutil cp model1_results.txt gs://san_yan_bucket/ml-models/
gsutil cp model2_results.txt gs://san_yan_bucket/ml-models/

echo "models complete" > /tmp/models_done.flag

echo "ml models execution complete"