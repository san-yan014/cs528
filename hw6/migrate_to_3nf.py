import mysql.connector
import sys

DB_HOST = '127.0.0.1'
DB_USER = 'root'
DB_PASSWORD = 'hw5password123'
DB_NAME = 'requests'

def migrate_to_3nf():
    try:
        conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        cursor = conn.cursor()
        
        print("creating normalized schema...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_country_mapping (
                ip_id INT AUTO_INCREMENT PRIMARY KEY,
                client_ip VARCHAR(50) UNIQUE NOT NULL,
                country VARCHAR(100)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests_normalized (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip_id INT,
                gender VARCHAR(20),
                age INT,
                income INT,
                time_of_day DATETIME,
                requested_file VARCHAR(255),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ip_id) REFERENCES ip_country_mapping(ip_id)
            )
        """)
        
        print("migrating data to ip_country_mapping...")
        cursor.execute("""
            INSERT IGNORE INTO ip_country_mapping (client_ip, country)
            SELECT DISTINCT client_ip, country FROM successful_requests
        """)
        
        print("migrating data to requests_normalized...")
        cursor.execute("""
            INSERT INTO requests_normalized (ip_id, gender, age, income, time_of_day, requested_file, timestamp)
            SELECT m.ip_id, s.gender, s.age, s.income, s.time_of_day, s.requested_file, s.timestamp
            FROM successful_requests s
            JOIN ip_country_mapping m ON s.client_ip = m.client_ip
        """)
        
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM ip_country_mapping")
        ip_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM requests_normalized")
        req_count = cursor.fetchone()[0]
        
        print(f"migration complete!")
        print(f"ip_country_mapping: {ip_count} unique IPs")
        print(f"requests_normalized: {req_count} requests")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    migrate_to_3nf()
