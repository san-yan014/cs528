from http.server import HTTPServer, BaseHTTPRequestHandler
from google.cloud import storage, pubsub_v1
import urllib.request
import json
import logging

FORBIDDEN = ['north korea', 'iran', 'cuba', 'myanmar', 'iraq', 'libya', 'sudan', 'zimbabwe', 'syria']
BUCKET_NAME = 'san_yan_bucket'
PROJECT_ID = 'direct-electron-486319-t6'
TOPIC_NAME = 'forbidden-requests'

def get_zone():
    try:
        r = urllib.request.Request(
            'http://metadata.google.internal/computeMetadata/v1/instance/zone',
            headers={'Metadata-Flavor': 'Google'}
        )
        with urllib.request.urlopen(r, timeout=2) as resp:
            return resp.read().decode().split('/')[-1]
    except Exception:
        return 'unknown'

ZONE = get_zone()

class Handler(BaseHTTPRequestHandler):

    def send(self, code, body=''):
        self.send_response(code)
        self.send_header('X-zone', ZONE)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        country = self.headers.get('X-country', '').lower().strip()
        if country in FORBIDDEN:
            try:
                publisher = pubsub_v1.PublisherClient()
                topic = publisher.topic_path(PROJECT_ID, TOPIC_NAME)
                msg = json.dumps({'country': country, 'file': self.path, 'ip': self.client_address[0]})
                publisher.publish(topic, msg.encode())
            except Exception as e:
                logging.error(f'pub/sub error: {e}')
            logging.critical(f'forbidden access from {country}: {self.path}')
            self.send(400, 'Permission Denied')
            return

        filepath = self.path.lstrip('/')
        try:
            client = storage.Client()
            bucket = client.bucket(BUCKET_NAME)
            blob = bucket.blob(filepath)
            if not blob.exists():
                logging.warning(f'file not found: {filepath}')
                self.send(404, 'Not Found')
                return
            content = blob.download_as_text()
            self.send_response(200)
            self.send_header('X-zone', ZONE)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(content.encode())
        except Exception as e:
            logging.error(f'error: {e}')
            self.send(500, 'Internal Server Error')

    def do_GET_methods(self):
        logging.warning(f'unsupported method: {self.command}')
        self.send(501, 'Not Implemented')

    # map all other methods to 501
    do_POST = do_PUT = do_DELETE = do_HEAD = do_OPTIONS = do_PATCH = do_GET_methods

    def log_message(self, format, *args):
        pass  # suppress default access logs

if __name__ == '__main__':
    server = HTTPServer(('', 80), Handler)
    print(f'starting server in zone: {ZONE}')
    server.serve_forever()