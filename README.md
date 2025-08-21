Trie vs Comperessed Trie Research App
===============
This project is used to compare peformance and efficiency metrics between a **Trie** and a **Compressed Trie**. 
Multiple different operations and metrics will be compared (see list below). The results of these tests can
be used to help determain which data structure is optimal for a given use case.

-----------
## **Tests to perform**: ##
### **Operations**: ###
* Searches
  * Exact search
  * Prefix search
  * Prefix enumeration (*Time to return the first K completions*)
  * Full traversal and export 
* Insertion / Deletion
  * Single insert / delete
  * Batch insert / delete
### **Metrics**: ###
* Memory
  * Node count
  * Memory usage
  * Avergae branching factor (*Edge count // Node count)
* Time
  * Timed operations (*Using time.perf_counter_ns()*)
### **Work Loads**: ###
* English words
* URL / File paths (*Very long identical prefixes*)
* Numeric IDs / Product codes
-------------

