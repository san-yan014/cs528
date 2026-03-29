from http.server import BaseHTTPRequestHandler, HTTPServer
from google.cloud import storage, pubsub_v1
import json

# configuration
FORBIDDEN = ['north korea', 'iran', 'cuba', 'myanmar', 'iraq', 'libya', 'sudan', 'zimbabwe', 'syria']
BUCKET_NAME = 'san_yan_bucket'
PROJECT_ID = 'direct-electron-486319-t6'
TOPIC_NAME = 'forbidden-requests'

class FileServer(BaseHTTPRequestHandler):
    
    def do_GET(self):
        # check country header
        country = self.headers.get('X-country', '').lower().strip()
        
        if country in FORBIDDEN:
            # publish to pub/sub
            try:
                publisher = pubsub_v1.PublisherClient()
                topic = publisher.topic_path(PROJECT_ID, TOPIC_NAME)
                message = json.dumps({
                    'country': country,
                    'file': self.path,
                    'ip': self.client_address[0]
                })
                publisher.publish(topic, message.encode('utf-8'))
            except Exception as e:
                print(f'pub/sub error: {e}')
            
            # log critical error
            print(json.dumps({'severity': 'CRITICAL', 'message': f'forbidden access from {country}', 'file': self.path}))
            
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Permission Denied')
            return
        
        # get filename from path
        filepath = self.path.strip('/')
        
        # convert .html to .json and add page_ prefix
        filename = filepath.replace('.html', '.json')
        parts = filename.split('/')
        if len(parts) == 2:
            filename = f"{parts[0]}/page_{parts[1]}"
        
        # read file from gcs
        try:
            client = storage.Client()
            bucket = client.bucket(BUCKET_NAME)
            blob = bucket.blob(filename)
            
            if not blob.exists():
                print(json.dumps({'severity': 'WARNING', 'message': f'file not found: {filename}'}))
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Not Found')
                return
            
            content = blob.download_as_text()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            
        except Exception as e:
            print(f'error: {e}')
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Internal Server Error')
    
    def do_POST(self):
        self._unsupported_method()
    
    def do_PUT(self):
        self._unsupported_method()
    
    def do_DELETE(self):
        self._unsupported_method()
    
    def do_HEAD(self):
        self._unsupported_method()
    
    def do_OPTIONS(self):
        self._unsupported_method()
    
    def do_PATCH(self):
        self._unsupported_method()
    
    def do_TRACE(self):
        self._unsupported_method()
    
    def do_CONNECT(self):
        self._unsupported_method()
    
    def _unsupported_method(self):
        print(json.dumps({'severity': 'WARNING', 'message': f'unsupported method: {self.command}'}))
        self.send_response(501)
        self.end_headers()
        self.wfile.write(b'Not Implemented')
    
    def log_message(self, format, *args):
        # suppress default request logging
        pass

if __name__ == '__main__':
    # configure server with request queue size for concurrent requests
    server = HTTPServer(('0.0.0.0', 80), FileServer)
    server.request_queue_size = 10  # handle up to 10 queued requests
    
    print('starting web server on port 80...')
    print(f'bucket: {BUCKET_NAME}')
    print(f'project: {PROJECT_ID}')
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nstopping server...')
        server.shutdown()