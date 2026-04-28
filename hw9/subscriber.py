from google.cloud import pubsub_v1, storage
from datetime import datetime
import json

# configuration
PROJECT_ID = 'direct-electron-486319-t6'
SUBSCRIPTION = 'forbidden-requests-sub'
BUCKET = 'san_yan_bucket'
LOG_FILE = 'forbidden-logs/log.txt'

def callback(message):
    # parse message
    data = json.loads(message.data.decode('utf-8'))
    
    # create log entry
    timestamp = datetime.now().isoformat()
    log = f"[{timestamp}] country={data.get('country')}, file={data.get('file')}, ip={data.get('ip')}\n"
    
    # print to console
    print(log.strip())
    
    # append to gcs
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET)
        blob = bucket.blob(LOG_FILE)
        
        # get existing content
        if blob.exists():
            existing = blob.download_as_text()
        else:
            existing = ""
        
        # append and upload
        blob.upload_from_string(existing + log)
        print(f"written to gs://{BUCKET}/{LOG_FILE}")
        
    except Exception as e:
        print(f'gcs error: {e}')
    
    message.ack()

def main():
    # note: no need to set credentials on vm - uses service account identity
    print(f'listening for messages on {SUBSCRIPTION}...\n')
    
    # subscribe
    subscriber = pubsub_v1.SubscriberClient()
    path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION)
    future = subscriber.subscribe(path, callback=callback)
    
    try:
        future.result()
    except KeyboardInterrupt:
        future.cancel()
        print('\nstopped')

if __name__ == '__main__':
    main()