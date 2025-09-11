#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os
from scipy.stats import gmean, wilcoxon  # FIXED: Use gmean instead of geometric_mean
from collections import defaultdict


def extract_benchmark_name(subject):
    """Extract benchmark name from subject path"""
    return subject.split('/')[-1]

def load_ablation_data():
    """Load all 16 CSV files for ablation study"""
    
    # Define file mapping
    file_configs = {
        # HDD Framework
        ('HDD', 'c', 'V-only'): 'hdd_sadd_v_c.csv',
        ('HDD', 'c', 'V+S'): 'hdd_sadd_vs_c.csv', 
        ('HDD', 'c', 'V+B'): 'hdd_sadd_vb_c.csv',
        ('HDD', 'c', 'V+S+B'): 'hdd_sadd_c.csv',
        ('HDD', 'xml', 'V-only'): 'hdd_sadd_v_xml.csv',
        ('HDD', 'xml', 'V+S'): 'hdd_sadd_vs_xml.csv',
        ('HDD', 'xml', 'V+B'): 'hdd_sadd_vb_xml.csv', 
        ('HDD', 'xml', 'V+S+B'): 'hdd_sadd_xml.csv',
        
        # Perses Framework
        ('Perses', 'c', 'V-only'): 'perses_sadd_v_c.csv',
        ('Perses', 'c', 'V+S'): 'perses_sadd_vs_c.csv',
        ('Perses', 'c', 'V+B'): 'perses_sadd_vb_c.csv',
        ('Perses', 'c', 'V+S+B'): 'perses_sadd_c.csv',
        ('Perses', 'xml', 'V-only'): 'perses_sadd_v_xml.csv',
        ('Perses', 'xml', 'V+S'): 'perses_sadd_vs_xml.csv',
        ('Perses', 'xml', 'V+B'): 'perses_sadd_vb_xml.csv',
        ('Perses', 'xml', 'V+S+B'): 'perses_sadd_xml.csv',
    }
    
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    
    for (framework, bench_type, variant), filepath in file_configs.items():
        if not os.path.exists(filepath):
            print("Warning: File not found: {}".format(filepath))
            continue
            
        df = pd.read_csv(filepath)
        print("Loaded {}: {} rows".format(filepath, len(df)))
        
        # Extract benchmark names
        df['benchmark'] = df['Subject'].apply(extract_benchmark_name)
        
        # Filter by benchmark type
        if bench_type == 'c':
            df_filtered = df[df['benchmark'].str.contains('^(clang-|gcc-)', regex=True, na=False)]
        elif bench_type == 'xml':
            df_filtered = df[df['benchmark'].str.contains('^xml-', regex=True, na=False)]
        
        # Store data
        for _, row in df_filtered.iterrows():
            benchmark = row['benchmark']
            data[framework][bench_type][benchmark][variant] = {
                'time': int(row['Time']),
                'size': int(row['Token_remaining']),
                'query': int(row['Query'])
            }
    
    return data

def calculate_geometric_mean_improvement(variant_values, baseline_values):
    """Calculate geometric mean improvement relative to baseline
    Formula: 100 * (1 - GM(variant/baseline)) %
    """
    if len(variant_values) != len(baseline_values):
        return 0.0
    
    ratios = []
    for v, b in zip(variant_values, baseline_values):
        if b > 0:
            ratios.append(v / b)
    
    if not ratios:
        return 0.0
    
    gm_ratio = gmean(ratios)  # FIXED: Use gmean
    return 100.0 * (1.0 - gm_ratio)

