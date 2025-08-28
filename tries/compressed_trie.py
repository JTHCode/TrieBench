"""
Compressed Trie (Radix/Patricia) with lazy edges and batch operations.

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
RadixNode
    Internal node type. Holds `edges` (None | list | dict) and `is_terminal`.
    Helper methods:
      - `_get(ch)` → `(label, child)` for the edge whose label starts with `ch`
      - `_set(label, child)` → insert/replace by first character
      - `_del(ch)` → delete edge by first character
      - `_iter_edges()` → iterate `(label, child)` pairs
      - `_degree()` → number of outgoing edges
      - `_only_edge()` → `(label, child)` if exactly one child, else None
      
CompressedTrie
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
"""


fanout_switch = 8

class RadixNode:
  __slots__ = ("edges", "is_terminal")
  
  def __init__(self, is_terminal=False):
    self.edges = None
    self.is_terminal = is_terminal
    

  def _get(self, ch):
    """Return (label, child) or None for the edge whose label starts with ch."""
    e = self.edges
    if e is None:
      return None
    if isinstance(e, dict): 
      return e.get(ch)

    for key, child in e:
      if key[0] == ch:
        return (key, child)
    return None


  def _set(self, chars, child):
    """Insert/replace edge by its first char."""
    e = self.edges
    ch = chars[0]
    
    if e is None:
      self.edges = [(chars, child)]
      return
    if isinstance(e, dict):
      e[ch] = (chars, child)
      return
      
    for i, (k, v) in enumerate(e):
      if k[0] == ch:
        e[i] = (chars, child)
        break
    else:
      e.append((chars, child))
      if len(e) >= fanout_switch:   # Promotion to dict
        self.edges = {k[0]: (k, child) for k, child in e}


  def _del(self, char):
    """Delete edge by first char; return True if deleted."""
    e = self.edges
    if e is None:
      return False

    if isinstance(e, dict):
      if char in e:
        del e[char]
        if len(e) <= fanout_switch - 2:  # Demotion to list
          self.edges = list(e.values())
        return True
      return False

    for i, (k, v) in enumerate(e):
      if k[0] == char:
        e.pop(i)
        if not e:
          self.edges = None
        return True
    return False


  def _iter_edges(self):
    """Yield (label, child) for all outgoing edges."""
    e = self.edges
    if not e: 
      return
    if isinstance(e, dict):
      for chars, child in e.values():
        yield (chars, child)
    else:
      yield from e


  def _degree(self):
    e = self.edges
    return 0 if not e else len(e)

  def _only_edge(self):
    """Return (label, child) if exactly one outgoing edge; else None."""
    e = self.edges
    if not e:
      return None
    if isinstance(e, dict):
      if len(e) == 1:
        return next(iter(e.values()))
      return None
    if len(e) == 1:
      return e[0]
    return None






#### ===================================================  ####
#    Compressed Trie (Radix Trie) with lazy children and batch operations
#### ===================================================  ####

