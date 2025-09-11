#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os
from scipy.stats import wilcoxon, gmean
from collections import defaultdict

def extract_benchmark_name(subject):
    """Extract benchmark name from subject path"""
    return subject.split('/')[-1]

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

def load_algorithm_data(file_configs, data_dir="."):
    """Load data for all algorithms and organize by benchmark"""
    all_data = defaultdict(lambda: defaultdict(dict))
    
    for filepath, framework, algorithm, benchmark_type in file_configs:
        full_path = os.path.join(data_dir, filepath)
        if not os.path.exists(full_path):
            print("Warning: File not found: {}".format(full_path))
            continue
            
        df = pd.read_csv(full_path)
        print("Loaded {}: {} rows".format(filepath, len(df)))
        
        # Extract benchmark names
        df['benchmark'] = df['Subject'].apply(extract_benchmark_name)
        
        # Filter by benchmark type
        if benchmark_type == 'c':
            df_filtered = df[df['benchmark'].str.contains('^(clang-|gcc-)', regex=True, na=False)]
        elif benchmark_type == 'xml':
            df_filtered = df[df['benchmark'].str.contains('^xml-', regex=True, na=False)]
        
        # Store data organized by benchmark
        for _, row in df_filtered.iterrows():
            benchmark = row['benchmark']
            key = "{}_{}".format(framework, algorithm)
            all_data[benchmark_type][benchmark][key] = {
                'time': int(row['Time']),
                'size': int(row['Token_remaining']),
                'query': int(row['Query'])
            }
    
    return all_data

def calculate_improvement_percentage(baseline, improved):
    """Calculate improvement percentage: (baseline - improved) / baseline * 100"""
    if baseline == 0:
        return 0.0
    return (baseline - improved) / baseline * 100.0

def analyze_algorithm_improvements(all_data, algorithm_set, framework, mean_type='arithmetic'):
    """Analyze improvements for a specific algorithm set and framework"""
    results = {}
    
    if algorithm_set == 'ddmin':
        baseline_algs = ['ddmin', 'Wddmin'] 
        improved_alg = 'SAddmin'
        comparison_names = ['SAddmin vs ddmin', 'SAddmin vs Wddmin']
    elif algorithm_set == 'probdd':
        baseline_algs = ['probdd', 'wprobdd']
        improved_alg = 'saprobdd'
        comparison_names = ['SAProbDD vs ProbDD', 'SAProbDD vs WProbDD']
    
    for benchmark_type in ['c', 'xml']:
        results[benchmark_type] = {}
        
        for i, baseline_alg in enumerate(baseline_algs):
            comparison_name = comparison_names[i]
            results[benchmark_type][comparison_name] = {
                'improvements': {'time': [], 'size': [], 'query': []},
                'stats': {}
            }
            
            # Collect improvement data for each benchmark
            baseline_key = "{}_{}".format(framework, baseline_alg)
            improved_key = "{}_{}".format(framework, improved_alg)
            
            benchmarks = all_data[benchmark_type].keys()
            
            for benchmark in benchmarks:
                if baseline_key in all_data[benchmark_type][benchmark] and \
                   improved_key in all_data[benchmark_type][benchmark]:
                    
                    baseline_data = all_data[benchmark_type][benchmark][baseline_key]
                    improved_data = all_data[benchmark_type][benchmark][improved_key]
                    
                    for metric in ['time', 'size', 'query']:
                        improvement = calculate_improvement_percentage(
                            baseline_data[metric], improved_data[metric]
                        )
                        results[benchmark_type][comparison_name]['improvements'][metric].append(improvement)
            
            # Calculate statistics
            for metric in ['time', 'size', 'query']:
                improvements = results[benchmark_type][comparison_name]['improvements'][metric]
                if improvements:
                    # Calculate mean based on the specified type
                    if mean_type == 'geometric':
                        mean_improvement = calculate_geometric_mean_improvement(improvements)
                    else: # Default to arithmetic
                        mean_improvement = np.mean(improvements)
                    
                    # Wilcoxon signed-rank test
                    try:
                        if len(improvements) >= 5 and not all(x == 0 for x in improvements):
                            _, p_value = wilcoxon(improvements)
                        else:
                            p_value = 1.0
                    except:
                        p_value = 1.0
                    
                    results[benchmark_type][comparison_name]['stats'][metric] = {
                        'mean_improvement': mean_improvement,
                        'p_value': p_value,
                        'count': len(improvements)
                    }
                else:
                    results[benchmark_type][comparison_name]['stats'][metric] = {
                        'mean_improvement': 0.0,
                        'p_value': 1.0,
                        'count': 0
                    }
    
    return results

