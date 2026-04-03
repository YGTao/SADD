# Installation

## Step 1: Install Docker

Install Docker (>= 24.0) following the official guide: https://docs.docker.com/get-docker/

Verify installation:
```bash
docker --version
# Expected: Docker version 24.x or newer
```

## Step 2: Pull the Docker Image

Ensure at least **150 GB** of free disk space, then pull the image:

```bash
docker pull saddartifact/sadd:latest
```

This downloads the pre-built image (~36 GB compressed, ~100 GB uncompressed) containing all compilers, frameworks, benchmarks, and pre-computed results. Download takes approximately 5–10 minutes on 1 Gbps or ~1 hour on 100 Mbps.

## Step 3: Start the Container

```bash
docker run \
  --cap-add SYS_PTRACE \
  -it \
  --name sadd_eval \
  -w /tmp/WeightDD \
  saddartifact/sadd:latest
```

You should see a prompt inside the container:
```
coq@<container>:/tmp/WeightDD$
```

> If you encounter permission issues, use `sudo` (password: `123`).

## Step 4: Validate the Installation

Inside the container, run the table generation script to confirm everything is working:

```bash
cd /tmp/WeightDD/csv_paper/table_ddmin
python3 ddmin_table_generator.py
```

**Expected output:** The script produces three files without errors:
- `ddmin_table.tex` — LaTeX source for Table 2 in the paper
- `means_results.csv` — geometric mean improvements
- `integrated_results.csv` — per-benchmark detailed results

This takes less than 1 minute and confirms that the Docker environment and all pre-computed data are correctly set up. The numbers in these files correspond to Table 2 in the paper.

You can similarly validate Table 3 and Table 4:
```bash
cd /tmp/WeightDD/csv_paper/table_averaged_probdd
python3 probdd_table_generator.py

cd /tmp/WeightDD/csv_paper/table_rq4
python3 rq4.py
```

## Re-attaching to the Container

If you exit the container, re-attach with:
```bash
docker start sadd_eval
docker exec -it sadd_eval bash
```

## Troubleshooting

| Issue | Solution |
|---|---|
| Permission denied | Use `sudo` (password: `123`) |
| Locale/encoding issues | `export LC_ALL=C.UTF-8 LANG=C.UTF-8` |
| Docker image pull slow | Ensure stable network; image is ~36 GB compressed |
| Not enough disk space | Free at least 150 GB on the Docker storage partition |
