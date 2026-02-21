import json
import time
import sys
import numpy as np
from google.cloud import storage
from concurrent.futures import ThreadPoolExecutor

def download_file(blob):
    """download a single file"""
    if blob.name.endswith('.json'):
        return json.loads(blob.download_as_text())
    return None

def main(bucket_name):
    start_time = time.time()
    
    # read all files from bucket
    print(f'reading from gs://{bucket_name}/graph_data/')
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = list(bucket.list_blobs(prefix='graph_data/'))
    
    print(f'found {len(blobs)} files, downloading...')
    
    # parallel download 
    pages = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(download_file, blobs)
        for i, result in enumerate(results):
            if result:
                pages.append(result)
            if (i + 1) % 1000 == 0:
                print(f'downloaded {i + 1} files...')
    
    n = len(pages)
    print(f'loaded {n} pages')
    
    # count links
    outgoing = [len(p['links']) for p in pages]
    incoming = [0] * n
    for p in pages:
        for link in p['links']:
            incoming[link] += 1
    
    # print statistics
    print('\noutgoing links:')
    print(f'  avg: {np.mean(outgoing):.2f}')
    print(f'  median: {np.median(outgoing):.2f}')
    print(f'  min: {np.min(outgoing)}')
    print(f'  max: {np.max(outgoing)}')
    print(f'  quintiles: {np.percentile(outgoing, [20, 40, 60, 80])}')
    
    print('\nincoming links:')
    print(f'  avg: {np.mean(incoming):.2f}')
    print(f'  median: {np.median(incoming):.2f}')
    print(f'  min: {np.min(incoming)}')
    print(f'  max: {np.max(incoming)}')
    print(f'  quintiles: {np.percentile(incoming, [20, 40, 60, 80])}')
    
    # build graph structure for pagerank
    outlinks = [p['links'] for p in pages]
    inlinks = [[] for _ in range(n)]
    for i, links in enumerate(outlinks):
        for j in links:
            inlinks[j].append(i)
    
    # pagerank algorithm
    print('\ncomputing pagerank...')
    pr = [1.0/n] * n
    
    for iteration in range(100):
        new_pr = []
        for i in range(n):
            # pr(a) = 0.15/n + 0.85 * sum(pr(t)/c(t))
            rank_sum = 0.0
            for t in inlinks[i]:
                c = len(outlinks[t])
                if c > 0:
                    rank_sum += pr[t] / c
            new_pr.append(0.15/n + 0.85 * rank_sum)
        
        # check convergence
        diff = sum(abs(new_pr[i] - pr[i]) for i in range(n))
        if diff / sum(pr) < 0.005:
            print(f'converged in {iteration + 1} iterations')
            pr = new_pr
            break
        pr = new_pr
    
    # top 5 pages
    top = sorted(enumerate(pr), key=lambda x: x[1], reverse=True)[:5]
    print('\ntop 5 pages by pagerank:')
    for page_id, score in top:
        print(f'  page {page_id}: {score:.6f}')
    
    print(f'\ntotal time: {time.time() - start_time:.2f}s')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: python pagerank_analysis.py BUCKET_NAME')
        sys.exit(1)
    main(sys.argv[1])