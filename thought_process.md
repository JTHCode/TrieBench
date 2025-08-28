# Walking through my thought process for creating this project #

## --- Planning --- ##
  * Decide what metrics and sub-metrics to test
  * Plan out out what specific operations/methods to implement in Trie classes
  * Define different work loads to perform tests with
  * Draft format and storage plans for the official test results
  * Choose which types of data visualizations will be best for project
___________

## --- Execution --- ##
### Trie Creation: ###
*Tries: Standard Trie, Compressed Trie*
  * Start with creating standard Trie class and implementing chosen methods
  * Add detailed docstring and function definitions
  * Create and run test_case modules, then peform various functionality tests on data structure
  * Revise data structure code based on test case results until perfect score is achieved
  * Repeat all previous steps for Compressed Trie
### Test Data Creation: ###
*Work load types: English Words, URLs✅, IP Adresses, Numeric IDs*
  * Create test data generation in work_loads.py for a specific work load type
  * Test work load generation functions for accuracy and suitability in work_load_tests.py
  * Revise work load generation functions based on analysis of test results
  * Repeat the previous 3 steps for all work load types
### Metric Benchmark Recorders Creation: ###
*Metrics: Node Count, Memory Usage, Average Branching Factor, Timed Operations*
  * Implement testing functions for chosen metric in metric_analyzers.py
  * Create and run metric_tests.py to confirm accuracy and reliability of metric tests
  * Revise testing functions in metric_analyzers.py until the tests in metric_tests.py are passed
  * Repeat the previous 3 steps for all metrics that will be tested
### Benchmarks Testing Module Creation: ###
  * Set up the metric test functions and the test data generation functions in benchmarks.py
  * Impliment the storage and format for test results as previously decided
  * Run small number of prelimenary tests from benchmarks.py to analyze output result storage
  * Decide on revisions for output result storage based on findings from prelimnary test
  * Repeat the previous 3 steps until satisfied with the output storage and format
### Data Visualization Creation: ###
  * Create data_visuals.py to analyze test results and output chosen data visualizations
  * Use sample data gathered from preliminary benchmarks.py test to run data_visuals.py
  * Revise data_visuals.py based on visual output results from preliminary tests
  * Repeat previous two steps until the data visualizations are satisfactory
  * Run large number of final benchmarks in benchmarks.py
  * Run final data visualizations in data_visuals.py
  * Incorperate final findings and plots in the web page




______________
## Notes: ##
- Using slots and lazy children assignment in Trie classes for memory efficiency
- Using "fanout_switch" in Compressed Trie that optimizes switching from a list to a dictionary for holding children whenever the fanout switch amount is reached
- URL generation uses realistic probablity for elements of the URL like sub domain, TLD, scheme and path; based off of data from https://w3techs.com/technologies