from http.server import BaseHTTPRequestHandler, HTTPServer
from google.cloud import storage, pubsub_v1
import mysql.connector
import json
import time
from datetime import datetime

FORBIDDEN = ['north korea', 'iran', 'cuba', 'myanmar', 'iraq', 'libya', 'sudan', 'zimbabwe', 'syria']
BUCKET_NAME = 'san_yan_bucket'
PROJECT_ID = 'direct-electron-486319-t6'
TOPIC_NAME = 'forbidden-requests'

DB_HOST = '127.0.0.1'
DB_USER = 'root'
DB_PASSWORD = 'hw5password123'
DB_NAME = 'requests'

class FileServer(BaseHTTPRequestHandler):
    
    def extract_headers(self):
        start = time.perf_counter()
        country = self.headers.get('X-country', '').lower().strip()
        client_ip = self.headers.get('X-client-ip', self.client_address[0])
        gender = self.headers.get('X-gender', '')
        age = self.headers.get('X-age', 0)
        income = self.headers.get('X-income', 0)
        elapsed = time.perf_counter() - start
        print(f'header extraction: {elapsed:.6f}s')
        return country, client_ip, gender, age, income
    
    def read_from_gcs(self, filename):
        start = time.perf_counter()
        try:
            client = storage.Client()
            bucket = client.bucket(BUCKET_NAME)
            blob = bucket.blob(filename)
            if not blob.exists():
                elapsed = time.perf_counter() - start
                print(f'gcs read: {elapsed:.6f}s (not found)')
                return None
            content = blob.download_as_text()
            elapsed = time.perf_counter() - start
            print(f'gcs read: {elapsed:.6f}s')
            return content
        except Exception as e:
            elapsed = time.perf_counter() - start
            print(f'gcs read error: {elapsed:.6f}s - {e}')
            return None
    
    def send_http_response(self, status_code, content):
        start = time.perf_counter()
        self.send_response(status_code)
        if status_code == 200:
            self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(content if isinstance(content, bytes) else content.encode('utf-8'))
        elapsed = time.perf_counter() - start
        print(f'send response: {elapsed:.6f}s')
    
    def insert_success_to_db(self, country, client_ip, gender, age, income, is_banned, requested_file):
        start = time.perf_counter()
        try:
            def parse_numeric(value):
                if not value:
                    return 0
                value_str = str(value).strip().lower()
                
                multiplier = 1000 if 'k' in value_str else 1
                value_str = value_str.replace('k', '').replace('+', '')
                
                if '-' in value_str and value_str[0].isdigit():
                    base = int(value_str.split('-')[0])
                else:
                    try:
                        base = int(float(value_str))
                    except:
                        return 0
                
                return base * multiplier
                        
            age_val = parse_numeric(age)
            income_val = parse_numeric(income)
            
            conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO successful_requests 
                (country, client_ip, gender, age, income, is_banned, time_of_day, requested_file)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (country, client_ip, gender, age_val, income_val, is_banned, datetime.now(), requested_file))
            conn.commit()
            cursor.close()
            conn.close()
            elapsed = time.perf_counter() - start
            print(f'db insert (success): {elapsed:.6f}s')
        except Exception as e:
            elapsed = time.perf_counter() - start
            print(f'db insert error: {elapsed:.6f}s - {e}')
    
    def insert_failure_to_db(self, requested_file, error_code):
        start = time.perf_counter()
        try:
            conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO failed_requests (requested_file, error_code)
                VALUES (%s, %s)
            """, (requested_file, error_code))
            conn.commit()
            cursor.close()
            conn.close()
            elapsed = time.perf_counter() - start
            print(f'db insert (failure): {elapsed:.6f}s')
        except Exception as e:
            elapsed = time.perf_counter() - start
            print(f'db insert error: {elapsed:.6f}s - {e}')
    
    def do_GET(self):
        country, client_ip, gender, age, income = self.extract_headers()
        
        if country in FORBIDDEN:
            try:
                publisher = pubsub_v1.PublisherClient()
                topic = publisher.topic_path(PROJECT_ID, TOPIC_NAME)
                message = json.dumps({'country': country, 'file': self.path, 'ip': client_ip})
                publisher.publish(topic, message.encode('utf-8'))
            except Exception as e:
                print(f'pub/sub error: {e}')
            
            print(json.dumps({'severity': 'CRITICAL', 'message': f'forbidden access from {country}', 'file': self.path}))
            self.insert_failure_to_db(self.path, 400)
            self.send_http_response(400, b'Permission Denied')
            return
        
        filepath = self.path.strip('/')
        filename = filepath.replace('.html', '.json')
        parts = filename.split('/')
        if len(parts) == 2:
            filename = f"{parts[0]}/page_{parts[1]}"
        
        content = self.read_from_gcs(filename)
        
        if content is None:
            print(json.dumps({'severity': 'WARNING', 'message': f'file not found: {filename}'}))
            self.insert_failure_to_db(self.path, 404)
            self.send_http_response(404, b'Not Found')
            return
        
        is_banned = country in FORBIDDEN
        self.insert_success_to_db(country, client_ip, gender, age, income, is_banned, self.path)
        self.send_http_response(200, content)
    
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
        self.insert_failure_to_db(self.path, 501)
        self.send_http_response(501, b'Not Implemented')
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 80), FileServer)
    server.request_queue_size = 10
    
    print('starting web server on port 80...')
    print(f'bucket: {BUCKET_NAME}')
    print(f'project: {PROJECT_ID}')
    print(f'database: {DB_NAME}@{DB_HOST}')
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nstopping server...')
        server.shutdown()