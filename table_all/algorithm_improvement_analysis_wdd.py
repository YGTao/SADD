#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os
from scipy.stats import gmean
from collections import defaultdict

def calculate_geometric_mean_improvement(improvements):
    """
    Correctly calculates the geometric mean of improvement percentages.
    Handles positive (improvement) and negative (degradation) values.
    """
    if not improvements:
        return 0.0
    
    # Convert percentage improvements to performance ratios
    # e.g., 20% improvement -> ratio of 0.80
    # e.g., -15% improvement (degradation) -> ratio of 1.15
    ratios = [1 - (imp / 100.0) for imp in improvements]
    
    # Calculate the geometric mean of the ratios
    # We use max(0.00001, r) to avoid issues with zero values in ratios if any
    avg_ratio = gmean([max(0.00001, r) for r in ratios])
    
    # Convert the average ratio back to a percentage improvement
    geo_mean_improvement = (1 - avg_ratio) * 100.0
    return geo_mean_improvement

def extract_benchmark_name(subject):
    """Extract benchmark name from subject path"""
    return subject.split('/')[-1]

def load_algorithm_data():
    """Load time data for all algorithms"""
    
    # Define file configurations  
    file_configs = {
        # HDD Framework
        ('HDD', 'SADDMIN'): ['hdd_sadd_c.csv', 'hdd_sadd_xml.csv'],
        ('HDD', 'WDDMIN'): ['hdd_wdd_c.csv', 'hdd_wdd_xml.csv'],
        ('HDD', 'SAPROBDD'): ['hdd_saprobdd_c.csv', 'hdd_saprobdd_xml.csv'],
        ('HDD', 'WPROBDD'): ['hdd_wprobdd_c.csv', 'hdd_wprobdd_xml.csv'],
        
        # Perses Framework
        ('Perses', 'SADDMIN'): ['perses_sadd_c.csv', 'perses_sadd_xml.csv'],
        ('Perses', 'WDDMIN'): ['perses_wdd_c.csv', 'perses_wdd_xml.csv'],
        ('Perses', 'SAPROBDD'): ['perses_saprobdd_c.csv', 'perses_saprobdd_xml.csv'],
        ('Perses', 'WPROBDD'): ['perses_wprobdd_c.csv', 'perses_wprobdd_xml.csv'],
    }
    
    # Store data by framework -> algorithm -> {benchmark: time}
    data = defaultdict(lambda: defaultdict(dict))
    
    for (framework, algorithm), file_list in file_configs.items():
        
        for filepath in file_list:
            if not os.path.exists(filepath):
                print("Warning: File not found: {}".format(filepath))
                continue
                
            df = pd.read_csv(filepath)
            print("Loaded {}: {} rows".format(filepath, len(df)))
            
            # Extract benchmark names and filter
            df['benchmark'] = df['Subject'].apply(extract_benchmark_name)
            
            # Determine benchmark type from filename
            if '_c.csv' in filepath:
                df_filtered = df[df['benchmark'].str.contains('^(clang-|gcc-)', regex=True, na=False)]
            elif '_xml.csv' in filepath:
                df_filtered = df[df['benchmark'].str.contains('^xml-', regex=True, na=False)]
            else:
                df_filtered = df
            
            # Store benchmark -> time mapping
            for _, row in df_filtered.iterrows():
                benchmark = row['benchmark']
                time_val = row['Time']
                data[framework][algorithm][benchmark] = time_val
    
    return data