def format_p_value(p_value):
    """Format p-value in scientific notation if very small"""
    if p_value < 0.001:
        return "{:.2e}".format(p_value)
    else:
        return "{:.3f}".format(p_value)

def generate_paper_style_summary(results, algorithm_set, framework):
    """Generate paper-style summary text"""
    summary_lines = []
    summary_lines.append("=" * 60)
    summary_lines.append("{} Framework - {} Algorithm Set".format(framework, algorithm_set.upper()))
    summary_lines.append("=" * 60)
    
    if algorithm_set == 'ddmin':
        improved_name = 'SAddmin'
        baseline_names = ['ddmin', 'Wddmin']
    else:
        improved_name = 'SAProbDD'
        baseline_names = ['ProbDD', 'WProbDD']
    
    for i, baseline_name in enumerate(baseline_names):
        comparison_key = list(results['c'].keys())[i]
        
        summary_lines.append("\n{} vs {} Comparison:".format(improved_name, baseline_name))
        summary_lines.append("-" * 40)
        
        c_stats = results['c'][comparison_key]['stats']
        xml_stats = results['xml'][comparison_key]['stats']
        
        metric_overall_p = {}
        for metric in ['time', 'size', 'query']:
            c_improvements = results['c'][comparison_key]['improvements'][metric]
            xml_improvements = results['xml'][comparison_key]['improvements'][metric]
            all_metric_improvements = c_improvements + xml_improvements
            
            try:
                if len(all_metric_improvements) >= 5 and not all(x == 0 for x in all_metric_improvements):
                    _, metric_p = wilcoxon(all_metric_improvements)
                else:
                    metric_p = 1.0
            except:
                metric_p = 1.0
            metric_overall_p[metric] = metric_p
        
        time_c = c_stats['time']['mean_improvement']
        time_xml = xml_stats['time']['mean_improvement']
        size_c = c_stats['size']['mean_improvement']
        size_xml = xml_stats['size']['mean_improvement']
        query_c = c_stats['query']['mean_improvement']
        query_xml = xml_stats['query']['mean_improvement']
        
        # Generate summary text
        summary_lines.append(
            "Time: {}{} generates {:.2f}% and {:.2f}% faster results than {}{} "
            "on C and XML benchmarks, respectively, with overall p-value of {}.".format(
                framework, improved_name[0].lower(), time_c, time_xml, 
                framework, baseline_name[0].lower(), format_p_value(metric_overall_p['time'])
            )
        )
        summary_lines.append(
            "Size: {}{} generates {:.2f}% and {:.2f}% smaller results than {}{} "
            "on C and XML benchmarks, respectively, with overall p-value of {}.".format(
                framework, improved_name[0].lower(), size_c, size_xml, 
                framework, baseline_name[0].lower(), format_p_value(metric_overall_p['size'])
            )
        )
        summary_lines.append(
            "Query: {}{} generates {:.2f}% and {:.2f}% fewer queries than {}{} "
            "on C and XML benchmarks, respectively, with overall p-value of {}.".format(
                framework, improved_name[0].lower(), query_c, query_xml, 
                framework, baseline_name[0].lower(), format_p_value(metric_overall_p['query'])
            )
        )
        
        # Detailed breakdown
        summary_lines.append("\nDetailed Results:")
        summary_lines.append("  C Benchmarks:")
        summary_lines.append("    Time: {:.2f}% improvement (p={})".format(
            time_c, format_p_value(c_stats['time']['p_value'])))
        summary_lines.append("    Size: {:.2f}% improvement (p={})".format(
            size_c, format_p_value(c_stats['size']['p_value'])))
        summary_lines.append("    Query: {:.2f}% improvement (p={})".format(
            query_c, format_p_value(c_stats['query']['p_value'])))
        
        summary_lines.append("  XML Benchmarks:")
        summary_lines.append("    Time: {:.2f}% improvement (p={})".format(
            time_xml, format_p_value(xml_stats['time']['p_value'])))
        summary_lines.append("    Size: {:.2f}% improvement (p={})".format(
            size_xml, format_p_value(xml_stats['size']['p_value'])))
        summary_lines.append("    Query: {:.2f}% improvement (p={})".format(
            xml_stats['query']['mean_improvement'], format_p_value(xml_stats['query']['p_value'])))
    
    return '\n'.join(summary_lines)

