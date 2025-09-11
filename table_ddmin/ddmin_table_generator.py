#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import pandas as pd
import numpy as np
import os
from math import log, exp

def extract_benchmark_name(subject):
    """Extract benchmark name from subject path"""
    return subject.split('/')[-1]

def geometric_mean(values):
    """Calculate geometric mean, handling zero values"""
    values = [v for v in values if v > 0]  # Exclude zero values
    if not values:
        return 0
    return exp(sum(log(v) for v in values) / len(values))

def process_csv_file(filepath, framework, algorithm, benchmark_type):
    """Process a single CSV file - auto-extract all benchmarks"""
    try:
        df = pd.read_csv(filepath)
        print("Reading {}: {} rows".format(filepath, len(df)))
        
        # Extract benchmark names from Subject column
        df['benchmark'] = df['Subject'].apply(extract_benchmark_name)
        
        # Auto-filter by benchmark type based on benchmark name patterns
        if benchmark_type == 'c':
            # Filter for clang-* and gcc-* benchmarks
            df_filtered = df[df['benchmark'].str.contains('^(clang-|gcc-)', regex=True, na=False)]
        elif benchmark_type == 'xml':
            # Filter for xml-* benchmarks
            df_filtered = df[df['benchmark'].str.contains('^xml-', regex=True, na=False)]
        else:
            raise ValueError("Unknown benchmark type: {}".format(benchmark_type))
        
        # Get all unique benchmarks from this file
        target_benchmarks = sorted(df_filtered['benchmark'].unique())
        print("Found {} {} benchmarks: {}".format(len(target_benchmarks), benchmark_type, target_benchmarks[:5]))
        if len(target_benchmarks) > 5:
            print("... and {} more".format(len(target_benchmarks) - 5))
        
        # Prepare result data for all found benchmarks
        results = []
        for benchmark in target_benchmarks:
            bench_data = df_filtered[df_filtered['benchmark'] == benchmark]
            if not bench_data.empty:
                row = bench_data.iloc[0]
                results.append({
                    'benchmark': benchmark,
                    'framework': framework,
                    'algorithm': algorithm,
                    'benchmark_type': benchmark_type,
                    'time': int(row['Time']),
                    'size': int(row['Token_remaining']),
                    'query': int(row['Query'])  # Read real Query values from file
                })
            else:
                # If no data for benchmark, fill with zeros
                results.append({
                    'benchmark': benchmark,
                    'framework': framework, 
                    'algorithm': algorithm,
                    'benchmark_type': benchmark_type,
                    'time': 0,
                    'size': 0,
                    'query': 0
                })
        
        return results
        
    except Exception as e:
        print("Error processing file {}: {}".format(filepath, str(e)))
        return []

def get_all_benchmarks(all_results):
    """Extract all unique benchmarks and separate by type"""
    df = pd.DataFrame(all_results)
    all_unique_benchmarks = sorted(df['benchmark'].unique())
    
    # Separate by type based on naming pattern
    c_benchmarks = sorted([b for b in all_unique_benchmarks if b.startswith(('clang-', 'gcc-'))])
    xml_benchmarks = sorted([b for b in all_unique_benchmarks if b.startswith('xml-')])
    
    return c_benchmarks, xml_benchmarks, all_unique_benchmarks

def calculate_means(all_results):
    """Calculate arithmetic and geometric means for all benchmarks"""
    df = pd.DataFrame(all_results)
    
    means = {}
    frameworks = ['HDD', 'Perses']
    algorithms = ['ddmin', 'Wddmin', 'SAddmin']
    benchmark_types = ['c', 'xml']
    
    for framework in frameworks:
        for algorithm in algorithms:
            for bench_type in benchmark_types:
                # Filter data
                subset = df[
                    (df['framework'] == framework) & 
                    (df['algorithm'] == algorithm) & 
                    (df['benchmark_type'] == bench_type)
                ]
                
                if not subset.empty:
                    # Arithmetic mean
                    arith_mean = {
                        'time': int(subset['time'].mean()),
                        'size': int(subset['size'].mean()),
                        'query': int(subset['query'].mean())
                    }
                    
                    # Geometric mean
                    geom_mean = {
                        'time': int(geometric_mean(subset['time'].tolist())),
                        'size': int(geometric_mean(subset['size'].tolist())),
                        'query': int(geometric_mean(subset['query'].tolist()))
                    }
                    
                    key = "{}_{}_{}" .format(framework, algorithm, bench_type)
                    means[key] = {
                        'arithmetic': arith_mean,
                        'geometric': geom_mean
                    }
    
    return means

