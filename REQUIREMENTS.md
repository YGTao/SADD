# Requirements

## Hardware Requirements

### Minimum (for verifying pre-computed results and running individual benchmarks)
- **CPU:** 4+ cores (x86_64)
- **RAM:** 16 GB
- **Storage:** 150 GB free disk space (Docker image ~100 GB uncompressed + experiment outputs)

### Recommended (for full reproduction with parallel execution)
- **CPU:** 8+ cores (for `-j 8` parallel execution)
- **RAM:** 64 GB or more
- **Storage:** 200 GB free disk space

### Paper's Experimental Platform
- **CPU:** Intel Xeon @ 3.20GHz
- **RAM:** 256 GB
- **OS:** Ubuntu 22.04 LTS
- **Execution mode:** Single-process, single-threaded per benchmark

> **Note:** Absolute timing results are hardware-dependent. Relative improvements (percentage gains reported via geometric means) should be consistent across platforms.

## Software Requirements

| Software | Version | Purpose |
|---|---|---|
| Docker | >= 24.0 | Container runtime ([Install guide](https://docs.docker.com/get-docker/)) |

All other dependencies (Python, Java, GCC, Clang, BaseX, Perses, HDD, pandas, matplotlib) are pre-installed inside the Docker image `saddartifact/sadd:latest`.

### Optional
- `tmux` or `screen` — for keeping long-running experiments alive on remote servers

## Docker Image

- **Image:** `saddartifact/sadd:latest` on [Docker Hub](https://hub.docker.com/r/saddartifact/sadd)
- **Compressed download size:** ~36 GB
- **Uncompressed disk usage:** ~100 GB
- **Download time:** ~5–10 minutes on 1 Gbps; ~1 hour on 100 Mbps

## Estimated Experiment Time

All single-core times are computed by summing the T(s) column from the corresponding paper table across all 62 benchmarks and algorithm configurations. Wall-clock times assume `-j 8` parallel execution; actual times may be longer due to load imbalance (the longest benchmark, clang-27137, dominates at ~138 hours across all Table 2 configurations).

| Task | Single-core | Wall time (`-j 8`) |
|---|---|---|
| Reproduce Tables 2–4 from pre-computed CSVs | — | < 1 minute |
| Table 2: ddmin variants (§5.1, RQ1/RQ3) | ~722 hours | ~4 days |
| Table 3: ProbDD variants × 5 runs (§5.2, RQ2/RQ3) | ~1,835 hours | ~10 days |
| Table 4: ablation study (§5.3, RQ4) | ~500 hours | ~3 days |
| Full reproduction (all RQs) | ~3,060 hours | ~17 days |

We also provide pre-computed experimental results in `csv_paper/` and `result_paper/` for reference.