def main():
    """Main analysis function"""
    print("=== Algorithm Improvement Analysis ===")
    print("Analyzing improvements and statistical significance...")
    print("")
    
    ddmin_configs = [
        ("hdd_ddmin_c.csv", "HDD", "ddmin", "c"),
        ("hdd_ddmin_xml.csv", "HDD", "ddmin", "xml"),
        ("hdd_wdd_c.csv", "HDD", "Wddmin", "c"),
        ("hdd_wdd_xml.csv", "HDD", "Wddmin", "xml"),
        ("hdd_sadd_c.csv", "HDD", "SAddmin", "c"),
        ("hdd_sadd_xml.csv", "HDD", "SAddmin", "xml"),
        ("perses_ddmin_c.csv", "Perses", "ddmin", "c"),
        ("perses_ddmin_xml.csv", "Perses", "ddmin", "xml"),
        ("perses_wdd_c.csv", "Perses", "Wddmin", "c"),
        ("perses_wdd_xml.csv", "Perses", "Wddmin", "xml"),
        ("perses_sadd_c.csv", "Perses", "SAddmin", "c"),
        ("perses_sadd_xml.csv", "Perses", "SAddmin", "xml"),
    ]
    
    probdd_configs = [
        ("hdd_probdd_c.csv", "HDD", "probdd", "c"),
        ("hdd_probdd_xml.csv", "HDD", "probdd", "xml"),
        ("hdd_wprobdd_c.csv", "HDD", "wprobdd", "c"),
        ("hdd_wprobdd_xml.csv", "HDD", "wprobdd", "xml"),
        ("hdd_saprobdd_c.csv", "HDD", "saprobdd", "c"),
        ("hdd_saprobdd_xml.csv", "HDD", "saprobdd", "xml"),
        ("perses_probdd_c.csv", "Perses", "probdd", "c"),
        ("perses_probdd_xml.csv", "Perses", "probdd", "xml"),
        ("perses_wprobdd_c.csv", "Perses", "wprobdd", "c"),
        ("perses_wprobdd_xml.csv", "Perses", "wprobdd", "xml"),
        ("perses_saprobdd_c.csv", "Perses", "saprobdd", "c"),
        ("perses_saprobdd_xml.csv", "Perses", "saprobdd", "xml"),
    ]
    
    # Loop over both mean types to generate two separate reports
    for mean_type in ['arithmetic', 'geometric']:
    # for mean_type in ['geometric']:
        print("\n" + "="*80)
        print(f"CALCULATING USING {mean_type.upper()} MEAN")
        print("="*80 + "\n")
        
        all_summaries = []
        
        for algorithm_set, configs in [('ddmin', ddmin_configs), ('probdd', probdd_configs)]:
            print("Loading data for {} algorithm set...".format(algorithm_set))
            all_data = load_algorithm_data(configs)
            
            for framework in ['HDD', 'Perses']:
                print("Analyzing {} framework...".format(framework))
                results = analyze_algorithm_improvements(all_data, algorithm_set, framework, mean_type=mean_type)
                summary = generate_paper_style_summary(results, algorithm_set, framework)
                all_summaries.append(summary)
                print(summary)
                print("\n")
        
        if mean_type == 'geometric':
            output_filename = "improvement_analysis_results_geometric.txt"
        else:
            output_filename = "improvement_analysis_results.txt"
            
        with open(output_filename, 'w') as f:
            f.write(f"Algorithm Improvement Analysis Results ({mean_type.capitalize()} Mean)\n")
            f.write("Generated automatically for paper writing\n")
            f.write("=" * 80 + "\n\n")
            f.write('\n\n'.join(all_summaries))
        
        print(f"Analysis with {mean_type} mean complete! Results saved to {output_filename}")

if __name__ == "__main__":
    main()
