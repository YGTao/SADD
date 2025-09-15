#!/bin/bash
# Collect SAdd results (C + XML) into 16 CSVs -> table_rq4/
# Each input dir looks like: result_sadd_c/hdd_sadd_v_0 (etc.)

set -euo pipefail

echo "=== SAdd Results Collection Script (C + XML) ==="

OUT_DIR="table_rq4"
mkdir -p "$OUT_DIR"

# 8 configs for each dataset (C/XML)
configs=(hdd_sadd_0 hdd_sadd_v_0 hdd_sadd_vb_0 hdd_sadd_vs_0 \
         perses_sadd_0 perses_sadd_v_0 perses_sadd_vb_0 perses_sadd_vs_0)

datasets=("c" "xml")   # result_sadd_c / result_sadd_xml
total_files=$(( ${#configs[@]} * ${#datasets[@]} ))
current_file=0

echo "Target output dir: $OUT_DIR"
echo "Will generate $total_files CSV files (8 C + 8 XML)."
echo ""

for ds in "${datasets[@]}"; do
  base_dir="result_sadd_${ds}"
  echo "--- Dataset: ${ds^^}  (base: $base_dir) ---"

  for cfg in "${configs[@]}"; do
    current_file=$((current_file + 1))

    input_dir="${base_dir}/${cfg}"
    base_name="${cfg%_0}"
    output_file="${OUT_DIR}/${base_name}_${ds}.csv"

    echo "[$current_file/$total_files] ${base_name}_${ds}.csv"
    echo "  Input : $input_dir/*"
    echo "  Output: $output_file"

    if [ ! -d "$input_dir" ]; then
      echo "  ✗ WARNING: $input_dir does not exist, skipping..."
      echo ""
      continue
    fi

    if [ -z "$(ls -A "$input_dir" 2>/dev/null)" ]; then
      echo "  ✗ WARNING: $input_dir is empty, skipping..."
      echo ""
      continue
    fi

    echo "  Running: ./convert_result_to_csv.py -d $input_dir/* -o $output_file"
    if ./convert_result_to_csv.py -d $input_dir/* -o "$output_file"; then
      echo "  ✓ OK: $output_file"
    else
      echo "  ✗ FAILED: $output_file"
    fi
    echo ""
  done
done

echo "=== Collection Summary ==="
echo "Expected files: $total_files"

generated_count=0
if [ -d "$OUT_DIR" ]; then
  generated_count=$(find "$OUT_DIR" -name "*.csv" 2>/dev/null | wc -l)
fi

echo "Generated files: $generated_count"
echo "Output directory: $OUT_DIR/"
echo ""
echo "Generated CSV list:"
if [ "$generated_count" -gt 0 ]; then
  ls -la "$OUT_DIR"/*.csv 2>/dev/null | awk '{printf "  %-40s (%s bytes)\n", $9, $5}'
else
  echo "  No CSV files found"
fi

echo ""
echo "Collection complete!"

