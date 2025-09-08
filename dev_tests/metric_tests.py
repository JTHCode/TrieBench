#!/usr/bin/env python3
import unittest
import time
import random
import gc
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.metric_analyzers import MetricAnalyzer
from tries.standard_trie import Trie
from tries.compressed_trie import CompressedTrie
from components.work_loads import WorkLoad


class TestMetricAnalyzer(unittest.TestCase):
    """Comprehensive unit tests for MetricAnalyzer class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.work_load = WorkLoad(seed=42)
        self.test_words = self.work_load.words(100, unique=True)
        self.standard_trie = Trie()
        self.compressed_trie = CompressedTrie()
        
        # Pre-populate tries for testing
        self.standard_trie.batch_insert(self.test_words)
        self.compressed_trie.batch_insert(self.test_words)
        
        self.standard_analyzer = MetricAnalyzer(self.standard_trie, self.test_words, rng=42)
        self.compressed_analyzer = MetricAnalyzer(self.compressed_trie, self.test_words, rng=42)
    
    def test_init_valid_input(self):
        """Test MetricAnalyzer initialization with valid input"""
        analyzer = MetricAnalyzer(self.standard_trie, self.test_words, rng=42)
        self.assertEqual(analyzer.trie, self.standard_trie)
        self.assertEqual(analyzer.work_load, self.test_words)
        self.assertIsInstance(analyzer.rng, random.Random)
    
    def test_init_empty_workload(self):
        """Test MetricAnalyzer initialization with empty work load raises ValueError"""
        with self.assertRaises(ValueError) as context:
            MetricAnalyzer(self.standard_trie, [])
        self.assertIn("work_load must not be empty", str(context.exception))
    
    def test_init_none_workload(self):
        """Test MetricAnalyzer initialization with None work load"""
        with self.assertRaises(TypeError):
            MetricAnalyzer(self.standard_trie, None)
    
    def test_time_inserts_returns_positive_nanoseconds(self):
        """Test that time_inserts returns a positive time in nanoseconds"""
        # Create fresh trie to avoid double insertion
        fresh_trie = Trie()
        analyzer = MetricAnalyzer(fresh_trie, self.test_words)
        
        # Test without mocking - just verify it returns positive time
        result = analyzer.time_inserts()
        
        # Verify result is positive
        self.assertGreater(result, 0)
        self.assertIsInstance(result, int)
    
    def test_time_deletes_valid_input(self):
        """Test time_deletes with valid input"""
        n = 10
        result = self.standard_analyzer.time_deletes(n)
        
        self.assertGreater(result, 0)
        self.assertIsInstance(result, int)  # Should return nanoseconds as int
    
    def test_time_deletes_invalid_input_zero(self):
        """Test time_deletes with n=0 raises ValueError"""
        with self.assertRaises(ValueError) as context:
            self.standard_analyzer.time_deletes(0)
        self.assertIn("n must be greater than 0", str(context.exception))
    
    def test_time_deletes_invalid_input_negative(self):
        """Test time_deletes with negative n raises ValueError"""
        with self.assertRaises(ValueError) as context:
            self.standard_analyzer.time_deletes(-1)
        self.assertIn("n must be greater than 0", str(context.exception))
    
    def test_time_deletes_invalid_input_too_large(self):
        """Test time_deletes with n > work_load length raises ValueError"""
        with self.assertRaises(ValueError) as context:
            self.standard_analyzer.time_deletes(len(self.test_words) + 1)
        self.assertIn("n must be greater than 0 and less than or equal to the length of the work load", str(context.exception))
    
    def test_time_enumerate_prefix_returns_positive_time(self):
        """Test time_enumerate_prefix returns positive time"""
        prefix = "test"
        result = self.standard_analyzer.time_enumerate_prefix(prefix)
        
        self.assertGreater(result, 0)
        self.assertIsInstance(result, int)
    
    def test_time_exact_search_returns_positive_time(self):
        """Test time_exact_search returns positive time"""
        word = self.test_words[0] if self.test_words else "test"
        result = self.standard_analyzer.time_exact_search(word)
        
        self.assertGreater(result, 0)
        self.assertIsInstance(result, int)
    
    def test_time_prefix_search_returns_positive_time(self):
        """Test time_prefix_search returns positive time"""
        prefix = "test"
        result = self.standard_analyzer.time_prefix_search(prefix)
        
        self.assertGreater(result, 0)
        self.assertIsInstance(result, int)
    
    def test_time_full_traversal_returns_positive_time(self):
        """Test time_full_traversal returns positive time"""
        result = self.standard_analyzer.time_full_traversal()
        
        self.assertGreater(result, 0)
        self.assertIsInstance(result, int)
    
    def test_measure_memory_usage_returns_positive_bytes(self):
        """Test measure_memory_usage returns positive memory usage"""
        result = self.standard_analyzer.measure_memory_usage()
        
        self.assertGreater(result, 0)
        self.assertIsInstance(result, int)
    
    def test_measure_memory_usage_calls_gc_collect(self):
        """Test that measure_memory_usage calls garbage collection"""
        with patch('gc.collect') as mock_gc:
            self.standard_analyzer.measure_memory_usage()
            mock_gc.assert_called_once()
    
    def test_measure_node_count_returns_positive_integer(self):
        """Test measure_node_count returns positive integer"""
        result = self.standard_analyzer.measure_node_count()
        
        self.assertGreater(result, 0)
        self.assertIsInstance(result, int)
    
    def test_measure_avg_branching_factor_returns_float(self):
        """Test measure_avg_branching_factor returns float"""
        result = self.standard_analyzer.measure_avg_branching_factor()
        
        self.assertGreaterEqual(result, 0.0)
        self.assertIsInstance(result, float)
    
    def test_performance_characteristics(self):
        """Test that performance measurements show expected characteristics"""
        # Memory usage should be reasonable
        memory = self.standard_analyzer.measure_memory_usage()
        self.assertLess(memory, 10 * 1024 * 1024)  # Less than 10MB for 100 words
        
        # Node count should be reasonable
        node_count = self.standard_analyzer.measure_node_count()
        self.assertGreater(node_count, len(self.test_words))  # More nodes than words
        self.assertLess(node_count, len(self.test_words) * 10)  # But not too many more
        
        # Branching factor should be reasonable
        branching_factor = self.standard_analyzer.measure_avg_branching_factor()
        self.assertGreater(branching_factor, 0)
        self.assertLess(branching_factor, 50)  # Reasonable upper bound


class TestMetricAnalyzerIntegration(unittest.TestCase):
    """Integration tests for MetricAnalyzer with real data"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.work_load = WorkLoad(seed=123)
        self.large_word_set = self.work_load.words(1000, unique=True)
        self.url_set = self.work_load.urls(100)
        self.ip_set = self.work_load.ips(100)
    
    def test_large_dataset_performance(self):
        """Test performance with larger datasets"""
        trie = Trie()
        trie.batch_insert(self.large_word_set)
        analyzer = MetricAnalyzer(trie, self.large_word_set)
        
        # Memory usage should scale reasonably
        memory = analyzer.measure_memory_usage()
        self.assertLess(memory, 100 * 1024 * 1024)  # Less than 100MB for 1000 words
        
        # Node count should be reasonable
        node_count = analyzer.measure_node_count()
        self.assertGreater(node_count, len(self.large_word_set))
        
        # Operations should complete in reasonable time
        start_time = time.time()
        analyzer.time_full_traversal()
        end_time = time.time()
        
        self.assertLess(end_time - start_time, 1.0)  # Less than 1 second
    
    def test_different_data_types(self):
        """Test with different types of data (words, URLs, IPs)"""
        data_sets = [
            ("words", self.large_word_set),
            ("urls", self.url_set),
            ("ips", self.ip_set)
        ]
        
        for data_type, data in data_sets:
            with self.subTest(data_type=data_type):
                trie = Trie()
                trie.batch_insert(data)
                analyzer = MetricAnalyzer(trie, data)
                
                # All metrics should work
                memory = analyzer.measure_memory_usage()
                node_count = analyzer.measure_node_count()
                branching_factor = analyzer.measure_avg_branching_factor()
                
                self.assertGreater(memory, 0)
                self.assertGreater(node_count, 0)
                self.assertGreaterEqual(branching_factor, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
