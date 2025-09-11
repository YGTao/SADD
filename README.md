# Artifact for "Structure-Aware Delta Debugging with Geometric--Information Weights"

## Introduction

Thank you for evaluating this artifact.

To evaluate this artifact, a Linux machine with [docker](https://docs.docker.com/get-docker/) is needed.

## Notes

- All the experiments take very long time to finish, so it is recommended to use tools like screen and tmux to manage sessions if the experiments are run on remote server.
- The experiments involving ProbDD in this paper were repeated 5 times to mitigate the randomness of ProbDD algorithms.

## Docker Environment Setup

1. If docker is not installed, install it by following the [instructions](https://docs.docker.com/get-docker/).

2. Install the docker image.

   ```shell
   docker pull 
   ```

3. Start a container

   ```shell
   docker container run --cap-add SYS_PTRACE --interactive --tty 
   # for all operations in docker, use 'sudo' when meeting permission denied issues, password is 123
   cd /tmp/WeightDD/
   ```

## Benchmark Suites

Under the root directory of the project, the benchmarks are located in:

- `./c_benchmarks`: benchmark-C which consists of 32 C programs;
- `./xml_benchmarks`: benchmark-XML which consists of 30 XML files.

## Implementation

We implemented all the related algorithms in this paper based on [Perses](https://github.com/uw-pluverse/perses). 

To run the evaluation, we need perses (including Perses, HDD, and all related algorithms in this paper). For convenience , we have pre-built the tools and put them under `/tmp/binaries/` in the docker image (also put in the `tools` directory of this repo. Three JAR files are required fo evaluation:

```
> tree /tmp/binaries/
/tmp/binaries/
|-- perses_deploy.jar
|-- perses_stat_deploy.jar
|-- token_counter_deploy.jar
|-- volume-S-B-0.jar
|-- volume-S-B-1.jar
|-- volume-S0-B1.jar
`-- volume-S1-B0.jar
```


## RQ1: $SA_{ddmin}$ v.s. $ddmin$

```shell
# For C Benchmarks:
./run_exp_parallel_c.py -s c_benchmarks/* -r perses_ddmin perses_sadd hdd_ddmin hdd_sadd -o result_sadd_c -j 8
# For XML Benchmarks:
./run_exp_parallel_xml.py -s xml_benchmarks/xml-* -r perses_ddmin perses_sadd hdd_ddmin hdd_sadd -o result_sadd_xml -j 8
# Run convert_result_to_csv.py to export the results into csv files, use '-h' to see usage notes
./convert_result_to_csv.py -d result_sadd_c/hdd_ddmin_0/*  -o hdd_ddmin_c.csv
./convert_result_to_csv.py -d result_sadd_c/hdd_sadd_0/*  -o hdd_sadd_c.csv
./convert_result_to_csv.py -d result_sadd_c/perses_ddmin_0/*  -o perses_ddmin_c.csv
./convert_result_to_csv.py -d result_sadd_c/perses_sadd_0/*  -o perses_sadd_c.csv
./convert_result_to_csv.py -d result_sadd_xml/hdd_ddmin_0/*  -o hdd_ddmin_xml.csv
./convert_result_to_csv.py -d result_sadd_xml/hdd_sadd_0/*  -o hdd_sadd_xml.csv
./convert_result_to_csv.py -d result_sadd_xml/perses_ddmin_0/*  -o perses_ddmin_xml.csv
./convert_result_to_csv.py -d result_sadd_xml/perses_sadd_0/*  -o perses_sadd_xml.csv
```

## RQ2: $SA_{ProbDD}$ v.s. $ProbDD$

```shell
# For C Benchmarks:
./run_exp_parallel_c.py -s c_benchmarks/* -r perses_probdd perses_saprobdd hdd_probdd hdd_saprobdd -o result_saprobdd_c -j 8
# For XML Benchmarks:
./run_exp_parallel_xml.py -s xml_benchmarks/xml-* -r perses_probdd perses_saprobdd hdd_probdd hdd_saprobdd -o result_saprobdd_xml -j 8
# Run convert_result_to_csv.py to export the results into csv files, use '-h' to see usage notes
./convert_result_to_csv.py -d result_saprobdd_c/hdd_probdd_0/*  -o hdd_probdd_c.csv
./convert_result_to_csv.py -d result_saprobdd_c/hdd_saprobdd_0/*  -o hdd_saprobdd_c.csv
./convert_result_to_csv.py -d result_saprobdd_c/perses_probdd_0/* -o perses_probdd_c.csv
./convert_result_to_csv.py -d result_saprobdd_c/perses_saprobdd_0/* -o perses_saprobdd_c.csv
./convert_result_to_csv.py -d result_saprobdd_xml/hdd_probdd_0/*  -o hdd_probdd_xml.csv
./convert_result_to_csv.py -d result_saprobdd_xml/hdd_saprobdd_0/*  -o hdd_saprobdd_xml.csv
./convert_result_to_csv.py -d result_saprobdd_xml/perses_probdd_0/* -o perses_probdd_xml.csv
./convert_result_to_csv.py -d result_saprobdd_xml/perses_saprobdd_0/* -o perses_saprobdd_xml.csv
```

## RQ3: $SA_{ddmin}$ v.s. $W_{ddmin}$ and $SA_{ProbDD}$ v.s. $W_{ProbDD}$

```shell
# For C Benchmarks:
./run_exp_parallel_c.py -s c_benchmarks/* -r perses_sadd perses_wdd perses_saprobdd perses_wprobdd hdd_sadd hdd_wdd hdd_saprobdd hdd_wprobdd -o result_comparison_c -j 20
# For XML Benchmarks:
./run_exp_parallel_xml.py -s xml_benchmarks/xml-* -r perses_sadd perses_wdd perses_saprobdd perses_wprobdd hdd_sadd hdd_wdd hdd_saprobdd hdd_wprobdd -o result_comparison_xml -j 20
# Run convert_result_to_csv.py to export the results into csv files, use '-h' to see usage notes
./convert_result_to_csv.py -d result_comparison_c/hdd_sadd_0/*  -o hdd_sadd_c.csv
./convert_result_to_csv.py -d result_comparison_c/hdd_wdd_0/*  -o hdd_wdd_c.csv
./convert_result_to_csv.py -d result_comparison_c/hdd_saprobdd_0/*  -o hdd_saprobdd_c.csv
./convert_result_to_csv.py -d result_comparison_c/hdd_wprobdd_0/*  -o hdd_wprobdd_c.csv
./convert_result_to_csv.py -d result_comparison_c/perses_sadd_0/* -o perses_sadd_c.csv
./convert_result_to_csv.py -d result_comparison_c/perses_wdd_0/* -o perses_wdd_c.csv
./convert_result_to_csv.py -d result_comparison_c/perses_saprobdd_0/* -o perses_saprobdd_c.csv
./convert_result_to_csv.py -d result_comparison_c/perses_wprobdd_0/* -o perses_wprobdd_c.csv
./convert_result_to_csv.py -d result_comparison_xml/hdd_sadd_0/*  -o hdd_sadd_xml.csv
./convert_result_to_csv.py -d result_comparison_xml/hdd_wdd_0/*  -o hdd_wdd_xml.csv
./convert_result_to_csv.py -d result_comparison_xml/hdd_saprobdd_0/*  -o hdd_saprobdd_xml.csv
./convert_result_to_csv.py -d result_comparison_xml/hdd_wprobdd_0/*  -o hdd_wprobdd_xml.csv
./convert_result_to_csv.py -d result_comparison_xml/perses_sadd_0/* -o perses_sadd_xml.csv
./convert_result_to_csv.py -d result_comparison_xml/perses_wdd_0/* -o perses_wdd_xml.csv
./convert_result_to_csv.py -d result_comparison_xml/perses_saprobdd_0/* -o perses_saprobdd_xml.csv
./convert_result_to_csv.py -d result_comparison_xml/perses_wprobdd_0/* -o perses_wprobdd_xml.csv



## Evaluation Results

**RQ4**: The raw data of the weights information during delta debugging are put in `results_rq1`, and the correlation values are exported to the csv files under `results_rq1_csv`. 

From this figure, the probability of elements being deleted is negatively correlated with their weights in ddmin executions in both HDD and Perses, to varying degrees. This validation provides a solid foundation for the design of $W_{ddmin}$.