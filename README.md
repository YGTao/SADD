# Artifact for *Structure-Aware Delta Debugging with Geometric‑Information Weights*

Thank you for evaluating our artifact. This README provides a **minimal, deterministic path** to reproduce the paper's results (ddmin variants) and a **batched path** for ProbDD variants (5 runs).

---

## 1. System Requirements

- **OS:** Linux (recommended) with Docker Desktop
- **Docker:** ≥ 24.0 — [Install guide](https://docs.docker.com/get-docker/)
- **Optional:** `tmux`/`screen` for long‑running jobs; 

> The experiments (especially probabilistic with 5× repeats) are long. Please consider running inside `tmux`/`screen` on a server.

---

## 2. Docker Environment Setup

We provide a prebuilt image that contains implementations of ddmin, ProbDD, WDD, and SADD algorithms for both Perses and HDD frameworks.

```bash
# Pull image
docker pull saddartifact/sadd:latest

# Start a container (interactive), working in /tmp/WeightDD
# and --name sadd_eval to re‑attach later.
docker run \
  --cap-add SYS_PTRACE \
  -it \
  --name sadd_eval \
  -w /tmp/WeightDD \
  saddartifact/sadd:latest

# Inside container (prompt example):
# coq@<container>:/tmp/WeightDD$
```

> If you encounter permission issues inside the container, try prefixing commands with `sudo` (password: `123`).

---

## 3. Benchmarks

Under the project root (`/tmp/WeightDD` in the container):

- `./c_benchmarks/` — **C** suite (32 programs)
- `./xml_benchmarks/` — **XML** suite (30 inputs)

---

## 4. Prebuilt Tools (JARs)

We supply prebuilt JARs under `/tmp/binaries/`.

```text
/tmp/binaries/
├── perses_deploy.jar
├── perses_stat_deploy.jar
├── token_counter_deploy.jar
├── volume-S-B-0.jar  # V only
├── volume-S-B-1.jar  # V + S + B
├── volume-S0-B1.jar  # V + B
└── volume-S1-B0.jar  # V + S
```

These are used by our scripts to run **ddmin/ProbDD/WDD** baselines and **SADD** (structure‑aware) variants.

> **Naming convention:** In the implementation, the metric denoted *U* (Decision Uniformity) in the paper is referred to as *S*. For example, `V+S` corresponds to V+U in the paper, and `volume-S1-B0.jar` enables V+U with B disabled.

---

## 5. Running Experiments

We provide parallel runners for C and XML suites. Adjust `-j` to match available cores. Paths below assume **container working dir** `/tmp/WeightDD`.
> Full reproduction requires ~3,060 single-core hours (~17 days with `-j 8`). See `REQUIREMENTS.md` for per-table estimates.

### 5.0 Quick Demo Runs (Recommended for Sanity Checks)

For reviewers who want to verify that the reducers run correctly without 
committing to the full experiment, we provide two small demo suites with 
the same directory layout as the full benchmark suites:

- `c_demo_benchmarks/` — 12 C benchmarks (6 clang + 6 gcc)
- `xml_demo_benchmarks/` — 2 XML benchmarks

Any of the runner commands in §5.1–§5.3 can be used on the demo suites by 
simply changing the input path and output directory. For example, the 
following commands mirror §5.1 on the demo suites:

```bash
# C demo: baselines (ddmin + W_ddmin) and SADD
./run_exp_parallel_c.py \
  -s c_demo_benchmarks/* \
  -r perses_ddmin perses_wdd hdd_ddmin hdd_wdd \
  -o result_wdd_c_demo \
  -j 8

./run_exp_parallel_c.py \
  -s c_demo_benchmarks/* \
  -r perses_sadd hdd_sadd \
  -o result_sadd_c_demo \
  -j 8

# XML demo: baselines (ddmin + W_ddmin) and SADD
./run_exp_parallel_xml.py \
  -s xml_demo_benchmarks/xml-* \
  -r perses_ddmin perses_wdd hdd_ddmin hdd_wdd \
  -o result_wdd_xml_demo \
  -j 8

./run_exp_parallel_xml.py \
  -s xml_demo_benchmarks/xml-* \
  -r perses_sadd hdd_sadd \
  -o result_sadd_xml_demo \
  -j 8
```

The same pattern applies to §5.2 (probabilistic variants) and §5.3 (RQ4 
ablation) — just replace `c_benchmarks/` with `c_demo_benchmarks/` and 
adjust the output directory.

**Inspecting demo results.** Each run produces per-benchmark logs under 
the specified output directory (e.g., `result_sadd_c_demo/perses_sadd_0/<benchmark>/`), 
containing reducer output, query count, elapsed time, and the reduced 
program. Reviewers can inspect these logs directly to confirm that the 
reducers are working as expected.

Reviewers may also create their own subsets by copying selected 
benchmarks from `c_benchmarks/` or `xml_benchmarks/` into these demo 
directories.

### 5.1 Ddmin Variants (ddmin, W\_ddmin, SA\_ddmin)

#### C benchmarks

```bash
# Baselines: ddmin + W_ddmin (Perses and HDD frameworks)
./run_exp_parallel_c.py \
  -s c_benchmarks/* \
  -r perses_ddmin perses_wdd hdd_ddmin hdd_wdd \
  -o result_wdd_c \
  -j 8

# Structure‑Aware (SADD) variants
./run_exp_parallel_c.py \
  -s c_benchmarks/* \
  -r perses_sadd hdd_sadd \
  -o result_sadd_c \
  -j 8
```

#### XML benchmarks

```bash
# Baselines: ddmin + W_ddmin
./run_exp_parallel_xml.py \
  -s xml_benchmarks/xml-* \
  -r perses_ddmin perses_wdd hdd_ddmin hdd_wdd \
  -o result_wdd_xml \
  -j 8

# Structure‑Aware (SADD)
./run_exp_parallel_xml.py \
  -s xml_benchmarks/xml-* \
  -r perses_sadd hdd_sadd \
  -o result_sadd_xml \
  -j 8
```

### 5.2 Probabilistic Variants (ProbDD, W\_ProbDD, SA\_ProbDD)

We repeat each probabilistic configuration **5 runs** to mitigate randomness (`-i 5`).

#### C benchmarks

```bash
# ProbDD + W_ProbDD (5 runs)
./run_exp_parallel_c.py \
  -s c_benchmarks/* \
  -r perses_probdd perses_wprobdd hdd_probdd hdd_wprobdd \
  -o result_wprobdd_c \
  -j 8 -i 5

# SA_ProbDD (5 runs)
./run_exp_parallel_c.py \
  -s c_benchmarks/* \
  -r perses_saprobdd hdd_saprobdd \
  -o result_saprobdd_c \
  -j 8 -i 5
```

#### XML benchmarks

```bash
# ProbDD + W_ProbDD (5 runs)
./run_exp_parallel_xml.py \
  -s xml_benchmarks/xml-* \
  -r perses_probdd perses_wprobdd hdd_probdd hdd_wprobdd \
  -o result_wprobdd_xml \
  -j 8 -i 5

# SA_ProbDD (5 runs)
./run_exp_parallel_xml.py \
  -s xml_benchmarks/xml-* \
  -r perses_saprobdd hdd_saprobdd \
  -o result_saprobdd_xml \
  -j 8 -i 5
```

> **Note**: Runner scripts create subfolders ending with `_0`..`_4` for each probabilistic run.

### 5.3 RQ4 Ablation Study 

```bash
# Ablation variants for C
./run_exp_parallel_c.py \
  -s c_benchmarks/* \
  -r perses_sadd_v perses_sadd_vs perses_sadd_vb hdd_sadd_v hdd_sadd_vs hdd_sadd_vb \
  -o result_sadd_c  \
  -j 8

# Ablation variants for XML  
./run_exp_parallel_xml.py \
  -s xml_benchmarks/xml-* \
  -r perses_sadd_v perses_sadd_vs perses_sadd_vb hdd_sadd_v hdd_sadd_vs hdd_sadd_vb \
  -o result_sadd_xml \
  -j 8
```

---

## 6. Converting Results to CSV

Use the helper script to convert each method's logs to CSV format.

> **Note:** We provide processed CSVs in `csv_paper/` — see Section 8 for details.

### 6.1 Deterministic Baselines (ddmin, W\_ddmin)

```bash
# C benchmarks
./convert_result_to_csv.py -d result_wdd_c/perses_ddmin_0/*  -o perses_ddmin_c.csv
./convert_result_to_csv.py -d result_wdd_c/perses_wdd_0/*    -o perses_wdd_c.csv
./convert_result_to_csv.py -d result_wdd_c/hdd_ddmin_0/*     -o hdd_ddmin_c.csv
./convert_result_to_csv.py -d result_wdd_c/hdd_wdd_0/*       -o hdd_wdd_c.csv

# XML benchmarks
./convert_result_to_csv.py -d result_wdd_xml/perses_ddmin_0/* -o perses_ddmin_xml.csv
./convert_result_to_csv.py -d result_wdd_xml/perses_wdd_0/*   -o perses_wdd_xml.csv
./convert_result_to_csv.py -d result_wdd_xml/hdd_ddmin_0/*    -o hdd_ddmin_xml.csv
./convert_result_to_csv.py -d result_wdd_xml/hdd_wdd_0/*      -o hdd_wdd_xml.csv
```

### 6.2 Structure‑Aware (SA\_ddmin)

```bash
# C benchmarks
./convert_result_to_csv.py -d result_sadd_c/perses_sadd_0/* -o perses_sadd_c.csv
./convert_result_to_csv.py -d result_sadd_c/hdd_sadd_0/*    -o hdd_sadd_c.csv

# XML benchmarks
./convert_result_to_csv.py -d result_sadd_xml/perses_sadd_0/* -o perses_sadd_xml.csv
./convert_result_to_csv.py -d result_sadd_xml/hdd_sadd_0/*    -o hdd_sadd_xml.csv
```

### 6.3 Probabilistic Results — Batch Processing (ProbDD, W\_ProbDD, SA\_ProbDD)

We provide two scripts to **collect** and **average** the five probabilistic runs.

#### 6.3.1 Collect five runs → 60 CSVs

```bash
# In /tmp/WeightDD directory (where experimental results are located)
chmod +x collect_probdd_results.sh
./collect_probdd_results.sh
# This reads from result_wprobdd_*/ and result_saprobdd_*/ directories
# Output: ./table_probdd/*.csv (12 configs × 5 runs = 60 files)
```

#### 6.3.2 Average five runs → 12 CSVs

```bash
# Still in /tmp/WeightDD
python3 average_probdd_results.py
# Input: ./table_probdd/*.csv
# Output: ./table_averaged_probdd/*.csv (one per config)
```

### 6.4 RQ4 Ablation Results

```bash
# In /tmp/WeightDD directory
chmod +x collect_rq4_results.sh
./collect_rq4_results.sh
# This reads from result_sadd_c/ and result_sadd_xml/ directories
# Output: ./table_rq4/*.csv (16 files: 8 configs × 2 datasets)
```

---

## 7. Answering Research Questions

### **RQ1: SADD vs. ddmin**

Compare `*_sadd_*.csv` vs `*_ddmin_*.csv` on **output size**, **queries**, **time**.

### **RQ2: SA\_ProbDD vs. ProbDD**

Compare `*_saprobdd_*.csv` vs `*_probdd_*.csv` (use 5‑run averages from `table_averaged_probdd/`).

### **RQ3: Structure‑Aware vs. Weighted**

Compare:
- SA\_ddmin vs W\_ddmin: `*_sadd_*.csv` vs `*_wdd_*.csv`
- SA\_ProbDD vs W\_ProbDD: `*_saprobdd_*.csv` vs `*_wprobdd_*.csv`

### **RQ4: Component Contribution (Ablation)**

Analyze SADD's components **V**, **S**, **B** (see §4 for naming convention) via four configs:
1. **V only** — suffix `_v`
2. **V+S** — suffix `_vs`
3. **V+B** — suffix `_vb`
4. **V+S+B** (full SADD) — no suffix

*Reading guide*: `(V+S)−V` and `(V+B)−V` give individual contributions of **S** and **B**; `full − (V+S) − (V+B) + V` is the **synergy**.

---

## 8. Reproducing Paper Tables

We provide our evaluation results and table generation scripts. The raw reducer outputs are in `result_paper/`, and the corresponding processed CSV files are organized in `csv_paper/`. To reproduce the tables from the paper:

```bash
# Table 2: SADD vs. ddmin
cd csv_paper/table_ddmin
python3 ddmin_table_generator.py
# → Outputs: ddmin_table.tex, means_results.csv, integrated_results.csv

# Table 3: SA_ProbDD vs. ProbDD/W_ProbDD 
cd csv_paper/table_averaged_probdd
python3 probdd_table_generator.py
# → Outputs: probdd_table.tex, probdd_means_results.csv, probdd_integrated_results.csv

# Table 4: Component ablation analysis
cd csv_paper/table_rq4
python3 rq4.py
# → Outputs: ablation_table.tex, ablation_analysis_summary.txt, ablation_detailed_results.csv
```

These scripts will generate LaTeX tables and detailed CSV analysis files using our experimental data. You can also apply these scripts to your own experimental results by organizing the CSVs in the same directory structure.

Directory structure:
- `result_paper/`: Raw experimental outputs from our evaluation runs
- `csv_paper/table_ddmin/`: All deterministic algorithm CSVs and Table 2 generator
- `csv_paper/table_averaged_probdd/`: Averaged probabilistic CSVs and Table 3 generator
- `csv_paper/table_rq4/`: Ablation study CSVs and Table 4 generator with analysis

---

## 9. Troubleshooting

1. **Permission denied in Docker**  
   Use `sudo` (password `123`) inside the container: e.g., `sudo bash`, `sudo ./run_exp_parallel_c.py ...`.

2. **Python missing packages for CSV/plots**  
   `pip install pandas matplotlib` (inside or outside the container, depending on where you post‑process).

3. **Locale/encoding issues**  
   Set `LC_ALL=C.UTF-8` and `LANG=C.UTF-8` inside the shell.

---

## 10. Reusing and Extending SADD

### 10.1 Where the Code Is

The core of SADD is the structural weight function, implemented in:

`perses-weight-dd/src/org/perses/delta/FanoutWeightProvider.kt`

This class computes a per-element weight from each element's subtree
and is invoked by the weighted reducers in the same package. A small
number of additional changes were made at the call sites that previously
supplied token-count weights, so that SADD's structural weights are used
instead. The overall delta-debugging control logic, tree construction,
oracle invocation, and test driver follow Perses and WDD without
substantive modification.

### 10.2 What the Weight Function Does

`FanoutWeightProvider` computes a structural weight

`W = floor( V · ( 1 + λ_S · S + λ_SB · ( S · φ(B) ) ) ) + 1`

from each element's subtree: `V` (geometric volume, computed as
depth × leaves), `S` (decision uniformity in [0,1]), and `B` (effective
branching complexity, saturated via `φ(B) = B / (B + C)`). See Section 3
of the paper for the full formulation. Note: `S` in the code corresponds
to **U** in the paper (see the naming convention note in §4 of this README).