class CompressedTrie:
  __slots__ = ("root", )
  
  def __init__(self):
    self.root = RadixNode()


  @staticmethod
  def _lcp(a, b):
    """Helper to Return the length of the Longest Common Prefix between a and b."""
    i = 0
    n = min(len(a), len(b))
    while i < n and a[i] == b[i]:
      i += 1
    return i


  def _prepare_batch(self,
     words,
     normalize=str.casefold,
     dedup=True,
     presorted=False):
    """Normalize, and optionally sort/deduplicate, a batch of strings.
  
    Parameters
    ----------
    words : Iterable[str]
    Incoming words to process.
    normalize : Callable[[str], str], default=str.casefold
    Normalization function applied to each element (e.g., case folding).
    dedup : bool, default=True
    Remove duplicates within the batch.
    presorted : bool, default=False
    If True, `words` is already sorted under *the same* `normalize` rule.
    When True + dedup, we do a stable O(n) pass to remove duplicates.
  
    Returns
    -------
    list[str]
    Normalized (and possibly sorted/deduplicated) words ready for batch ops.
    """
    items = (normalize(w) for w in words)
  
    if not presorted:
      return sorted(set(items)) if dedup else sorted(items)
  
    if dedup:
      unique = []
      last = None
      for w in items:
        if w != last:
          unique.append(w)
          last = w
      return unique
    return list(items)


  def single_insert(self, word, normalize=str.casefold):
    """Insert a word into the compressed (radix/Patricia) trie in O(L) time.

    - Optionally normalizes `word` once.
    - Selects candidate edge by first character; if none exists, adds a new edge
      labeled with the remaining `word` to a terminal node.
    - If an edge label is fully matched, descends and continues with the suffix.
    - On partial match, splits the edge:
      creates an intermediate node for the shared prefix, reattaches the old tail,
      and (if present) adds the new tail as a terminal edge. Marks the intermediate
      node terminal when the word ends at the split.
    - If traversal ends exactly at a node, marks that node as terminal.

    Args:
        word (str): Key to insert.
        normalize (Callable[[str], str] | None): Optional normalizer (default: str.casefold).

    Returns:
        None
    """
    if normalize is not None:
      word = normalize(word)
    node = self.root

    while word:
      RN = RadixNode
      nxt = node._get(word[0])
      if nxt is None:
        node._set(word, RadixNode(True))
        return
        
      label, child = nxt
      i = self._lcp(word, label)
      if i == len(label):
        word = word[i:]
        node = child
        continue
      if i > 0:
        shared, old, new = label[:i], label[i:], word[i:]
        mid = RN(is_terminal=(new == ""))
        node._set(shared, mid)
        mid._set(old, child)
        if new:
          mid._set(new, RN(True))
        return
      node._set(word, RN(True))   # Fall back
      return
    node.is_terminal = True
  


  def batch_insert(self, words, *, normalize=str.casefold, dedup=True, presorted=False):
    """Insert a single word into the compressed trie."""
    words = self._prepare_batch(words, normalize, dedup, presorted)
    for w in words:
      self.single_insert(w, normalize=None)



  def single_delete(self, word, normalize=str.casefold):
    """Delete one word from the compressed (radix/Patricia) trie.

    - Optionally normalizes `word` once.
    - Traverses by selecting candidate edges via first character and matching the
      longest common prefix (LCP) against each edge label. If traversal diverges
      mid-edge, the word is not present and no changes are made.
    - If traversal ends exactly at a node boundary and that node is terminal, unmark
      it and prune upward:
      * remove edges for nodes that become childless; and
      * coalesce (merge) unary, non-terminal nodes by concatenating their sole edge
        labels into the parent’s incoming edge (multi-level).
    - Special case: deleting the empty string "" unmarks the root if it is terminal.

    Args:
        word (str): Key to delete.
        normalize (Callable[[str], str] | None): Optional normalizer (default: str.casefold).

    Returns:
        bool: True if the word existed and was deleted; False otherwise.

    Complexity:
        O(L + P), where L = len(word) and P = number of nodes pruned/merged."""
    if normalize is not None:
      word = normalize(word)
    if word == "":
      if self.root.is_terminal:
          self.root.is_terminal = False
          return True
      return False

    node = self.root
    rem = word
    frames = []
    lcp = self._lcp
    _get = RadixNode._get
    _set = RadixNode._set
    _del = RadixNode._del

    while rem:
      hit = _get(node, rem[0])
      if hit is None:
        return False
      label, child = hit
      i = lcp(rem, label)
      if i < len(label):
        return False
      frames.append((node, label, child))
      node = child
      rem = rem[i:]

    if not node.is_terminal:
      return False
    node.is_terminal = False

    cur = node
    while frames:
      parent, in_label, _ = frames.pop()
      if cur.is_terminal:
        break

      deg = cur._degree()
      if deg == 1:
        only = cur._only_edge()
        child_label, grand = only
        _set(parent, in_label + child_label, grand)
        cur = parent
        while frames and not cur.is_terminal and cur._degree() == 1:
          gp, gp_edge, _ = frames.pop()
          only2 = cur._only_edge()
          child_label, grand_child = only2
          _set(gp, gp_edge + child_label, grand_child)
          cur = gp
        return True
        
      if deg == 0:
        _del(parent, in_label[0])
        cur = parent
        continue
      break
    return True



  def batch_delete(self, words, *, normalize=str.casefold, dedup=True, presorted=False):
    """Delete many words; returns (deleted_count, missing_count)."""
    words = self._prepare_batch(words, normalize, dedup, presorted)
    deleted = 0
    missing = 0
    for w in words:
      if self.single_delete(w, normalize=None):
        deleted += 1
      else:
        missing += 1
    return deleted, missing
  
    
    

  def prefix_search(self, prefix, normalize=str.casefold):
    """Locate the node for a given prefix in the compressed (radix/Patricia) trie.

    - Optionally normalizes `prefix`.
    - Traverses edges by first character, consuming whole edge labels when matched.
    - If the prefix ends *mid-edge*, returns the child node for that edge plus the
      unconsumed remainder (`pending`).
    - Empty prefix returns `(root, "")`; missing path returns `(None, "")`.

    Args:
        prefix (str): Prefix to locate.
        normalize (Callable[[str], str] | None): Optional normalizer (default: str.casefold).

    Returns:
        tuple[RadixNode | None, str]:
            `(node, pending)` where `pending == ""` if the prefix ends exactly on a
            node boundary; otherwise `pending` is the leftover suffix of the edge label.

    Notes:
        Exact membership check succeeds if `node is not None`, `pending == ""`,
        and `node.is_terminal` is True.

    Complexity:
        O(L), where L = len(prefix).
    """
    if normalize is not None:
      prefix = normalize(prefix)
    if not prefix:                     
      return self.root, ""
      
    node = self.root
    lcp = self._lcp
    while prefix:
      hit = node._get(prefix[0])
      if hit is None:
        return None, ""
      label, child = hit
      i = lcp(prefix, label)
      
      if i == len(label):
        prefix = prefix[i:]
        node = child
        continue
        
      if i == len(prefix):
        return child, label[i:]
      return None, ""
    return node, ""


  def search(self, word, normalize=str.casefold):
    """Return the terminal node for `word` if present, else None.
    """
    node, suffix = self.prefix_search(word, normalize)
    return node if node and node.is_terminal and suffix == "" else None


  def count_nodes(self, get_avg_branch_factor=False):
    """Return total node count, or average branching factor over internal nodes.

    Parameters
    ----------
    get_avg_branch_factor : bool, default=False
        If False, return the total node count.
        If True, return average out-degree over internal nodes only:
        `sum(len(children)) / (# internal nodes)`.

    Returns
    -------
    int | float
        Total nodes (int) or average branching factor (float).

    Complexity
    ----------
    O(#nodes) time, O(depth) extra space.
    """
    total_nodes = 0
    internal = 0
    total_deg = 0

    stack = [self.root]
    while stack:
      node = stack.pop()
      total_nodes += 1

      deg = node._degree()
      if deg > 0:
        total_deg += deg
        internal += 1
        for _, child in (node._iter_edges()):
          stack.append(child)
    if get_avg_branch_factor:
      return (total_deg / internal) if internal else 0.0
    return total_nodes



  def enumerate_prefix(self, prefix, k=None, normalize=str.casefold):
    """Enumerate all words that start with `prefix` using an iterative DFS.

    - Optionally normalizes `prefix`, then uses `prefix_search` to locate the start:
      if the prefix ends mid-edge, appends the pending edge suffix to a mutable
      buffer before traversal.
    - If the starting position corresponds to a stored word (after applying the
      pending suffix, if any), yields that word, then explores descendants.
    - Traverses without recursion using a stack of `(node, child_iterator, depth)`,
      extending the shared buffer with each edge label and restoring it on backtrack.
    - Yields up to `k` matches when `k` is provided; otherwise streams all matches.
    - Output order follows the nodes’ child iteration order (insertion order);
      this method does not impose lexicographic sorting.

    Args:
        prefix (str): Prefix to enumerate from ("" enumerates the entire trie).
        k (int | None): Optional limit on number of results (None for all).
        normalize (Callable[[str], str] | None): Optional normalizer (default: str.casefold).

    Yields:
        str: Normalized words beginning with `prefix`.

    Notes:
        - If the prefix path is missing or `k <= 0`, nothing is yielded.
        - Handles mid-edge prefixes correctly by seeding the buffer with the
          remainder of the matching edge before DFS.

    Complexity:
        O(L + K·Ā), where L = len(prefix), K = #yielded words, and Ā is the average
        suffix length under the prefix. Uses O(depth) auxiliary space for the stack.
    """

    if normalize is not None:
      prefix = normalize(prefix)
    node, suffix = self.prefix_search(prefix, normalize=None)
    if node is None:
      return
    if k is not None and k <= 0:
      return

    buf = list(prefix)
    yielded = 0
    if suffix or node.is_terminal:
      buf.extend(suffix)
      if node.is_terminal:
        yield "".join(buf)
        if k is not None:
          yielded += 1
          if yielded >= k:
            return

    _iter = RadixNode._iter_edges
    to_str = "".join
    stack = [(node, _iter(node), len(buf))]
    
    while stack:
      node, children, depth = stack[-1]
      try:
        buf[depth:] = []
        label, child = next(children)
        buf.extend(label)
        if child.is_terminal:
          yield to_str(buf)
          if k is not None:
            yielded += 1
            if yielded >= k:
              return
        stack.append((child, _iter(child), len(buf)))
      except StopIteration:
        stack.pop()
    return
    

