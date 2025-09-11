#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import glob
from collections import defaultdict

def average_csv_files(base_name, input_dir="table_probdd", output_dir="table_averaged_probdd"):
    """
    Average 5 CSV files with same base name but different suffixes (0,1,2,3,4)
    """
    print("Processing: {}".format(base_name))
    
    # Find all files with this base name
    pattern = os.path.join(input_dir, "{}_*.csv".format(base_name))
    files = glob.glob(pattern)
    
    if len(files) != 5:
        print("  Warning: Expected 5 files, found {} for {}".format(len(files), base_name))
        for f in files:
            print("    Found: {}".format(f))
    
    # Read all CSV files
    dataframes = []
    for file_path in sorted(files):
        try:
            df = pd.read_csv(file_path)
            dataframes.append(df)
            print("  Read: {} ({} rows)".format(os.path.basename(file_path), len(df)))
        except Exception as e:
            print("  Error reading {}: {}".format(file_path, e))
            return False
    
    if not dataframes:
        print("  No valid data files found for {}".format(base_name))
        return False
    
    # Combine all dataframes and calculate averages
    combined_data = defaultdict(list)
    
    # Process each dataframe
    for df in dataframes:
        for _, row in df.iterrows():
            subject = row['Subject']
            combined_data[subject].append({
                'Time': row['Time'],
                'Token_remaining': row['Token_remaining'], 
                'Query': row['Query']
            })
    
    # Calculate averages for each subject
    averaged_results = []
    for subject, measurements in combined_data.items():
        if len(measurements) == 0:
            continue
            
        avg_time = sum(m['Time'] for m in measurements) / len(measurements)
        avg_tokens = sum(m['Token_remaining'] for m in measurements) / len(measurements)
        avg_query = sum(m['Query'] for m in measurements) / len(measurements)
        
        averaged_results.append({
            'Subject': subject,
            'Query': int(round(avg_query)),
            'Time': int(round(avg_time)),
            'Token_remaining': int(round(avg_tokens))
        })
    
    # Create output dataframe
    output_df = pd.DataFrame(averaged_results)
    output_df = output_df.sort_values('Subject')  # Sort by subject name
    
    # Save to output file
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "{}.csv".format(base_name))
    output_df.to_csv(output_file, index=False)
    
    print("  Averaged {} subjects from {} files".format(len(averaged_results), len(dataframes)))
    print("  Saved: {}".format(output_file))
    return True

def main():
    """
    Main function to process all configurations
    """
    print("=== ProbDD Results Averaging Script ===")
    print("Averaging 5 runs per configuration into single files")
    print("")
    
    # Define all base configurations (without _0,_1,_2,_3,_4 suffixes)
    configurations = [
        "hdd_probdd_c",
        "hdd_probdd_xml", 
        "hdd_wprobdd_c",
        "hdd_wprobdd_xml",
        "hdd_saprobdd_c",
        "hdd_saprobdd_xml",
        "perses_probdd_c",
        "perses_probdd_xml",
        "perses_wprobdd_c", 
        "perses_wprobdd_xml",
        "perses_saprobdd_c",
        "perses_saprobdd_xml"
    ]
    
    input_dir = "table_probdd"
    output_dir = "table_averaged_probdd"
    
    # Check input directory exists
    if not os.path.exists(input_dir):
        print("Error: Input directory '{}' does not exist".format(input_dir))
        return
    
    # Count input files
    input_files = glob.glob(os.path.join(input_dir, "*.csv"))
    print("Found {} CSV files in {}".format(len(input_files), input_dir))
    print("")
    
    # Process each configuration
    successful = 0
    failed = 0
    
    for config in configurations:
        if average_csv_files(config, input_dir, output_dir):
            successful += 1
        else:
            failed += 1
        print("")
    
    # Summary
    print("=== Processing Summary ===")
    print("Expected configurations: {}".format(len(configurations)))
    print("Successfully processed: {}".format(successful))
    print("Failed: {}".format(failed))
    print("")
    
    # List output files
    output_files = glob.glob(os.path.join(output_dir, "*.csv"))
    print("Generated {} averaged files in {}:".format(len(output_files), output_dir))
    for file_path in sorted(output_files):
        file_size = os.path.getsize(file_path)
        print("  {} ({} bytes)".format(os.path.basename(file_path), file_size))
    
    print("")
    print("Averaging complete!")

if __name__ == "__main__":
    main()
