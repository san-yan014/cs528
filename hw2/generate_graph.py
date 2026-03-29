import os
import random
import json

# generate 20k files with random links
num_files = 20000
max_links = 375
output_dir = 'graph_data'

os.makedirs(output_dir, exist_ok=True)

for i in range(num_files):
    num_links = random.randint(0, max_links)
    links = random.sample(range(num_files), min(num_links, num_files-1))
    
    data = {'page_id': i, 'links': links}
    
    with open(f'{output_dir}/page_{i}.json', 'w') as f:
        json.dump(data, f)
    
    if i % 1000 == 0:
        print(f'{i} files done')

print('done')