def generate_formatted_benchmark_row(benchmark, data_lookup, frameworks, algorithms):
    """Generate a single benchmark row with bold formatting"""
    
    # Collect all data for this benchmark
    benchmark_data = {}
    for framework in frameworks:
        benchmark_data[framework] = {}
        for algorithm in algorithms:
            key = "{}_{}_{}".format(framework, algorithm, benchmark)
            if key in data_lookup:
                row = data_lookup[key]
                benchmark_data[framework][algorithm] = {
                    'time': int(row['time']),
                    'size': int(row['size']),
                    'query': int(row['query'])
                }
            else:
                benchmark_data[framework][algorithm] = {'time': 0, 'size': 0, 'query': 0}
    
    # Format row with bold detection (same logic as working debug version)
    row_parts = ["    {:<25}".format(benchmark)]
    
    for framework in frameworks:
        # Get values for this framework
        times = [benchmark_data[framework][alg]['time'] for alg in algorithms]
        sizes = [benchmark_data[framework][alg]['size'] for alg in algorithms]
        queries = [benchmark_data[framework][alg]['query'] for alg in algorithms]
        
        # Find minimums (same logic as working version)
        time_min = min([t for t in times if t > 0]) if any(t > 0 for t in times) else 0
        size_min = min([s for s in sizes if s > 0]) if any(s > 0 for s in sizes) else 0
        query_min = min([q for q in queries if q > 0]) if any(q > 0 for q in queries) else 0
        
        # Format each algorithm's values
        for i, algorithm in enumerate(algorithms):
            time_val = times[i]
            size_val = sizes[i]
            query_val = queries[i]
            
            # Time
            if time_val == time_min and time_val > 0:
                time_str = "\\textbf{{{:,}}}".format(time_val)
            else:
                time_str = "{:,}".format(time_val) if time_val > 0 else "0"
            
            # Size  
            if size_val == size_min and size_val > 0:
                size_str = "\\textbf{{{}}}".format(size_val)
            else:
                size_str = "{}".format(size_val) if size_val > 0 else "0"
            
            # Query
            if query_val == query_min and query_val > 0:
                query_str = "\\textbf{{{}}}".format(query_val)
            else:
                query_str = "{}".format(query_val) if query_val > 0 else "0"
            
            row_parts.extend([" & {:>14}".format(time_str), " & {:>14}".format(size_str), " & {:>14}".format(query_str)])
    
    return "".join(row_parts) + " \\\\"

def generate_formatted_mean_row(label, mean_data, frameworks, algorithms):
    """Generate a mean row with bold formatting"""
    
    row_parts = ["    {:<25}".format(label)]
    
    for framework in frameworks:
        # Get values for this framework
        times = []
        sizes = []
        queries = []
        
        for algorithm in algorithms:
            key = "{}_{}".format(framework, algorithm)
            if key in mean_data:
                times.append(mean_data[key]['time'])
                sizes.append(mean_data[key]['size'])
                queries.append(mean_data[key]['query'])
            else:
                times.append(0)
                sizes.append(0)
                queries.append(0)
        
        # Find minimums
        time_min = min([t for t in times if t > 0]) if any(t > 0 for t in times) else 0
        size_min = min([s for s in sizes if s > 0]) if any(s > 0 for s in sizes) else 0
        query_min = min([q for q in queries if q > 0]) if any(q > 0 for q in queries) else 0
        
        # Format each algorithm's values
        for i, algorithm in enumerate(algorithms):
            time_val = times[i]
            size_val = sizes[i]
            query_val = queries[i]
            
            # Time
            if time_val == time_min and time_val > 0:
                time_str = "\\textbf{{{:,}}}".format(time_val)
            else:
                time_str = "{:,}".format(time_val) if time_val > 0 else "0"
            
            # Size  
            if size_val == size_min and size_val > 0:
                size_str = "\\textbf{{{}}}".format(size_val)
            else:
                size_str = "{}".format(size_val) if size_val > 0 else "0"
            
            # Query
            if query_val == query_min and query_val > 0:
                query_str = "\\textbf{{{}}}".format(query_val)
            else:
                query_str = "{}".format(query_val) if query_val > 0 else "0"
            
            row_parts.extend([" & {:>14}".format(time_str), " & {:>14}".format(size_str), " & {:>14}".format(query_str)])
    
    return "".join(row_parts) + " \\\\"

