import mysql.connector
import sys
import time

DB_HOST = '127.0.0.1'
DB_USER = 'root'
DB_PASSWORD = 'hw5password123'
DB_NAME = 'requests'

def wait_for_proxy():
    max_attempts = 30
    for i in range(max_attempts):
        try:
            conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
            conn.close()
            print("cloud sql proxy ready")
            return True
        except:
            print(f"waiting for proxy... attempt {i+1}/{max_attempts}")
            time.sleep(2)
    return False

def create_schema():
    try:
        if not wait_for_proxy():
            print("error: could not connect to cloud sql proxy")
            sys.exit(1)
        
        conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS successful_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                country VARCHAR(100),
                client_ip VARCHAR(50),
                gender VARCHAR(20),
                age INT,
                income INT,
                is_banned BOOLEAN,
                time_of_day DATETIME,
                requested_file VARCHAR(255),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS failed_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                requested_file VARCHAR(255),
                error_code INT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("schema created successfully")
        print("tables: successful_requests, failed_requests")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"error creating schema: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_schema()