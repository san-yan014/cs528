import requests
import random

# update this after deploying cloud function
URL = 'https://us-central1-direct-electron-486319-t6.cloudfunctions.net/serve_file'

# countries
ALLOWED = ['usa', 'canada', 'uk', 'france', 'germany', 'japan']
FORBIDDEN = ['iran', 'cuba', 'myanmar', 'north korea', 'iraq', 'libya', 'sudan', 'zimbabwe', 'syria']

# sample files
FILES = [
    'graph_data/page_0.json',
    'graph_data/page_1.json',
    'graph_data/page_100.json',
    'graph_data/page_1000.json',
    'graph_data/page_10000.json',
]

def make_request(file_path, country):
    headers = {'X-country': country}
    params = {'file': file_path}
    try:
        response = requests.get(URL, params=params, headers=headers, timeout=10)
        return response.status_code
    except:
        return Nonetest

# counters
results = {'200': 0, '400': 0, '404': 0, 'error': 0}

print(f'testing {URL}\n')

# make 100 requests
for i in range(100):
    file_path = random.choice(FILES)
    country = random.choice(ALLOWED + FORBIDDEN)
    
    status = make_request(file_path, country)
    
    if status == 200:
        results['200'] += 1
    elif status == 400:
        results['400'] += 1
    elif status == 404:
        results['404'] += 1
    else:
        results['error'] += 1
    
    if (i + 1) % 10 == 0:
        print(f'{i+1}/100 - status {status}')

# summary
print(f'\nresults:')
print(f'  200 ok: {results["200"]}')
print(f'  400 permission denied: {results["400"]}')
print(f'  404 not found: {results["404"]}')
print(f'  errors: {results["error"]}')