def calculate_improvement_rates(data):
    """Calculate improvement rates for each test case"""
    
    results = {}
    
    for framework in ['HDD', 'Perses']:
        if framework not in data:
            continue
            
        results[framework] = {}
        
        print("\n" + "="*60)
        print("{} Framework - Improvement Rate Analysis".format(framework))
        print("="*60)
        
        # Get all unique benchmarks across algorithms
        all_benchmarks = set()
        for algorithm in ['SADDMIN', 'WDDMIN', 'SAPROBDD', 'WPROBDD']:
            if algorithm in data[framework]:
                all_benchmarks.update(data[framework][algorithm].keys())
        
        print("Total unique benchmarks: {}".format(len(all_benchmarks)))
        
        # Calculate improvement rates for each benchmark
        saddmin_improvements = []  # SADDMIN vs WDDMIN (in percentage)
        saprobdd_improvements = []  # SAPROBDD vs WPROBDD (in percentage)
        
        saddmin_total_time = 0
        wddmin_total_time = 0  
        saprobdd_total_time = 0
        wprobdd_total_time = 0
        
        valid_cases = 0
        
        for benchmark in all_benchmarks:
            # Get times for this benchmark
            saddmin_time = data[framework].get('SADDMIN', {}).get(benchmark)
            wddmin_time = data[framework].get('WDDMIN', {}).get(benchmark)
            saprobdd_time = data[framework].get('SAPROBDD', {}).get(benchmark)
            wprobdd_time = data[framework].get('WPROBDD', {}).get(benchmark)
            
            # Calculate SADDMIN vs WDDMIN improvement (as percentage)
            if saddmin_time is not None and wddmin_time is not None and wddmin_time > 0:
                improvement = (wddmin_time - saddmin_time) / wddmin_time * 100.0
                saddmin_improvements.append(improvement)
                saddmin_total_time += saddmin_time
                wddmin_total_time += wddmin_time
                
            # Calculate SAPROBDD vs WPROBDD improvement (as percentage)
            if saprobdd_time is not None and wprobdd_time is not None and wprobdd_time > 0:
                improvement = (wprobdd_time - saprobdd_time) / wprobdd_time * 100.0
                saprobdd_improvements.append(improvement)
                saprobdd_total_time += saprobdd_time
                wprobdd_total_time += wprobdd_time
                
            # Count valid cases (where all 4 algorithms have data)
            if all(t is not None for t in [saddmin_time, wddmin_time, saprobdd_time, wprobdd_time]):
                valid_cases += 1
        
        print("Valid test cases with all 4 algorithms: {}".format(valid_cases))
        print("SADDMIN vs WDDMIN comparisons: {}".format(len(saddmin_improvements)))
        print("SAPROBDD vs WPROBDD comparisons: {}".format(len(saprobdd_improvements)))
        
        # Calculate geometric means of improvement rates using the correct method
        saddmin_gmean = 0
        saprobdd_gmean = 0
        
        if saddmin_improvements:
            saddmin_gmean = calculate_geometric_mean_improvement(saddmin_improvements)
            print("\nSADDMIN vs WDDMIN:")
            print("  Improvement rates range: {:.2f}% to {:.2f}%".format(
                min(saddmin_improvements), max(saddmin_improvements)))
            print("  Geometric mean improvement: {:.2f}%".format(saddmin_gmean))
        
        if saprobdd_improvements:
            saprobdd_gmean = calculate_geometric_mean_improvement(saprobdd_improvements)
            print("\nSAPROBDD vs WPROBDD:")
            print("  Improvement rates range: {:.2f}% to {:.2f}%".format(
                min(saprobdd_improvements), max(saprobdd_improvements)))
            print("  Geometric mean improvement: {:.2f}%".format(saprobdd_gmean))
        
        # Calculate overall SA vs W improvement (combining all improvement rates)
        all_sa_improvements = saddmin_improvements + saprobdd_improvements
        overall_sa_gmean = 0
        
        if all_sa_improvements:
            overall_sa_gmean = calculate_geometric_mean_improvement(all_sa_improvements)
            print("\n" + "-"*40)
            print("OVERALL SA* vs W* ALGORITHMS:")
            print("  Total improvement cases: {} (all SA vs W comparisons)".format(len(all_sa_improvements)))
            print("  Combined geometric mean improvement: {:.2f}%".format(overall_sa_gmean))
            print("  (This combines SADDMIN vs WDDMIN + SAPROBDD vs WPROBDD)")
            print("  Improvement rates range: {:.2f}% to {:.2f}%".format(
                min(all_sa_improvements), max(all_sa_improvements)))
        
        # Calculate total time comparisons
        total_sa_time = saddmin_total_time + saprobdd_total_time
        total_w_time = wddmin_total_time + wprobdd_total_time
        
        print("\n" + "-"*40)
        print("Total Time Comparisons:")
        print("SADDMIN total time: {:,.2f} seconds".format(saddmin_total_time))
        print("WDDMIN total time: {:,.2f} seconds".format(wddmin_total_time))
        print("SAPROBDD total time: {:,.2f} seconds".format(saprobdd_total_time))  
        print("WPROBDD total time: {:,.2f} seconds".format(wprobdd_total_time))
        print("")
        print("SADDMIN + SAPROBDD total: {:,.2f} seconds".format(total_sa_time))
        print("WDDMIN + WPROBDD total: {:,.2f} seconds".format(total_w_time))
        
        if total_w_time > 0:
            overall_improvement = (total_w_time - total_sa_time) / total_w_time * 100.0
            print("Overall time improvement: {:.2f}%".format(overall_improvement))
        
        # Store results
        results[framework] = {
            'saddmin_improvements': saddmin_improvements,
            'saprobdd_improvements': saprobdd_improvements,
            'all_sa_improvements': all_sa_improvements,
            'saddmin_gmean': saddmin_gmean,
            'saprobdd_gmean': saprobdd_gmean,
            'overall_sa_gmean': overall_sa_gmean,
            'total_times': {
                'saddmin': saddmin_total_time,
                'wddmin': wddmin_total_time, 
                'saprobdd': saprobdd_total_time,
                'wprobdd': wprobdd_total_time,
                'sa_combined': total_sa_time,
                'w_combined': total_w_time,
                'overall_improvement': (total_w_time - total_sa_time) / total_w_time * 100.0 if total_w_time > 0 else 0
            },
            'valid_cases': valid_cases
        }
    
    return results

