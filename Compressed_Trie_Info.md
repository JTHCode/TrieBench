# Compressed Trie (Radix/Patricia) #

This module implements a memory-efficient, high-performance compressed trie
(radix trie / Patricia trie) for string keys. It stores labels on **edges**
rather than single characters on nodes, which reduces depth and speeds up
operations that share long prefixes (e.g., URL paths, file system paths,
natural-language terms).

Key features
------------
- **Space efficiency**
  - Nodes use `__slots__` and defer allocating children until needed.
  - Outgoing edges are stored adaptively:
    - small fanout → list of `(label, child)` tuples
    - large fanout → dict mapping `first_char -> (label, child)`
  - The switch threshold is controlled by the module constant `fanout_switch`.
- **Normalization-aware API**
  - All public methods accept an optional `normalize` callable (default:
    `str.casefold`) so callers can consistently case-fold / normalize Unicode.
- **Batch operations**
  - `batch_insert` / `batch_delete` prepare (normalize/sort/dedup) inputs once
    for efficiency and then perform per-key operations.
- **Iterative traversals**
  - All traversals are iterative (no recursion), avoiding recursion limits and
    reducing Python call overhead.
- **Proper mid-edge handling**
  - `prefix_search` returns `(node, pending)` where `pending` captures the
    remainder of an edge label when the prefix ends mid-edge—crucial for
    correct search and enumeration on compressed tries.

Classes
-------
### RadixNode ###
  Internal node type. Holds `edges` (None | list | dict) and `is_terminal`.
  Helper methods:
  - `_get(ch)` → `(label, child)` for the edge whose label starts with `ch`
  - `_set(label, child)` → insert/replace by first character
  - `_del(ch)` → delete edge by first character
  - `_iter_edges()` → iterate `(label, child)` pairs
  - `_degree()` → number of outgoing edges
  - `_only_edge()` → `(label, child)` if exactly one child, else None

### CompressedTrie ###
  Public API for building and querying the trie.

Public API (high level)
-----------------------
- `_prepare_batch(words, normalize=str.casefold, dedup=True, presorted=False)`
    Normalize and (optionally) sort/deduplicate a batch.
- `single_insert(word, normalize=str.casefold)`
    Insert one word; splits edges as needed (Patricia behavior).
- `batch_insert(words, *, normalize=str.casefold, dedup=True, presorted=False)`
    Insert many words efficiently after a single preparation pass.
- `single_delete(word, normalize=str.casefold)`
    Delete one word; prunes empty nodes and **coalesces** unary non-terminal
    nodes by concatenating their edge labels upward.
- `batch_delete(words, *, normalize=str.casefold, dedup=True, presorted=False)`
    Delete many words; returns `(deleted_count, missing_count)`.
- `prefix_search(prefix, normalize=str.casefold)`
    Return `(node, pending)` for `prefix`. `pending == ""` when the prefix ends
    on a node boundary; otherwise `pending` is the unconsumed remainder of the
    matching edge label.
- `search(word, normalize=str.casefold)`
    Return the terminal node if `word` exists; else `None`.
- `enumerate_prefix(prefix, k=None, normalize=str.casefold)`
    Generator that streams words beginning with `prefix` using iterative DFS and
    a shared mutable buffer. Handles mid-edge prefixes correctly. Yields up to
    `k` results when provided.
- `count_nodes(get_avg_branch_factor=False)`
    Return total node count, or the average out-degree over internal nodes.

Complexity (typical)
--------------------
Let L be the input string length.
- Insert/search/delete: **O(L)** on average (shorter in practice due to edge labels).
- Prefix enumeration: **O(L + K · Ā)** where K is results yielded and Ā is the
  average suffix length in the enumerated subtree.
- Batch operations: dominated by `O(n log n)` for sorting when `presorted=False`;
  otherwise linear after normalization and stable deduplication.

Conventions & invariants
------------------------
- **Edge invariant:** At any node, no two outgoing edges share the same first
  character. This enables O(1) candidate selection by first char in dict mode.
- **Children container:** `edges` is `None` for leaves; a list or dict otherwise.
  `_iter_edges()` yields in container order (insertion order in practice).
- **Normalization:** If you pass `presorted=True` to batch methods, the inputs
  must be sorted under the **same** normalization you pass in.
- **Empty string:** If `""` is inserted, the root’s `is_terminal` represents it.
  Enumeration starting at `""` may yield `""` accordingly.

