# Standard Trie (character-per-edge) #

This module provides a compact, fast Trie implementation tuned for large batches.
Key design choices:
- **Memory efficiency:** `TrieNode` uses `__slots__` and *lazy* child dicts (`children=None`
  until the first child is added), dramatically reducing per-node overhead.
- **Normalization-aware API:** Most methods accept a `normalize` callable (default:
  `str.casefold`) so callers can consistently case-fold / normalize Unicode at the
  API boundary.
- **Batch performance:** `batch_insert` and `batch_delete` both exploit the Longest
  Common Prefix (LCP) between *adjacent, sorted* inputs to minimize retraversal.
- **Iterative traversals:** All traversals are iterative (no recursion), avoiding
  Python recursion limits and extra call overhead.


Classes
-------
### TrieNode: ###
  Minimal node holding `children` (dict[str, TrieNode] or None) and `is_terminal`.
### Trie: ###
  Public API for insert, delete, search, prefix enumeration, and structural stats.


Complexity (typical)
--------------------
- single insert / search: O(L)
- batch insert (sorted): ~O(total new characters created); avoids re-walking shared prefixes
- batch delete (sorted): ~O(total characters touched) + pruning work
- enumerate prefix: O(L + K · avg_suffix_length), where K is number of results yielded


Conventions & Notes
-------------------
- **Normalization:** All mutating/read methods accept `normalize`. If you pass
  `presorted=True`, the input must already be sorted according to the *same*
  normalization you pass here.
- **Children:** `children` is `None` for leaves; create the dict only when adding
  the first child. Always guard with `if node.children: ...`.
- **Enumeration order:** By default follows child insertion order. If you need
  lexicographic output, sort keys at visitation time in your caller.
- **Deletion semantics:** Deleting a non-present word increments `missing_count`;
  present words are unmarked and pruned upward until reaching a terminal node or
  a node with remaining children.
- **Empty string:** If your dataset may include `""` (empty word), `root.is_terminal`
  will represent it; enumeration will yield `""` when appropriate.