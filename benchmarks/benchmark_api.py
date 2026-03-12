"""
Performance benchmark for the /preprocess/basic and /preprocess/nlp API endpoints.

Runs two benchmark modes for each endpoint:
  • Whole-text  — full file sent as one request
  • Chunked     — file split with splitlines(), one request per line,
                  results joined back into a single string

USAGE
-----
Start the server first, then run from the project root:

    python benchmarks/benchmark_api.py

Options:
    --url   Base URL of the running server (default: http://localhost:8000)
    --runs  Number of timed passes per input file (default: 5)
    --input Path to a single .txt file to benchmark (overrides inputs/ dir)

The benchmark reuses the same config.json and inputs/ from the integration
test suite:

    preprocess/tests/integration/config.json
    preprocess/tests/integration/inputs/*.txt
"""

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

INTEGRATION_DIR = Path(__file__).parent.parent / "preprocess" / "tests" / "integration"
CONFIG_FILE = INTEGRATION_DIR / "config.json"
INPUTS_DIR = INTEGRATION_DIR / "inputs"
PROJECT_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def resolve_path(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        print(f"ERROR: No config.json found at {CONFIG_FILE}")
        print("       Set up the integration test config first (see preprocess/tests/integration/).")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_replacement_table(config: dict) -> dict:
    table_path_str = config.get("replacement_table")
    if not table_path_str:
        print("ERROR: No 'replacement_table' key in config.json.")
        sys.exit(1)
    p = resolve_path(table_path_str)
    if not p.exists():
        print(f"ERROR: Replacement table not found: {p}")
        sys.exit(1)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def load_input_files(override: str | None) -> list[Path]:
    if override:
        p = Path(override)
        if not p.exists():
            print(f"ERROR: Input file not found: {p}")
            sys.exit(1)
        return [p]
    if not INPUTS_DIR.exists():
        print(f"ERROR: Inputs directory not found: {INPUTS_DIR}")
        sys.exit(1)
    files = sorted(INPUTS_DIR.glob("*.txt"))
    if not files:
        print(f"ERROR: No .txt files found in {INPUTS_DIR}")
        sys.exit(1)
    return files


def check_server(base_url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{base_url}/health", timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def post_json(url: str, payload: dict) -> tuple[float, dict]:
    """POST payload, return (elapsed_ms, response_body)."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=120) as response:
        body = json.loads(response.read())
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return elapsed_ms, body


def percentile(data: list[float], p: float) -> float:
    sorted_data = sorted(data)
    idx = (len(sorted_data) - 1) * p / 100
    lo = int(idx)
    hi = lo + 1
    frac = idx - lo
    if hi >= len(sorted_data):
        return sorted_data[lo]
    return sorted_data[lo] + frac * (sorted_data[hi] - sorted_data[lo])


def fmt_ms(ms: float) -> str:
    return f"{ms:.0f}ms"


def print_stats(label: str, samples_ms: list[float]):
    mn = min(samples_ms)
    med = statistics.median(samples_ms)
    mean = statistics.mean(samples_ms)
    p95 = percentile(samples_ms, 95)
    mx = max(samples_ms)
    print(f"    min {fmt_ms(mn)}  median {fmt_ms(med)}  mean {fmt_ms(mean)}  p95 {fmt_ms(p95)}  max {fmt_ms(mx)}")


# ---------------------------------------------------------------------------
# Benchmark runners
# ---------------------------------------------------------------------------

def benchmark_endpoint(
    endpoint_url: str,
    endpoint_label: str,
    input_files: list[Path],
    base_payload: dict,
    runs: int,
) -> list[float]:
    """Returns flat list of all latency samples in ms."""
    box_width = 63
    print(f"\n  ┌─ {endpoint_label} {'─' * (box_width - len(endpoint_label) - 4)}┐")

    all_samples: list[float] = []

    for input_file in input_files:
        text = input_file.read_text(encoding="utf-8")
        payload = {**base_payload, "text": text}
        char_count = len(text)

        print(f"  │  {input_file.name}  ({char_count:,} chars)")

        # Warm-up run (not counted)
        try:
            post_json(endpoint_url, payload)
        except Exception as e:
            print(f"  │    ERROR during warm-up: {e}")
            print(f"  └{'─' * box_width}┘")
            return []

        # Timed runs
        samples: list[float] = []
        for i in range(runs):
            try:
                elapsed_ms, _ = post_json(endpoint_url, payload)
                samples.append(elapsed_ms)
                print(f"  │    run {i + 1}/{runs}: {fmt_ms(elapsed_ms)}", end="\r")
            except Exception as e:
                print(f"  │    ERROR on run {i + 1}: {e}")

        print(" " * 40, end="\r")  # clear the run counter line
        if samples:
            print_stats(input_file.name, samples)
            all_samples.extend(samples)

    if all_samples:
        total_time_s = sum(all_samples) / 1000
        throughput = len(all_samples) / total_time_s if total_time_s > 0 else 0
        print(f"  │")
        print(f"  │  Overall  ({len(all_samples)} requests total)")
        print_stats("overall", all_samples)
        print(f"  │  Throughput: {throughput:.1f} req/s")

    print(f"  └{'─' * box_width}┘")
    return all_samples


def benchmark_endpoint_chunked(
    endpoint_url: str,
    endpoint_label: str,
    input_files: list[Path],
    base_payload: dict,
    runs: int,
) -> None:
    """
    Split each input file with splitlines(), send one request per line,
    join the responses back, and report per-line latency + total wall-clock
    time per pass.

    Empty lines are passed through without an API call (they carry no
    content to process).
    """
    box_width = 63
    print(f"\n  ┌─ {endpoint_label} {'─' * (box_width - len(endpoint_label) - 4)}┐")

    for input_file in input_files:
        text = input_file.read_text(encoding="utf-8")
        lines = text.splitlines()
        non_empty = [l for l in lines if l.strip()]

        print(f"  │  {input_file.name}  ({len(text):,} chars, {len(lines)} lines, {len(non_empty)} non-empty)")

        def run_pass() -> tuple[list[float], str]:
            """Send one request per non-empty line; return (latencies_ms, rejoined_text)."""
            line_results: list[str] = []
            latencies: list[float] = []
            for line in lines:
                if not line.strip():
                    line_results.append(line)
                    continue
                payload = {**base_payload, "text": line}
                elapsed_ms, body = post_json(endpoint_url, payload)
                latencies.append(elapsed_ms)
                line_results.append(body.get("text", line))
            return latencies, "\n".join(line_results)

        # Warm-up pass (not counted)
        try:
            run_pass()
        except Exception as e:
            print(f"  │    ERROR during warm-up: {e}")
            print(f"  └{'─' * box_width}┘")
            return

        all_line_latencies: list[float] = []
        pass_totals_ms: list[float] = []

        for i in range(runs):
            try:
                t0 = time.perf_counter()
                latencies, _ = run_pass()
                wall_ms = (time.perf_counter() - t0) * 1000
                all_line_latencies.extend(latencies)
                pass_totals_ms.append(wall_ms)
                print(f"  │    pass {i + 1}/{runs}: {fmt_ms(wall_ms)} total  ({len(latencies)} requests)", end="\r")
            except Exception as e:
                print(f"  │    ERROR on pass {i + 1}: {e}")

        print(" " * 60, end="\r")

        if pass_totals_ms and all_line_latencies:
            print(f"  │  Per-request latency across all passes ({len(all_line_latencies)} requests):")
            print(f"  │  ", end="")
            print_stats("", all_line_latencies)
            print(f"  │  Wall-clock time per pass ({len(lines)} lines reassembled):")
            print(f"  │  ", end="")
            print_stats("", pass_totals_ms)
            avg_pass_s = statistics.mean(pass_totals_ms) / 1000
            throughput = len(non_empty) / avg_pass_s if avg_pass_s > 0 else 0
            print(f"  │  Throughput: {throughput:.1f} lines/s")

    print(f"  └{'─' * box_width}┘")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark /preprocess/basic and /preprocess/nlp")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--runs", type=int, default=5, help="Timed runs per input file")
    parser.add_argument("--input", default=None, help="Single .txt file to use (overrides inputs/ dir)")
    return parser.parse_args()


def main():
    args = parse_args()
    base_url = args.url.rstrip("/")

    print(f"\n  Server: {base_url}  ", end="")
    if check_server(base_url):
        print("(reachable)")
    else:
        print("(UNREACHABLE — is the server running?)")
        sys.exit(1)

    config = load_config()
    replacement_table = load_replacement_table(config)
    input_files = load_input_files(args.input)

    print(f"  Input files: {len(input_files)}  |  Runs per file: {args.runs}  |  Warm-up: 1 run (excluded)")

    # ── /preprocess/basic ───────────────────────────────────────────────────
    basic_payload = {
        "replacement_table": replacement_table,
        "single_kanji_filter": config.get("single_kanji_filter", True),
        "verbose": False,
    }
    benchmark_endpoint(
        endpoint_url=f"{base_url}/preprocess/basic",
        endpoint_label="POST /preprocess/basic  [whole-text]",
        input_files=input_files,
        base_payload=basic_payload,
        runs=args.runs,
    )
    benchmark_endpoint_chunked(
        endpoint_url=f"{base_url}/preprocess/basic",
        endpoint_label="POST /preprocess/basic  [chunked]",
        input_files=input_files,
        base_payload=basic_payload,
        runs=args.runs,
    )

    # ── /preprocess/nlp ─────────────────────────────────────────────────────
    tokenizer = config.get("tokenizer", "fugashi")
    nlp_payload = {
        "replacement_table": replacement_table,
        "tokenizer": tokenizer,
        "tag_potential_proper_nouns": config.get("tag_potential_proper_nouns", False),
        "use_single_kanji_filter": config.get("single_kanji_filter", True),
        "use_user_dict": config.get("use_user_dict", False),
        "user_dic_path": config.get("user_dict_path"),
        "verbose": False,
    }
    benchmark_endpoint(
        endpoint_url=f"{base_url}/preprocess/nlp",
        endpoint_label=f"POST /preprocess/nlp  ({tokenizer})  [whole-text]",
        input_files=input_files,
        base_payload=nlp_payload,
        runs=args.runs,
    )
    benchmark_endpoint_chunked(
        endpoint_url=f"{base_url}/preprocess/nlp",
        endpoint_label=f"POST /preprocess/nlp  ({tokenizer})  [chunked]",
        input_files=input_files,
        base_payload=nlp_payload,
        runs=args.runs,
    )

    print()


if __name__ == "__main__":
    main()