def analyze_ablation_results(data):
    """Analyze ablation study results with incremental contributions"""
    
    results = {}
    
    for framework in ['HDD', 'Perses']:
        results[framework] = {}
        
        for bench_type in ['c', 'xml']:
            results[framework][bench_type] = {}
            
            # Get all benchmarks for this combination
            benchmarks = list(data[framework][bench_type].keys())
            benchmarks = [b for b in benchmarks if all(
                variant in data[framework][bench_type][b] 
                for variant in ['V-only', 'V+S', 'V+B', 'V+S+B']
            )]
            
            print("Analyzing {}-{}: {} benchmarks".format(framework, bench_type, len(benchmarks)))
            
            if not benchmarks:
                continue
            
            # For each metric, calculate improvements relative to V-only as baseline
            for metric in ['time', 'size', 'query']:
                # Collect values for each variant
                variant_data = {}
                for variant in ['V-only', 'V+S', 'V+B', 'V+S+B']:
                    variant_data[variant] = [
                        data[framework][bench_type][b][variant][metric] 
                        for b in benchmarks
                    ]
                
                # Use V-only as baseline (uniform baseline)
                baseline_values = variant_data['V-only']
                
                # Calculate improvements for each variant relative to V-only
                improvements = {}
                for variant in ['V-only', 'V+S', 'V+B', 'V+S+B']:
                    improvements[variant] = calculate_geometric_mean_improvement(
                        variant_data[variant], baseline_values
                    )
                
                # Calculate incremental contributions
                s_contribution = improvements['V+S'] - improvements['V-only']
                b_contribution = improvements['V+B'] - improvements['V-only'] 
                synergy = (improvements['V+S+B'] - improvements['V-only'] - 
                          s_contribution - b_contribution)
                
                # Statistical tests (Wilcoxon signed-rank test)
                p_values = {}
                for variant in ['V+S', 'V+B', 'V+S+B']:
                    try:
                        # Test if variant is significantly different from V-only
                        _, p_val = wilcoxon(variant_data[variant], baseline_values)
                        p_values[variant] = p_val
                    except:
                        p_values[variant] = 1.0
                
                results[framework][bench_type][metric] = {
                    'improvements': improvements,
                    'incremental': {
                        'S_contribution': s_contribution,
                        'B_contribution': b_contribution,
                        'synergy': synergy
                    },
                    'p_values': p_values,
                    'sample_size': len(benchmarks)
                }
    
    return results

def generate_ablation_table(results):
    """Generate LaTeX table for ablation study - BOTH FRAMEWORKS WITH P-VALUES"""
    
    latex_lines = []
    latex_lines.append("\\begin{table*}[t]")
    latex_lines.append("\\caption{Ablation study: Component contributions to \\SAddmin. ")
    latex_lines.append("Percentages are geometric means of improvements relative to V-only baseline; ")
    latex_lines.append("$p$-values from two-sided paired Wilcoxon tests. ")
    latex_lines.append("*: $p<0.05$, **: $p<0.01$, ***: $p<0.001$.}")
    latex_lines.append("\\label{tab:ablation}")
    latex_lines.append("\\centering")
    latex_lines.append("\\footnotesize")
    latex_lines.append("\\begin{tabular}{ll|rrr|rrr}")
    latex_lines.append("\\toprule")
    latex_lines.append("& & \\multicolumn{3}{c|}{C Programs} & \\multicolumn{3}{c}{XML Documents} \\\\")
    latex_lines.append("Framework & Variant & Time$\\downarrow$ & Size$\\downarrow$ & Query$\\downarrow$ & Time$\\downarrow$ & Size$\\downarrow$ & Query$\\downarrow$ \\\\")
    latex_lines.append("\\midrule")
    
    for framework_idx, framework in enumerate(['HDD', 'Perses']):
        if framework not in results:
            continue
            
        # Framework header with baseline
        latex_lines.append("\\multirow{{8}}{{*}}{{{0}}} & Baseline (V-only) & 0.0\\% & 0.0\\% & 0.0\\% & 0.0\\% & 0.0\\% & 0.0\\% \\\\".format(framework))
        
        # Variant rows
        for variant in ['V+S', 'V+B', 'V+S+B']:
            row_parts = ["", variant]
            
            for bench_type in ['c', 'xml']:
                if bench_type in results[framework]:
                    for metric in ['time', 'size', 'query']:
                        if metric in results[framework][bench_type]:
                            improvement = results[framework][bench_type][metric]['improvements'][variant]
                            p_val = results[framework][bench_type][metric]['p_values'][variant]
                            
                            # Format with significance markers
                            if p_val < 0.001:
                                marker = "***"
                            elif p_val < 0.01:
                                marker = "**"
                            elif p_val < 0.05:
                                marker = "*"
                            else:
                                marker = ""
                            
                            if variant == 'V+S+B':
                                row_parts.append("\\textbf{{{:.2f}\\%{}}}".format(improvement, marker))
                            else:
                                row_parts.append("{:.2f}\\%{}".format(improvement, marker))
                        else:
                            row_parts.append("--")
                else:
                    row_parts.extend(["--", "--", "--"])
            
            latex_lines.append(" & ".join(row_parts) + " \\\\")
        
        # Incremental contributions for this framework
        latex_lines.append("\\cmidrule(lr){2-8}")
        latex_lines.append("& \\multicolumn{7}{l}{\\textit{Incremental gains (beyond V-only):}}\\\\")
        
        for contrib_type, label in [('S_contribution', 'S contribution'), 
                                   ('B_contribution', 'B contribution'),
                                   ('synergy', 'Synergy (S+B)')]:
            row_parts = ["", label]
            
            for bench_type in ['c', 'xml']:
                if bench_type in results[framework]:
                    for metric in ['time', 'size', 'query']:
                        if metric in results[framework][bench_type]:
                            value = results[framework][bench_type][metric]['incremental'][contrib_type]
                            row_parts.append("{:+.2f}\\%".format(value))
                        else:
                            row_parts.append("--")
                else:
                    row_parts.extend(["--", "--", "--"])
            
            latex_lines.append(" & ".join(row_parts) + " \\\\")
        
        if framework_idx == 0:  # Add midrule between HDD and Perses
            latex_lines.append("\\midrule")
    
    latex_lines.append("\\bottomrule")
    latex_lines.append("\\end{tabular}")
    latex_lines.append("\\end{table*}")
    
    return '\n'.join(latex_lines)

