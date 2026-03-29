from google.cloud import storage, pubsub_v1
import json
import functions_framework


# defining the forbidden countries 
FORBIDDEN = ['north korea', 'iran', 'cuba', 'myanmar', 'iraq', 'libya', 'sudan', 'zimbabwe', 'syria']

# decorative function 
@functions_framework.http   # handles http requests 
def serve_file(request): 
    # enabling only "GET" requests
    if request.method != 'GET': 
        print(json.dumps({'severity': 'ERROR', 'message': f'unsupported method: {request.method}'}))
        return ('Not Implemented', 501)
    
    # check if it is from a forbidden country 
    country = request.headers.get('X-country', '').lower().strip()

    if country in FORBIDDEN:
            # send message to pub/sub
            try:
                publisher = pubsub_v1.PublisherClient()
                topic = publisher.topic_path('direct-electron-486319-t6', 'forbidden-requests')
                message = json.dumps({
                    'country': country,
                    'file': request.path,
                    'ip': request.remote_addr
                })
                publisher.publish(topic, message.encode('utf-8'))
            except Exception as e:
                print(f'pub/sub error: {e}')
            
            print(json.dumps({'severity': 'WARNING', 'message': f'forbidden access from {country}'}))
            return ('Permission Denied', 400)
    
    # get filename from query parameter or path
    filename = request.args.get('file')
    if not filename:
        # try to get from path (for professor's client)
        path = request.path.strip('/')
        
        # remove "serve_file/" prefix if present
        if path.startswith('serve_file/'):
            path = path.replace('serve_file/', '', 1)
        
        if path:
            # convert .html to .json and add page_ prefix
            filename = path.replace('.html', '.json')
            # add "page_" prefix to the number
            parts = filename.split('/')
            if len(parts) == 2:
                filename = f"{parts[0]}/page_{parts[1]}"
        else:
            return ('file parameter required', 400)
    
    # read file from gcs
    try:
        client = storage.Client()
        bucket = client.bucket('san_yan_bucket')
        blob = bucket.blob(filename)
        
        if not blob.exists():
            print(json.dumps({'severity': 'ERROR', 'message': f'file not found: {filename}'}))
            return ('Not Found', 404)
        
        content = blob.download_as_text()
        return (content, 200, {'Content-Type': 'application/json'})
        
    except Exception as e:
        print(f'error: {e}')
        return ('Internal Server Error', 500)