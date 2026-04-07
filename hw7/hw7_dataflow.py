import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions, GoogleCloudOptions, SetupOptions
import json
import argparse
import time

BUCKET = "san_yan_bucket"
PROJECT = "direct-electron-486319-t6"
INPUT = f"gs://{BUCKET}/graph_data/*.json"
OUTPUT = f"gs://{BUCKET}/dataflow-output"

def parse_page(line):
    try:
        d = json.loads(line)
        return (d["page_id"], d.get("links", []))
    except Exception:
        return None

def emit_incoming(element):
    page_id, links = element
    return [(target, 1) for target in links]

def make_bigrams(line):
    try:
        d = json.loads(line)
        links = d.get("links", [])
        for i in range(len(links) - 1):
            yield (f"page_{links[i]} page_{links[i+1]}", 1)
    except Exception:
        return

def format_outgoing(result):
    lines = ["=== Top 5 Outgoing Links ==="]
    for name, cnt in result:
        lines.append(f"  {name}: {cnt}")
    return "\n".join(lines)

def format_incoming(result):
    lines = ["=== Top 5 Incoming Links ==="]
    for pid, cnt in result:
        lines.append(f"  page_{pid}: {cnt}")
    return "\n".join(lines)

def format_bigrams(result):
    lines = ["=== Top 5 Word Bigrams ==="]
    for bigram, cnt in result:
        lines.append(f"  '{bigram}': {cnt}")
    return "\n".join(lines)

def run():
    options = PipelineOptions([
        "--runner=DataflowRunner",
        f"--project={PROJECT}",
        "--region=us-south1",
        f"--staging_location=gs://{BUCKET}/dataflow-temp/staging",
        f"--temp_location=gs://{BUCKET}/dataflow-temp/temp",
        "--job_name=hw7-combined-v3",
        "--num_workers=1",
        "--worker_machine_type=e2-medium",
    ])
    options.view_as(SetupOptions).save_main_session = True

    start = time.time()

    with beam.Pipeline(options=options) as p:
        parsed = (
            p
            | "Read" >> beam.io.ReadFromText(INPUT)
            | "Parse" >> beam.Map(parse_page)
            | "Filter" >> beam.Filter(lambda x: x is not None)
        )

        # outgoing
        (
            parsed
            | "OutCount" >> beam.Map(lambda x: (f"page_{x[0]}", len(x[1])))
            | "Top5Out" >> beam.combiners.Top.Of(5, key=lambda x: x[1])
            | "FormatOut" >> beam.Map(format_outgoing)
            | "WriteOut" >> beam.io.WriteToText(f"{OUTPUT}/outgoing")
        )

        # incoming
        (
            parsed
            | "EmitTargets" >> beam.FlatMap(emit_incoming)
            | "SumIncoming" >> beam.CombinePerKey(sum)
            | "Top5In" >> beam.combiners.Top.Of(5, key=lambda x: x[1])
            | "FormatIn" >> beam.Map(format_incoming)
            | "WriteIn" >> beam.io.WriteToText(f"{OUTPUT}/incoming")
        )

        # bigrams
        (
            p
            | "Read2" >> beam.io.ReadFromText(INPUT)
            | "Bigrams" >> beam.FlatMap(make_bigrams)
            | "SumBigrams" >> beam.CombinePerKey(sum)
            | "Top5Bigrams" >> beam.combiners.Top.Of(5, key=lambda x: x[1])
            | "FormatBigrams" >> beam.Map(format_bigrams)
            | "WriteBigrams" >> beam.io.WriteToText(f"{OUTPUT}/bigrams")
        )

    print(f"\nDataflow run time: {time.time() - start:.2f}s")

if __name__ == "__main__":
    run()