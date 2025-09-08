import sys
import os
import time
import gc
import tracemalloc
import random
from typing import Type, Optional, Any
from pympler import asizeof

# Metrics: Node Count, Memory Usage, Average Branching Factor, Timed Operations #

class MetricAnalyzer:
    def __init__(self, trie, work_load, rng=None):
        if len(work_load) == 0:
            raise ValueError("work_load must not be empty")
        self.trie = trie
        self.work_load = work_load
        self.rng = random.Random(rng)

    def time_inserts(self):
        start_time = time.perf_counter_ns()
        self.trie.batch_insert(self.work_load)
        end_time = time.perf_counter_ns()
        return end_time - start_time
    
    def time_deletes(self, n):
        if not 0 < n <= len(self.work_load): 
            raise ValueError("n must be greater than 0 and less than or equal to the length of the work load")
        start_time = time.perf_counter_ns()
        self.trie.batch_delete(self.rng.sample(self.work_load, n))
        end_time = time.perf_counter_ns()
        return end_time - start_time
    
    def time_enumerate_prefix(self, prefix=None):
        if prefix is None:
            sample_word = self.rng.choice(self.work_load)
            prefix = sample_word[:self.rng.randint(1, max(2, len(sample_word)//2))]
        start_time = time.perf_counter_ns()
        self.trie.enumerate_prefix(prefix)
        end_time = time.perf_counter_ns()
        return end_time - start_time
        
    def time_exact_search(self, word=None, miss_ratio=0.0):
        if word is None:
            word = self.rng.choice(self.work_load)
            if self.rng.random() < miss_ratio:
                while word in self.work_load:
                    word = word[:-self.rng.randint(1, len(word)//2)] + self.rng.choice(self.work_load)
        start_time = time.perf_counter_ns()
        self.trie.search(word)
        end_time = time.perf_counter_ns()
        return end_time - start_time
    
    def time_prefix_search(self, prefix=None, miss_ratio=0.0):
        if prefix is None:
            sample_word = self.rng.choice(self.work_load)
            prefix = sample_word[:self.rng.randint(1, len(sample_word)//2)]
            if self.rng.random() < miss_ratio:
                while prefix in self.work_load:
                    prefix = prefix[:-self.rng.randint(1, len(prefix)//2)] + self.rng.choice(self.work_load)
        start_time = time.perf_counter_ns()
        self.trie.prefix_search(prefix)
        end_time = time.perf_counter_ns()
        return end_time - start_time

    def time_full_traversal(self):
        start_time = time.perf_counter_ns()
        self.trie.enumerate_prefix("")
        end_time = time.perf_counter_ns()
        return end_time - start_time

    def measure_memory_usage(self):
        gc.collect()
        return asizeof.asizeof(self.trie)
    
    def measure_node_count(self):
        return self.trie.count_nodes()
    
    def measure_avg_branching_factor(self):
        return self.trie.count_nodes(get_avg_branch_factor=True)
    
    