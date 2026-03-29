#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

if [ -f /var/log/startup_already_done ]; then
    echo "startup already ran, skipping installation"
    systemctl start cloud-sql-proxy
    cd /app
    nohup python3 server.py > /tmp/server.log 2>&1 &
    exit 0
fi

apt-get update
apt-get install -y python3 python3-pip

mkdir -p /app
cd /app

gsutil cp gs://san_yan_bucket/web-server/server.py /app/
gsutil cp gs://san_yan_bucket/web-server/requirements.txt /app/
gsutil cp gs://san_yan_bucket/scripts/setup_schema.py /app/

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt --break-system-packages

cd ~
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.2/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy
mv cloud-sql-proxy /usr/local/bin/

cat > /etc/systemd/system/cloud-sql-proxy.service << 'EOF'
[Unit]
Description=Cloud SQL Proxy
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloud-sql-proxy direct-electron-486319-t6:us-central1:hw5-db
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cloud-sql-proxy
systemctl start cloud-sql-proxy

sleep 15

cd /app
python3 setup_schema.py

touch /var/log/startup_already_done

nohup python3 server.py > /tmp/server.log 2>&1 &

sleep 5
echo "web server setup complete"