### 10.3 How to Extend the Weight Function

- **Tune hyperparameters**: modify `lambdaS`, `lambdaSB`, and `cSaturation`.
- **Toggle signals**: flip `useEntropy` / `useBranchLoad` (the four
  prebuilt JARs in `binaries/` each fix a different combination; see §4).
- **Add a new signal**: extend the `computeMetrics` DFS and add a term
  to the `factor` expression in `weight(...)`.

### 10.4 How to Run SADD on Your Own Test Input

To apply SADD (or any baseline) to a new bug-triggering input of your own,
follow the layout of any existing benchmark under `c_benchmarks/` or
`xml_benchmarks/`:

1. Create a new directory `c_benchmarks/<name>/` (or `xml_benchmarks/<name>/`).
2. Place your input file and an oracle script that exits with status 0 iff
   the target property (e.g., the bug) is still triggered. Any existing
   benchmark directory can be used as a template.
3. Run the parallel runner:

   `./run_exp_parallel_c.py -s c_benchmarks/<name> -r perses_sadd -o result_new -j 8`

   For XML inputs, use `run_exp_parallel_xml.py` analogously.

---

<!-- ## 11. Citation

If you use this artifact in your research, please cite:
```bibtex
@inproceedings{sadd2026,
  title={Structure-Aware Delta Debugging with Geometric-Information Weights},
  author={Tao, Yonggang and Xue, Jingling},
  booktitle={Proceedings of the 2026 ACM Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering (FSE '26)},
  year={2026},
  publisher={ACM}
}
```

