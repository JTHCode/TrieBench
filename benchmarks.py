import random
import copy
import os
import pandas as pd
import datetime
from components.work_loads import WorkLoad
from tries.compressed_trie import CompressedTrie
from tries.standard_trie import Trie
from components.metric_analyzers import MetricAnalyzer


###========= CONFIGURATION KNOBS =========###

RUNS_PER_TEST = 20
SEED = None # set to None to generate random seeds
WORK_LOAD_SIZE = 100_000
DELETE_AMOUNT = WORK_LOAD_SIZE
WORK_LOAD_TYPE = "words"  # "words", "urls", "ips"
if WORK_LOAD_TYPE == "words":
    PREFIX_FREQUENCY = 0.0  # 0.0 -> 0.999...


###========= WORK LOAD GENERATION =========###

def generate_work_load():
    global SEED
    if SEED: 
        SEED += 2
    else:
        SEED = random.randint(0, 1000000)
    work_load_generator = WorkLoad(SEED)
    if WORK_LOAD_TYPE == "words":
        work_load = work_load_generator.words(WORK_LOAD_SIZE, PREFIX_FREQUENCY)
    elif WORK_LOAD_TYPE == "urls":
        work_load = work_load_generator.urls(WORK_LOAD_SIZE)
    elif WORK_LOAD_TYPE == "ips":
        work_load = work_load_generator.ips(WORK_LOAD_SIZE)
    return work_load


###========= TRIE CREATION/CONFIGURATION =========###
standard_trie = Trie()
compressed_trie = CompressedTrie()


###========= BENCHMARK RESULT FORMATTING =========###
output_format = {   'work_load_size': WORK_LOAD_SIZE,
                    'work_load_type': WORK_LOAD_TYPE,
                    'run_number': [],
                    'insert_time': [],
                    'delete_time': [],
                    'enumerate_prefix_time': [],
                    'exact_search_time': [],
                    'prefix_search_time': [],
                    'full_traversal_time': [],
                    'memory_usage': [],
                    'node_count': [],
                    'avg_branching_factor': [],
                    'prefix_frequency': PREFIX_FREQUENCY if WORK_LOAD_TYPE == "words" else None,
                    'seeds': [],                  
}

compressed_trie_results = copy.deepcopy(output_format)
standard_trie_results = copy.deepcopy(output_format)


###========= BENCHMARKING =========###

for run in range(RUNS_PER_TEST):
    work_load = generate_work_load()
    CT_TEST = MetricAnalyzer(compressed_trie, work_load, SEED)
    ST_TEST = MetricAnalyzer(standard_trie, work_load, SEED)
    compressed_trie_results['run_number'].append(run)
    standard_trie_results['run_number'].append(run)
    compressed_trie_results['insert_time'].append(CT_TEST.time_inserts())
    standard_trie_results['insert_time'].append(ST_TEST.time_inserts())
    compressed_trie_results['enumerate_prefix_time'].append(CT_TEST.time_enumerate_prefix())
    standard_trie_results['enumerate_prefix_time'].append(ST_TEST.time_enumerate_prefix())
    compressed_trie_results['exact_search_time'].append(CT_TEST.time_exact_search())
    standard_trie_results['exact_search_time'].append(ST_TEST.time_exact_search())
    compressed_trie_results['prefix_search_time'].append(CT_TEST.time_prefix_search())
    standard_trie_results['prefix_search_time'].append(ST_TEST.time_prefix_search())
    compressed_trie_results['full_traversal_time'].append(CT_TEST.time_full_traversal())
    standard_trie_results['full_traversal_time'].append(ST_TEST.time_full_traversal())
    compressed_trie_results['memory_usage'].append(CT_TEST.measure_memory_usage())
    standard_trie_results['memory_usage'].append(ST_TEST.measure_memory_usage())
    compressed_trie_results['node_count'].append(CT_TEST.measure_node_count())
    standard_trie_results['node_count'].append(ST_TEST.measure_node_count())
    compressed_trie_results['avg_branching_factor'].append(CT_TEST.measure_avg_branching_factor())
    standard_trie_results['avg_branching_factor'].append(ST_TEST.measure_avg_branching_factor())
    compressed_trie_results['delete_time'].append(CT_TEST.time_deletes(DELETE_AMOUNT))
    standard_trie_results['delete_time'].append(ST_TEST.time_deletes(DELETE_AMOUNT))
    standard_trie_results['seeds'].append(SEED)
    compressed_trie_results['seeds'].append(SEED)

CT_DATAFRAME = pd.DataFrame(compressed_trie_results)
ST_DATAFRAME = pd.DataFrame(standard_trie_results)


###========= SAVE RESULTS TO CSV =========###

# Generate timestamp for file naming
timestamp = datetime.datetime.now().strftime("%m-%d-%y_%H-%M")

# Create file names with data structure type and timestamp
ct_filename = f"cmprs_trie_{timestamp}.csv"
st_filename = f"strd_trie_{timestamp}.csv"

target_dir = f"benchmark_results/{WORK_LOAD_TYPE}"

os.makedirs(target_dir, exist_ok=True)

# Save compressed trie results
ct_filepath = f"{target_dir}/{ct_filename}"
CT_DATAFRAME.to_csv(ct_filepath, index=False)

# Save standard trie results
st_filepath = f"{target_dir}/{st_filename}"
ST_DATAFRAME.to_csv(st_filepath, index=False)

CT_DATAFRAME_MASTER = CT_DATAFRAME.copy()
ST_DATAFRAME_MASTER = ST_DATAFRAME.copy()
CT_DATAFRAME_MASTER['trie_type'] = 'Compressed Trie'
ST_DATAFRAME_MASTER['trie_type'] = 'Standard Trie'

# Combine both dataframes for master file
MASTER_DATAFRAME = pd.concat([CT_DATAFRAME_MASTER, ST_DATAFRAME_MASTER], ignore_index=True)

# Save master results to project root (append if exists)
master_filepath = "MASTER.csv"
if os.path.exists(master_filepath):
    # Read existing data and append new results
    existing_data = pd.read_csv(master_filepath)
    combined_data = pd.concat([existing_data, MASTER_DATAFRAME], ignore_index=True)
    combined_data.to_csv(master_filepath, index=False)
    print(f"Master results appended to: {master_filepath}")
else:
    # Create new file if it doesn't exist
    MASTER_DATAFRAME.to_csv(master_filepath, index=False)
    print(f"Master results saved to: {master_filepath}")

