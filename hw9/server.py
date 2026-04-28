from http.server import BaseHTTPRequestHandler, HTTPServer
from google.cloud import storage, pubsub_v1
import json

# configuration
FORBIDDEN = ['north korea', 'iran', 'cuba', 'myanmar', 'iraq', 'libya', 'sudan', 'zimbabwe', 'syria']
BUCKET_NAME = 'san_yan_bucket'
PROJECT_ID = 'direct-electron-486319-t6'
TOPIC_NAME = 'forbidden-requests'

# initialize clients once at startup
storage_client = storage.Client()
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)

class FileServer(BaseHTTPRequestHandler):

    def do_GET(self):
        country = self.headers.get('X-country', '').lower().strip()

        if country in FORBIDDEN:
            try:
                message = json.dumps({
                    'country': country,
                    'file': self.path,
                    'ip': self.client_address[0]
                })
                publisher.publish(topic_path, message.encode('utf-8'))
            except Exception as e:
                print(json.dumps({'severity': 'ERROR', 'message': f'pub/sub error: {e}'}), flush=True)

            print(json.dumps({'severity': 'CRITICAL', 'message': f'forbidden access from {country}', 'file': self.path}), flush=True)
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Permission Denied')
            return

        filepath = self.path.strip('/')

        # convert .html to .json
        filename = filepath.replace('.html', '.json')

        # strip bucket name prefix if http client includes it
        # e.g. san_yan_bucket/graph_data/14926.json -> graph_data/14926.json
        if filename.startswith(BUCKET_NAME + '/'):
            filename = filename[len(BUCKET_NAME) + 1:]

        # add page_ prefix to the final filename component if not already present
        parts = filename.split('/')
        if len(parts) >= 2 and not parts[-1].startswith('page_'):
            parts[-1] = 'page_' + parts[-1]
            filename = '/'.join(parts)

        try:
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob(filename)

            if not blob.exists():
                print(json.dumps({'severity': 'WARNING', 'message': f'file not found: {filename}'}), flush=True)
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
            print(json.dumps({'severity': 'ERROR', 'message': f'gcs error: {e}'}), flush=True)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Internal Server Error')

    def _unsupported_method(self):
        print(json.dumps({'severity': 'WARNING', 'message': f'unsupported method: {self.command}', 'path': self.path}), flush=True)
        self.send_response(501)
        self.end_headers()
        self.wfile.write(b'Not Implemented')

    def do_POST(self): self._unsupported_method()
    def do_PUT(self): self._unsupported_method()
    def do_DELETE(self): self._unsupported_method()
    def do_HEAD(self): self._unsupported_method()
    def do_OPTIONS(self): self._unsupported_method()
    def do_PATCH(self): self._unsupported_method()
    def do_TRACE(self): self._unsupported_method()
    def do_CONNECT(self): self._unsupported_method()

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 80), FileServer)
    server.request_queue_size = 10
    print('starting web server on port 80...', flush=True)
    print(f'bucket: {BUCKET_NAME}', flush=True)
    print(f'project: {PROJECT_ID}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nstopping server...', flush=True)
        server.shutdown()