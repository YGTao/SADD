#!/bin/bash

# Script to collect all ProbDD experiment results into CSV files
# Total: 12 configurations × 5 runs = 60 CSV files

echo "=== ProbDD Results Collection Script ==="

# Create output directory if it doesn't exist
mkdir -p table_probdd

# Define configurations
configurations=(
    "result_wprobdd_c/hdd_probdd:hdd_probdd_c"
    "result_wprobdd_c/hdd_wprobdd:hdd_wprobdd_c"  
    "result_wprobdd_c/perses_probdd:perses_probdd_c"
    "result_wprobdd_c/perses_wprobdd:perses_wprobdd_c"
    "result_wprobdd_xml/hdd_probdd:hdd_probdd_xml"
    "result_wprobdd_xml/hdd_wprobdd:hdd_wprobdd_xml"
    "result_wprobdd_xml/perses_probdd:perses_probdd_xml"
    "result_wprobdd_xml/perses_wprobdd:perses_wprobdd_xml"
    "result_saprobdd_c/hdd_saprobdd:hdd_saprobdd_c"
    "result_saprobdd_c/perses_saprobdd:perses_saprobdd_c"
    "result_saprobdd_xml/hdd_saprobdd:hdd_saprobdd_xml"
    "result_saprobdd_xml/perses_saprobdd:perses_saprobdd_xml"
)

# Counter for progress tracking
total_files=60
current_file=0

echo "Collecting $total_files CSV files..."
echo ""

# Process each configuration
for config in "${configurations[@]}"; do
    # Split configuration string
    IFS=':' read -r input_pattern output_base <<< "$config"
    
    echo "Processing configuration: $output_base"
    
    # Process each run (0 to 4)
    for run in {0..4}; do
        current_file=$((current_file + 1))
        
        # Build input directory and output filename
        input_dir="${input_pattern}_${run}"
        output_file="table_probdd/${output_base}_${run}.csv"
        
        echo "  [$current_file/$total_files] Generating ${output_base}_${run}.csv"
        echo "    Input: $input_dir/*"
        echo "    Output: $output_file"
        
        # Check if input directory exists
        if [ ! -d "$input_dir" ]; then
            echo "    ✗ WARNING: Input directory $input_dir does not exist, skipping..."
            continue
        fi
        
        # Check if directory has any files
        if [ -z "$(ls -A $input_dir 2>/dev/null)" ]; then
            echo "    ✗ WARNING: Input directory $input_dir is empty, skipping..."
            continue
        fi
        
        # FIXED: Run conversion WITHOUT quotes around wildcard
        echo "    Running: ./convert_result_to_csv.py -d $input_dir/* -o $output_file"
        if ./convert_result_to_csv.py -d $input_dir/* -o "$output_file"; then
            echo "    ✓ Successfully created $output_file"
        else
            echo "    ✗ Failed to create $output_file"
        fi
        echo ""
    done
done

echo "=== Collection Summary ==="
echo "Expected files: $total_files"

# Count generated files
generated_count=0
if [ -d "table_probdd" ]; then
    generated_count=$(find table_probdd -name "*.csv" 2>/dev/null | wc -l)
fi

echo "Generated files: $generated_count"
echo "Output directory: table_probdd/"
echo ""

# List all generated files
echo "Generated CSV files:"
if [ $generated_count -gt 0 ]; then
    ls -la table_probdd/*.csv 2>/dev/null | awk '{printf "  %-40s (%s bytes)\n", $9, $5}' 
else
    echo "  No CSV files found"
fi

echo ""
echo "Collection complete!"