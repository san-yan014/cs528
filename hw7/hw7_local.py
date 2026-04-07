import json
import time
from collections import defaultdict
from google.cloud import storage

BUCKET = "san_yan_bucket"
PROJECT = "direct-electron-486319-t6"
PREFIX = "graph_data/"

def main():
    client = storage.Client(project=PROJECT)
    bucket = client.bucket(BUCKET)

    print("Listing files...")
    blobs = list(bucket.list_blobs(prefix=PREFIX))
    print(f"Found {len(blobs)} files")

    outgoing_counts = {}   # page_id -> outgoing count
    incoming_counts = defaultdict(int)  # page_id -> incoming count
    bigram_counts = defaultdict(int)

    start = time.time()

    for i, blob in enumerate(blobs):
        if not blob.name.endswith(".json"):
            continue
        try:
            d = json.loads(blob.download_as_text())
        except Exception:
            continue

        pid = d["page_id"]
        links = d.get("links", [])

        # outgoing
        outgoing_counts[pid] = len(links)

        # incoming
        for target in links:
            incoming_counts[target] += 1

        # bigrams
        for j in range(len(links) - 1):
            bigram = f"page_{links[j]} page_{links[j+1]}"
            bigram_counts[bigram] += 1

        if (i + 1) % 2000 == 0:
            print(f"  processed {i+1} files...")

    elapsed = time.time() - start

    # top 5 outgoing
    top_out = sorted(outgoing_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    print("\n=== Top 5 Outgoing Links ===")
    for pid, cnt in top_out:
        print(f"  page_{pid}: {cnt}")

    # top 5 incoming
    top_in = sorted(incoming_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    print("\n=== Top 5 Incoming Links ===")
    for pid, cnt in top_in:
        print(f"  page_{pid}: {cnt}")

    # top 5 bigrams
    top_bigrams = sorted(bigram_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    print("\n=== Top 5 Word Bigrams ===")
    for bigram, cnt in top_bigrams:
        print(f"  '{bigram}': {cnt}")

    print(f"\nLocal run time: {elapsed:.2f}s")

if __name__ == "__main__":
    main()