"""
Standard Trie (character-per-edge) with lazy children and batch operations.

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
TrieNode
    Minimal node holding `children` (dict[str, TrieNode] or None) and `is_terminal`.
Trie
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
    """

class TrieNode:
  __slots__ = ("children", "is_terminal")

  def __init__(self):
    self.children = None
    self.is_terminal = False


class Trie:
  __slots__ = ("root", )

  def __init__(self):
    self.root = TrieNode()

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

    Complexity
    ----------
    O(n log n) when sorting; O(n) when `presorted=True`.
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
    """Insert a single word into the trie.

    Parameters
    ----------
    word : str
        Word to insert.
    normalize : Callable[[str], str], default=str.casefold
        Normalization applied before insertion.

    Notes
    -----
    - Lazily creates the `children` dict only when a node gets its first child.
    - Marks the terminal node's `is_terminal=True` at the end of the path.

    Complexity
    ----------
    O(L) time, O(new_nodes) space where L = len(word).
    """
    word = normalize(word)
    node = self.root

    for w in word:
      children = node.children
      nxt = None if children is None else children.get(w)
      if nxt is None:
        nxt = TrieNode()
        if children is None:
            node.children = {w: nxt}
        else:
            children[w] = nxt
      node = nxt
    node.is_terminal = True

  
  def single_delete(self, word, normalize=str.casefold):
    """Delete a single word from the trie.

    Implementation detail
    ---------------------
    Delegates to `batch_delete` with `dedup=False, presorted=True` to reuse the
    robust pruning logic.
    """
    deleted, _ = self.batch_delete([word], normalize=normalize, dedup=False, presorted=True)
    return deleted == 1

  
  def batch_insert(self,
                   words,
                   *,
                   normalize=str.casefold,
                   dedup=True,
                   presorted=False):
    """Bulk-insert many words efficiently using LCP reuse.

    Parameters
    ----------
    words : Iterable[str]
        Words to insert.
    normalize, dedup, presorted
        See `_prepare_batch`.

    Notes
    -----
    - Words are first prepared via `_prepare_batch`.
    - Iterates words in sorted order and reuses the Longest Common Prefix (LCP)
      with the previous word to avoid retraversing from the root.
    - Lazily creates child dicts for new branches.

    Complexity
    ----------
    ~O(total new characters created) plus O(n log n) if sorting is needed.
    """
    words = self._prepare_batch(words, normalize, dedup, presorted)

    prev = ''
    path = [self.root]

    for w in words:
      lp, lw = len(prev), len(w)
      i = 0
      while i < lp and i < lw and prev[i] == w[i]:
        i += 1

      path = path[:i + 1]
      node = path[-1]

      for char in w[i:]:
        children = node.children
        nxt = None if children is None else children.get(char)

        if nxt is None:
          nxt = TrieNode()
          if children is None:
              node.children = {char: nxt}
          else:
              children[char] = nxt

        path.append(nxt)
        node = nxt

      node.is_terminal = True
      prev = w

  

  def batch_delete(self,
                   words,
                   *,
                   normalize=str.casefold,
                   dedup=True,
                   presorted=False):
    """Bulk-delete many words with pruning.

    Strategy
    --------
    - Prepare inputs (normalize/sort/dedup).
    - Iterate words in sorted order and reuse LCP with the previous word to
      minimize descent work.
    - For each present word, unset `is_terminal` and prune upward while nodes
      are non-terminal and have no children.

    Parameters
    ----------
    words : Iterable[str]
    normalize, dedup, presorted
        See `_prepare_batch`.

    Returns
    -------
    tuple[int, int]
        (deleted_count, missing_count)

    Complexity
    ----------
    ~O(total characters touched) across all words, plus pruning.
    """
    words = self._prepare_batch(words, normalize, dedup, presorted)

    prev = ""
    path_nodes = [self.root]  
    path_edges = [""] 

    deleted = 0
    missing = 0

    for w in words:
      i = 0
      lp, lw = len(prev), len(w)
      while i < lp and i < lw and prev[i] == w[i]:
        i += 1

      path_nodes = path_nodes[:i + 1]
      path_edges = path_edges[:i + 1]

      node = path_nodes[-1]
      ok = True
      for ch in w[i:]:
        children = node.children
        if children is None or ch not in children:
          ok = False
          break
        node = children[ch]
        path_nodes.append(node)
        path_edges.append(ch)

      if not ok or not node.is_terminal:
        missing += 1
        prev = w
        continue

      node.is_terminal = False
      deleted += 1

      idx = len(path_nodes) - 1
      while idx > 0:
        cur = path_nodes[idx]
        if cur.is_terminal:
          break
        children_cur = cur.children
        if children_cur and len(children_cur) > 0:
          break

        parent = path_nodes[idx - 1]
        edge_ch = path_edges[idx]

        if parent.children:
          parent.children.pop(edge_ch, None)
          if len(parent.children) == 0:
            parent.children = None
        idx -= 1
      prev = w
    return deleted, missing
    

  def prefix_search(self, prefix, normalize=str.casefold):
    """Return the node at the end of `prefix`, or None if the path is missing.

    Parameters
    ----------
    prefix : str
        Prefix to locate.
    normalize : Callable[[str], str], default=str.casefold

    Returns
    -------
    TrieNode | None
        Node corresponding to the full prefix (may be terminal or not), else None.

    Complexity
    ----------
    O(L) where L = len(prefix).
    """
    prefix = normalize(prefix)
    node = self.root
    for w in prefix:
      node = None if node.children is None else node.children.get(w)
      if node is None:
        return None
    return node
    

  def search(self, word, normalize=str.casefold):
    """Return the terminal node for `word` if present, else None.
    """
    node = self.prefix_search(word, normalize)
    return node if node and node.is_terminal else None

  
  def enumerate_prefix(self, prefix, k=None, normalize=str.casefold):
    """Yield words that start with `prefix` using an iterative DFS.

    Parameters
    ----------
    prefix : str
        The prefix to enumerate from. Use "" to export the entire trie.
    k : int | None, default=None
        If None, yield all matches; otherwise, yield up to `k` matches.
    normalize : Callable[[str], str], default=str.casefold

    Yields
    ------
    str
        Words found under the prefix (normalized form).

    Implementation details
    ----------------------
    - Uses a shared mutable character buffer to minimize intermediate string
      allocations; only joins to a Python string at yield time.
    - Traversal order follows child insertion order. Sort keys in `child_iter`
      if lexicographic order is required.
    """
    prefix_norm = normalize(prefix)
    node = self.prefix_search(prefix, normalize)
    if node is None:
      return

    yielded = 0
    buf = list(prefix_norm)

    def child_iter(n):
      if not n.children:
          return iter(())
      keys = n.children.keys()
      return iter(keys)

    if node.is_terminal:
      yield "".join(buf)
      if k is not None:
          yielded += 1
          if yielded >= k:
              return

    stack = [(node, child_iter(node), len(buf))]

    while stack:
      n, it, depth = stack[-1]
      try:
          ch = next(it)                
          child = n.children[ch]
          buf.append(ch)                 
          if child.is_terminal:
              yield "".join(buf)
              if k is not None:
                  yielded += 1
                  if yielded >= k:
                      return
          stack.append((child, child_iter(child), len(buf)))
      except StopIteration:
          stack.pop()       
          buf[depth:] = []   
    return
    

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
      children = node.children
      if children:
        total_deg += len(children)
        internal += 1
        stack.extend(children.values())
    if get_avg_branch_factor:
      return (total_deg / internal) if internal else 0.0
    return total_nodes