def generate_latex_table(all_results):
    """Generate complete LaTeX table with all benchmarks and proper bolding"""
    
    print("\nGenerating FINAL LaTeX table with bold formatting...")
    
    df = pd.DataFrame(all_results)
    c_benchmarks, xml_benchmarks, _ = get_all_benchmarks(all_results)
    all_benchmarks_sorted = c_benchmarks + xml_benchmarks
    
    print("Total benchmarks: {}".format(len(all_benchmarks_sorted)))
    print("C benchmarks: {}".format(len(c_benchmarks)))
    print("XML benchmarks: {}".format(len(xml_benchmarks)))
    
    frameworks = ['HDD', 'Perses']
    algorithms = ['ddmin', 'Wddmin', 'SAddmin']
    
    # Create data lookup
    data_lookup = {}
    for _, row in df.iterrows():
        key = "{}_{}_{}".format(row['framework'], row['algorithm'], row['benchmark'])
        data_lookup[key] = row
    
    # LaTeX header (full version)
    latex_lines = [
        "\\begin{table*}[t!]",
        "    \\centering",
        "    \\setlength{\\tabcolsep}{5pt}",
        "    \\renewcommand{\\arraystretch}{0.92}",
        "    \\caption{",
        "        Results of \\ddmin variants across \\HDD and \\Perses frameworks on all benchmarks.",
        "        Better results in each comparison are highlighted in bold.",
        "    }",
        "    \\label{tab:evaluation-ddmin-variants}",
        "    \\resizebox{0.98\\textwidth}{!}{%",
        "    \\begin{tabular}{@{}l>{\\columncolor[HTML]{CFE8F6}}c>{\\columncolor[HTML]{DFF2FA}}c>{\\columncolor[HTML]{EFF7FD}}c>{\\columncolor[HTML]{CFE8F6}}c>{\\columncolor[HTML]{DFF2FA}}c>{\\columncolor[HTML]{EFF7FD}}c>{\\columncolor[HTML]{CFE8F6}}c>{\\columncolor[HTML]{DFF2FA}}c>{\\columncolor[HTML]{EFF7FD}}c>{\\columncolor[HTML]{CFE8F6}}c>{\\columncolor[HTML]{DFF2FA}}c>{\\columncolor[HTML]{EFF7FD}}c>{\\columncolor[HTML]{CFE8F6}}c>{\\columncolor[HTML]{DFF2FA}}c>{\\columncolor[HTML]{EFF7FD}}c>{\\columncolor[HTML]{CFE8F6}}c>{\\columncolor[HTML]{DFF2FA}}c>{\\columncolor[HTML]{EFF7FD}}c@{}}",
        "    \\toprule",
        "                                & \\multicolumn{9}{c}{\\HDD}                                                                                                                 & \\multicolumn{9}{c}{\\Perses}                                                                                                             \\\\ ",
        "    \\cmidrule(lr){2-10} \\cmidrule(lr){11-19}",
        "                                & \\multicolumn{3}{c}{\\ddmin}                 & \\multicolumn{3}{c}{\\Wddmin}                & \\multicolumn{3}{c}{\\SAddmin}               & \\multicolumn{3}{c}{\\ddmin}                 & \\multicolumn{3}{c}{\\Wddmin}                & \\multicolumn{3}{c}{\\SAddmin}               \\\\ ",
        "    \\cmidrule(lr){2-4} \\cmidrule(lr){5-7} \\cmidrule(lr){8-10} \\cmidrule(lr){11-13} \\cmidrule(lr){14-16} \\cmidrule(lr){17-19}",
        "    \\multirow{-3}{*}{Benchmark} & T(s)           & S(\\#)         & Q(\\#)         & T(s)            & S(\\#)           & Q(\\#)         & T(s)            & S(\\#)           & Q(\\#)         & T(s)           & S(\\#)         & Q(\\#)         & T(s)            & S(\\#)           & Q(\\#)         & T(s)            & S(\\#)           & Q(\\#)         \\\\ ",
        "    \\midrule"
    ]
    
    # Generate ALL benchmark rows with bold formatting
    for benchmark in all_benchmarks_sorted:
        row = generate_formatted_benchmark_row(benchmark, data_lookup, frameworks, algorithms)
        latex_lines.append(row)
    
    # Generate Mean rows with bold formatting
    latex_lines.append("    \\midrule")
    means = calculate_means(all_results)
    
    for bench_type, label in [('c', 'Mean (C)'), ('xml', 'Mean (XML)')]:
        mean_data = {}
        for framework in frameworks:
            for algorithm in algorithms:
                key = "{}_{}_{}" .format(framework, algorithm, bench_type)
                framework_alg_key = "{}_{}".format(framework, algorithm)
                if key in means:
                    mean_data[framework_alg_key] = means[key]['geometric']
                else:
                    mean_data[framework_alg_key] = {'time': 0, 'size': 0, 'query': 0}
        
        mean_row = generate_formatted_mean_row(label, mean_data, frameworks, algorithms)
        latex_lines.append(mean_row)
    
    # Table end
    latex_lines.extend([
        "    \\bottomrule",
        "    \\end{tabular}%",
        "    }",
        "\\end{table*}"
    ])
    
    return '\n'.join(latex_lines)

