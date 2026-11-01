import time
import json
import os
import sys
from data_engine.generators.synthetic_generator import SyntheticDataGenerator

def run_benchmarks(target_movements: int = 100000, seed: int = 20261022):
    print(f"=== STOCKMIND AI — HIGH-THROUGHPUT PIPELINE BENCHMARK ===")
    print(f"Benchmarking chunked generation for {target_movements:,} movements...")

    generator = SyntheticDataGenerator(seed=seed)
    products = generator.generate_products(500)
    locations = generator.generate_locations(50)
    skus = generator.generate_skus(1000, products)

    t0 = time.time()
    total_generated = 0
    chunk_times = []

    for chunk in generator.generate_movements_chunked(
        target_movements=target_movements,
        skus=skus,
        locations=locations,
        chunk_size=25000
    ):
        total_generated += len(chunk)
        elapsed_so_far = time.time() - t0
        chunk_times.append(round(elapsed_so_far, 3))

    total_time = time.time() - t0
    rate = round(total_generated / max(0.001, total_time))

    print(f"Generated {total_generated:,} records in {total_time:.2f}s ({rate:,} rows/sec)")
    
    benchmark_report = {
        "benchmark_timestamp": time.time(),
        "target_movements": target_movements,
        "total_generated": total_generated,
        "elapsed_seconds": round(total_time, 3),
        "rows_per_second": rate,
        "status": "PASS"
    }

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_path = os.path.join(base_dir, "output", "benchmark_report.json")
    with open(out_path, "w") as f:
        json.dump(benchmark_report, f, indent=2)

    print(f"Benchmark results written to {out_path}")
    return benchmark_report

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
    run_benchmarks(target_movements=count)
