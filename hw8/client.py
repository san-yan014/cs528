import requests
import time
import random
import argparse

def run_client(host, num_files, interval=1.0):
    print(f"Sending requests to {host} every {interval}s")
    print(f"{'Time':>8} | {'Status':>6} | {'Zone':>20} | File")
    print("-" * 65)

    for i in range(num_files):
        file_id = random.randint(0, 19999)
        url = f"http://{host}/graph_data/page_{file_id}.json"
        try:
            resp = requests.get(url, timeout=5)
            zone = resp.headers.get('X-zone', 'unknown')
            print(f"{i:>8} | {resp.status_code:>6} | {zone:>20} | page_{file_id}.json")
        except requests.exceptions.ConnectionError:
            print(f"{i:>8} | {'ERROR':>6} | {'connection failed':>20} |")
        except requests.exceptions.Timeout:
            print(f"{i:>8} | {'TIMEOUT':>6} | {'no response':>20} |")
        except Exception as e:
            print(f"{i:>8} | {'ERROR':>6} | {str(e)[:20]:>20} |")
        time.sleep(interval)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', required=True, help='Load balancer IP or hostname')
    parser.add_argument('--n', type=int, default=200, help='Number of requests')
    parser.add_argument('--interval', type=float, default=1.0, help='Seconds between requests')
    args = parser.parse_args()
    run_client(args.host, args.n, args.interval)