def generate_integrated_csv(all_results):
    """Generate integrated CSV file with all benchmarks"""
    df = pd.DataFrame(all_results)
    
    # Reorder columns
    columns_order = ['benchmark', 'benchmark_type', 'framework', 'algorithm', 'time', 'size', 'query']
    df = df[columns_order]
    
    # Sort by benchmark type first, then by benchmark name
    df['sort_key'] = df.apply(lambda row: (
        0 if row['benchmark_type'] == 'c' else 1,  # C benchmarks first
        row['benchmark']  # Then alphabetically by benchmark name
    ), axis=1)
    
    df = df.sort_values(['sort_key', 'framework', 'algorithm']).drop('sort_key', axis=1)
    
    return df

def generate_means_csv(all_results):
    """Generate means CSV file"""
    means = calculate_means(all_results)
    
    means_data = []
    for key, values in means.items():
        framework, algorithm, bench_type = key.split('_')
        
        # Arithmetic mean
        means_data.append({
            'benchmark_type': bench_type,
            'framework': framework,
            'algorithm': algorithm,
            'mean_type': 'arithmetic',
            'time': values['arithmetic']['time'],
            'size': values['arithmetic']['size'],
            'query': values['arithmetic']['query']
        })
        
        # Geometric mean
        means_data.append({
            'benchmark_type': bench_type,
            'framework': framework,
            'algorithm': algorithm,
            'mean_type': 'geometric',
            'time': values['geometric']['time'],
            'size': values['geometric']['size'],
            'query': values['geometric']['query']
        })
    
    return pd.DataFrame(means_data)

def main():
    """Main function"""
    print("=== FINAL Table Generator (Based on Working Bold Logic) ===")
    
    # Configure 12 files
    file_configs = [
        # Format: (file_path, framework_name, algorithm_name, benchmark_type)
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
    
    all_results = []
    
    # Process each file
    for filepath, framework, algorithm, bench_type in file_configs:
        if os.path.exists(filepath):
            results = process_csv_file(filepath, framework, algorithm, bench_type)
            all_results.extend(results)
            print("Successfully processed: {} ({} benchmarks)".format(filepath, len(results)))
        else:
            print("File not found: {}".format(filepath))
    
    if not all_results:
        print("No data found, please check file paths and formats")
        return
    
    print("\nTotal records processed: {}".format(len(all_results)))
    
    # Generate FINAL LaTeX table
    latex_code = generate_latex_table(all_results)
    with open("ddmin_table.tex", 'w', encoding='utf-8') as f:
        f.write(latex_code)
    print("\nFINAL LaTeX table saved to: ddmin_table.tex")
    
    # Generate CSV files
    integrated_df = generate_integrated_csv(all_results)
    integrated_df.to_csv("integrated_results.csv", index=False)
    print("Integrated data saved to: integrated_results.csv")
    
    means_df = generate_means_csv(all_results)
    means_df.to_csv("means_results.csv", index=False)
    print("Means data saved to: means_results.csv")
    
    # Statistics
    c_benchmarks, xml_benchmarks, _ = get_all_benchmarks(all_results)
    print("\n=== Final Statistics ===")
    print("Total unique benchmarks: {}".format(len(c_benchmarks) + len(xml_benchmarks)))
    print("C benchmarks: {}".format(len(c_benchmarks)))
    print("XML benchmarks: {}".format(len(xml_benchmarks)))
    print("Processed files: 12/12")

if __name__ == "__main__":
    main()