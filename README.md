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
* IP Adresses
-------------

## Credit/Sources: ##
- List of English words used for random sampling data: https://github.com/dwyl/english-words
- List of common English words for random sampling data: http://www.mit.edu/~ecprice/wordlist.10000
- Data source used for assigning probability in URL generation: https://w3techs.com/technologies
- Source for base URL Domains: [^fn1]

[^fn1]: Victor Le Pochat, Tom Van Goethem, Samaneh Tajalizadehkhoob, Maciej Korczyński, and Wouter Joosen. 2019. "Tranco: A Research-Oriented Top Sites Ranking Hardened Against Manipulation," Proceedings of the 26th Annual Network and Distributed System Security Symposium (NDSS 2019). https://doi.org/10.14722/ndss.2019.23386