def generate_summary_report(results):
    """Generate human-readable summary report"""
    
    summary_lines = []
    summary_lines.append("=" * 80)
    summary_lines.append("ABLATION STUDY ANALYSIS RESULTS")
    summary_lines.append("=" * 80)
    
    for framework in ['HDD', 'Perses']:
        if framework not in results:
            continue
            
        summary_lines.append("\n{} Framework:".format(framework))
        summary_lines.append("-" * 40)
        
        for bench_type in ['c', 'xml']:
            if bench_type not in results[framework]:
                continue
                
            summary_lines.append("\n  {} Benchmarks:".format(bench_type.upper()))
            
            # Show final results (V+S+B)
            for metric in ['time', 'size', 'query']:
                if metric not in results[framework][bench_type]:
                    continue
                    
                data = results[framework][bench_type][metric]
                full_improvement = data['improvements']['V+S+B']
                p_val = data['p_values']['V+S+B']
                sample_size = data['sample_size']
                
                # Incremental breakdown
                s_contrib = data['incremental']['S_contribution']
                b_contrib = data['incremental']['B_contribution'] 
                synergy = data['incremental']['synergy']
                
                summary_lines.append("    {}: {:.2f}% total improvement (p={:.3e}, n={})".format(
                    metric.capitalize(), full_improvement, p_val, sample_size))
                summary_lines.append("      S contribution: {:+.2f}%".format(s_contrib))
                summary_lines.append("      B contribution: {:+.2f}%".format(b_contrib))
                summary_lines.append("      Synergy: {:+.2f}%".format(synergy))
    
    return '\n'.join(summary_lines)

def main():
    """Main analysis function"""
    print("=== Ablation Study Analysis ===")
    print("Processing 16 CSV files for component contribution analysis...")
    print("FIXED: Using gmean and including both frameworks with p-values")
    print("")
    
    # Load data
    data = load_ablation_data()
    
    # Analyze results
    results = analyze_ablation_results(data)
    
    # Generate outputs
    print("\n" + "="*50)
    print("ANALYSIS COMPLETE")
    print("="*50)
    
    # Summary report
    summary = generate_summary_report(results)
    print(summary)
    
    # Save summary to file
    with open("ablation_analysis_summary.txt", 'w') as f:
        f.write(summary)
    print("\nSummary saved to: ablation_analysis_summary.txt")
    
    # Generate LaTeX table - FIXED VERSION
    latex_table = generate_ablation_table(results)
    if latex_table:
        with open("ablation_table.tex", 'w') as f:
            f.write(latex_table)
        print("FIXED LaTeX table saved to: ablation_table.tex")
        print("- Includes BOTH HDD and Perses frameworks")
        print("- Shows p-values with significance markers")
        print("- Uses gmean for geometric mean calculation")
        
        print("\nLaTeX Table Preview:")
        print("-" * 40)
        print(latex_table[:1500] + "..." if len(latex_table) > 1500 else latex_table)
    
    # Save detailed results as CSV for further analysis
    detailed_results = []
    for framework in results:
        for bench_type in results[framework]:
            for metric in results[framework][bench_type]:
                data = results[framework][bench_type][metric]
                detailed_results.append({
                    'framework': framework,
                    'benchmark_type': bench_type,
                    'metric': metric,
                    'V-only': data['improvements']['V-only'],
                    'V+S': data['improvements']['V+S'],
                    'V+B': data['improvements']['V+B'],
                    'V+S+B': data['improvements']['V+S+B'],
                    'S_contribution': data['incremental']['S_contribution'],
                    'B_contribution': data['incremental']['B_contribution'],
                    'synergy': data['incremental']['synergy'],
                    'p_value_VS': data['p_values']['V+S'],
                    'p_value_VB': data['p_values']['V+B'],
                    'p_value_VSB': data['p_values']['V+S+B'],
                    'sample_size': data['sample_size']
                })
    
    if detailed_results:
        detailed_df = pd.DataFrame(detailed_results)
        detailed_df.to_csv("ablation_detailed_results.csv", index=False)
        print("Detailed results saved to: ablation_detailed_results.csv")

if __name__ == "__main__":
    main()