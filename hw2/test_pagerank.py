# test on simple 4-node graph

# graph: 0->1,2  1->2  2->0  3->0,1,2
pages = [
    {'page_id': 0, 'links': [1, 2]},
    {'page_id': 1, 'links': [2]},
    {'page_id': 2, 'links': [0]},
    {'page_id': 3, 'links': [0, 1, 2]}
]

n = 4
outlinks = [p['links'] for p in pages]
inlinks = [[] for _ in range(n)]
for i, links in enumerate(outlinks):
    for j in links:
        inlinks[j].append(i)

# run pagerank
pr = [1.0/n] * n
for iteration in range(100):
    new_pr = []
    for i in range(n):
        rank_sum = 0.0
        for t in inlinks[i]:
            c = len(outlinks[t])
            if c > 0:
                rank_sum += pr[t] / c
        new_pr.append(0.15/n + 0.85 * rank_sum)
    
    diff = sum(abs(new_pr[i] - pr[i]) for i in range(n))
    if diff / sum(pr) < 0.005:
        break
    pr = new_pr

# verify
total = sum(pr)
print(f'pagerank sum: {total:.6f} (should be ~1.0)')
assert abs(total - 1.0) < 0.01, 'sum should be 1'

max_page = pr.index(max(pr))
print(f'highest ranked page: {max_page} (should be 2)')
assert max_page == 2, 'page 2 should have highest rank (3 incoming links)'

print('all tests passed!')
print(f'pageranks: {[f"{x:.4f}" for x in pr]}')