def generate_summary_report(results):
    """Generate final summary report"""
    
    print("\n" + "="*80)
    print("FINAL SUMMARY REPORT")
    print("="*80)
    
    print("{:<12} {:<25} {:<15} {:<15}".format(
        "Framework", "Comparison", "Cases", "Geometric Mean"))
    print("-" * 80)
    
    for framework in ['HDD', 'Perses']:
        if framework in results:
            r = results[framework]
            print("{:<12} {:<25} {:<15} {:<15.2f}%".format(
                framework, "SADDMIN vs WDDMIN", 
                len(r['saddmin_improvements']), r['saddmin_gmean']))
            print("{:<12} {:<25} {:<15} {:<15.2f}%".format(
                framework, "SAPROBDD vs WPROBDD",
                len(r['saprobdd_improvements']), r['saprobdd_gmean']))
            print("{:<12} {:<25} {:<15} {:<15.2f}%".format(
                framework, "SA* vs W* (OVERALL)", 
                len(r['all_sa_improvements']), r['overall_sa_gmean']))
            print("-" * 80)
    
    print("\nTOTAL TIME SUMMARY:")
    print("-" * 50)
    for framework in ['HDD', 'Perses']:
        if framework in results:
            times = results[framework]['total_times']
            print("{} Framework:".format(framework))
            print("  SADDMIN + SAPROBDD: {:,.1f} seconds".format(times['sa_combined']))
            print("  WDDMIN + WPROBDD: {:,.1f} seconds".format(times['w_combined']))
            print("  Overall improvement: {:.1f}%".format(times['overall_improvement']))
            print("")

def main():
    """Main analysis function"""
    print("=== Time Improvement Rate Analysis ===")
    print("Calculating improvement rates as: (old_time - new_time) / old_time * 100")
    print("Using CORRECT geometric mean calculation (same as document #2)")
    print("Computing geometric means for:")
    print("  1. SADDMIN vs WDDMIN")
    print("  2. SAPROBDD vs WPROBDD") 
    print("  3. Overall SA* vs W* (combining all improvement rates - 124 cases)")
    print("")
    
    # Load data
    data = load_algorithm_data()
    
    # Calculate improvement rates
    results = calculate_improvement_rates(data)
    
    # Generate summary
    generate_summary_report(results)
    
    # Save results to file
    with open("improvement_analysis_results_wdd.txt", "w") as f:
        f.write("Time Improvement Rate Analysis Results (CORRECTED GEOMETRIC MEAN)\n")
        f.write("Using same geometric mean calculation as document #2\n")
        f.write("="*60 + "\n\n")
        
        for framework in ['HDD', 'Perses']:
            if framework in results:
                r = results[framework]
                f.write("{} Framework:\n".format(framework))
                f.write("  SADDMIN vs WDDMIN geometric mean improvement: {:.2f}% ({} cases)\n".format(
                    r['saddmin_gmean'], len(r['saddmin_improvements'])))
                f.write("  SAPROBDD vs WPROBDD geometric mean improvement: {:.2f}% ({} cases)\n".format(
                    r['saprobdd_gmean'], len(r['saprobdd_improvements'])))
                f.write("  OVERALL SA* vs W* geometric mean improvement: {:.2f}% ({} cases)\n".format(
                    r['overall_sa_gmean'], len(r['all_sa_improvements'])))
                f.write("  Total time - SADDMIN + SAPROBDD: {:,.2f} seconds\n".format(r['total_times']['sa_combined']))
                f.write("  Total time - WDDMIN + WPROBDD: {:,.2f} seconds\n".format(r['total_times']['w_combined']))
                f.write("  Overall improvement: {:.2f}%\n".format(r['total_times']['overall_improvement']))
                f.write("\n")
    
    print("Results saved to: improvement_analysis_results_wdd.txt")

if __name__ == "__main__":
    main()