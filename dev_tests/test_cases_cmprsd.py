# test_cases.py
# Simple, self-contained test runner for your CompressedTrie implementation.
# - No external frameworks required
# - Clear PASS/FAIL/SKIP output
# - Covers every public method (and _prepare_batch) with deterministic + randomized + radix-specific cases

import random
import string
import sys
import os
from typing import Iterable

# Add parent directory to Python path so we can import from tries package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ------------------------------------------------------------------------------
# Import the implementation under test
# ------------------------------------------------------------------------------
try:
    from tries.compressed_trie import CompressedTrie, fanout_switch as FANOUT_SWITCH
except Exception as e:
    print("[FAIL] Could not import CompressedTrie from compressed_trie.py")
    print("       Import error:", repr(e))
    sys.exit(1)

# ------------------------------------------------------------------------------
# Tiny test harness
# ------------------------------------------------------------------------------
PASS = 0
FAIL = 0
SKIP = 0


def mark(result: str, name: str, detail: str = ""):
    global PASS, FAIL, SKIP
    if result == "PASS":
        PASS += 1
        print(f"[PASS] {name}")
    elif result == "FAIL":
        FAIL += 1
        print(f"[FAIL] {name} :: {detail}")
    elif result == "SKIP":
        SKIP += 1
        print(f"[SKIP] {name} :: {detail}")


def check(name: str, condition: bool, detail: str = ""):
    mark("PASS" if condition else "FAIL", name, detail)


def expect_exception(name: str, fn, exc_type=Exception):
    try:
        fn()
    except exc_type:
        mark("PASS", name)
    else:
        mark("FAIL", name, "Expected exception not raised")


def section(title: str):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ------------------------------------------------------------------------------
# Test data generators
# ------------------------------------------------------------------------------
def gen_words_fixed() -> list[str]:
    return [
        "app",
        "apple",
        "apply",
        "bat",
        "batch",
        "bath",
        "bar",
        "bark",
        "cat",
        "cater",
        "do",
        "dog",
        "dove",
    ]


def gen_words_with_dups_unsorted() -> list[str]:
    base = [
        "apply", "apple", "app", "bath", "batch", "bat", "bark", "bar", "dog",
        "dove", "do"
    ]
    # add some duplicates and shuffle
    words = base + ["app", "dog", "bath", "BATCH"]  # tests normalization too
    random.shuffle(words)
    return words


def gen_random_words(n: int,
                     alphabet: str = string.ascii_lowercase,
                     min_len=3,
                     max_len=10) -> list[str]:
    out = []
    for _ in range(n):
        L = random.randint(min_len, max_len)
        out.append("".join(random.choice(alphabet) for _ in range(L)))
    return out


# ------------------------------------------------------------------------------
# Individual tests (baseline)
# ------------------------------------------------------------------------------
def test_prepare_batch_basic():
    section("TEST: _prepare_batch (basic)")
    t = CompressedTrie()
    inp = ["B", "a", "A", "b", "a", "B"]
    out = t._prepare_batch(inp,
                           normalize=str.casefold,
                           dedup=True,
                           presorted=False)
    check("_prepare_batch sorted+dedup", out == ["a", "b"], f"Got: {out}")

    out2 = t._prepare_batch(inp,
                            normalize=str.casefold,
                            dedup=False,
                            presorted=False)
    check("_prepare_batch sorted no dedup",
          out2 == ["a", "a", "a", "b", "b", "b"], f"Got: {out2}")


def test_prepare_batch_presorted_stable_dedup():
    section("TEST: _prepare_batch (presorted + stable dedup)")
    t = CompressedTrie()
    # already normalized & sorted under casefold:
    inp = ["aa", "aa", "ab", "ab", "b", "b"]
    out = t._prepare_batch(inp,
                           normalize=str.casefold,
                           dedup=True,
                           presorted=True)
    check("_prepare_batch presorted stable dedup", out == ["aa", "ab", "b"],
          f"Got: {out}")


def test_single_insert_and_search():
    section("TEST: single_insert & search")
    t = CompressedTrie()
    for w in gen_words_fixed():
        t.single_insert(w)
    # present
    for w in ["app", "apple", "bath", "bark", "dog"]:
        check(f"search present: {w}", t.search(w) is not None)
    # missing
    for w in ["applyy", "apps", "ba", "d"]:
        check(f"search missing: {w}", t.search(w) is None)


def test_single_delete():
    section("TEST: single_delete")
    t = CompressedTrie()
    if not hasattr(t, "single_delete"):
        mark("SKIP", "single_delete", "Method not found on CompressedTrie")
        return

    for w in ["a", "ab", "abc"]:
        t.single_insert(w)
    ok = t.single_delete("abc")
    check("single_delete existing word", ok is True)
    check("single_delete parent word intact", t.search("ab") is not None)
    check("single_delete root child intact", t.search("a") is not None)
    ok2 = t.single_delete("abcd")
    check("single_delete missing word returns False", ok2 is False)


def test_prefix_search():
    section("TEST: prefix_search (boundary + mid-edge)")
    t = CompressedTrie()
    for w in gen_words_fixed():
        t.single_insert(w)

    node, pending = t.prefix_search("app")
    check("prefix_search existing boundary", node is not None
          and pending == "", f"node={node} pending={pending}")

    node, pending = t.prefix_search("apz")
    check("prefix_search missing path", node is None and pending == "",
          f"node={node} pending={pending}")

    # mid-edge: "appl" inside edge to "apple
    t2 = CompressedTrie()
    t2.single_insert("apple")
    node, pending = t2.prefix_search("appl")
    check("prefix_search mid-edge (single word)", node is not None
          and pending == "e", f"pending={pending}")


def test_batch_insert_and_search():
    section("TEST: batch_insert & search")
    t = CompressedTrie()
    words = gen_words_with_dups_unsorted()
    t.batch_insert(words, dedup=True, presorted=False)
    expected = {w.casefold() for w in words}
    for w in expected:
        ok = t.search(w) is not None
        check(f"batch_insert -> search: {w}", ok, "Insertion may have failed")


def test_enumerate_prefix():
    section("TEST: enumerate_prefix (DFS export)")
    t = CompressedTrie()
    words = gen_words_fixed()
    t.batch_insert(words)
    got = set(t.enumerate_prefix("", k=None))
    exp = set(w.casefold() for w in words)
    check("enumerate_prefix all words", got == exp,
          f"Got: {sorted(got)} Expected: {sorted(exp)}")

    sub = set(t.enumerate_prefix("ba", k=None))
    exp_sub = {w for w in exp if w.startswith("ba")}
    check("enumerate_prefix 'ba'", sub == exp_sub,
          f"Got: {sorted(sub)} Expected: {sorted(exp_sub)}")

    k_out = list(t.enumerate_prefix("app", k=2))
    check("enumerate_prefix limit k=2",
          len(k_out) == 2, f"Got length {len(k_out)}: {k_out}")


# ------------------------------------------------------------------------------
# New radix-specific tests
# ------------------------------------------------------------------------------
def test_mid_edge_enumeration_start():
    section("TEST: mid-edge enumeration start")
    t = CompressedTrie()
    t.batch_insert(["apple", "apply"])
    out = set(t.enumerate_prefix("appl"))
    check("mid-edge enumerate yields both", out == {"apple", "apply"},
          f"Got: {out}")


def test_insert_order_symmetry():
    section("TEST: insert order symmetry (app/apple)")
    t1 = CompressedTrie()
    t1.batch_insert(["apple", "app"])
    ok1 = (t1.search("app") is not None) and (t1.search("apple") is not None)
    e1 = set(t1.enumerate_prefix("app"))

    t2 = CompressedTrie()
    t2.batch_insert(["app", "apple"])
    ok2 = (t2.search("app") is not None) and (t2.search("apple") is not None)
    e2 = set(t2.enumerate_prefix("app"))

    check("both orders contain keys", ok1 and ok2)
    check("enumeration equal regardless of order", e1 == e2, f"{e1} vs {e2}")


def test_coalescing_single_level():
    section("TEST: coalescing (single level)")
    t = CompressedTrie()
    t.batch_insert(["bat", "batch"])
    before = t.count_nodes()
    t.single_delete("batch")
    after = t.count_nodes()
    check("coalescing preserves survivor", t.search("bat") is not None)
    check("coalescing reduces nodes", after < before,
          f"before={before} after={after}")


def test_coalescing_multi_level():
    section("TEST: coalescing (multi level)")
    t = CompressedTrie()
    t.batch_insert(["international", "internet"])
    before = t.count_nodes()
    ok = t.single_delete("international")
    after = t.count_nodes()
    check("delete international ok", ok is True)
    check("internet still present", t.search("internet") is not None)
    check("node count decreased", after < before,
          f"before={before} after={after}")


def test_empty_string_behavior():
    section("TEST: empty string '' behavior")
    t = CompressedTrie()
    t.single_insert("")
    check("search empty string present", t.search("") is not None)
    all_words = set(t.enumerate_prefix("", k=None))
    check("enumerate includes empty string", "" in all_words,
          f"Got: {sorted(all_words)}")
    # delete and confirm absence
    t.single_delete("")
    check("empty string deleted", t.search("") is None)


def test_fanout_promotion_demotion():
    section("TEST: fanout promotion/demotion around threshold")
    t = CompressedTrie()
    # Create many distinct first-characters at root
    n = max(4, FANOUT_SWITCH + 3)
    words = [chr(ord('a') + i) for i in range(n)]  # "a","b","c",...
    t.batch_insert(words)
    all1 = set(t.enumerate_prefix(""))
    check("all inserted present (promotion)", all1 == set(words),
          f"{all1} vs {set(words)}")
    # Now delete down below demotion hysteresis
    for w in reversed(words):
        t.single_delete(w)
        # keep last two to test demotion path without empty trie
        if len(set(t.enumerate_prefix(""))) <= 2:
            break
    survivors = set(t.enumerate_prefix(""))
    check("survivors present after deletions (demotion ok)", survivors
          <= set(words), f"survivors={survivors}")


def test_prefix_is_word_with_children():
    section("TEST: prefix equals a word and has children")
    t = CompressedTrie()
    t.batch_insert(["app", "apple", "apply"])
    out_all = list(t.enumerate_prefix("app"))
    check("includes 'app' and children",
          set(out_all) >= {"app", "apple", "apply"})
    out_k1 = list(t.enumerate_prefix("app", k=1))
    check("k=1 yields exactly one",
          len(out_k1) == 1 and out_k1[0] == "app", f"Got: {out_k1}")


def test_batch_delete_and_prune():
    section("TEST: batch_delete & pruning")
    t = CompressedTrie()
    words = gen_words_fixed()
    t.batch_insert(words)

    to_delete = ["apply", "bath", "zzz"]  # include a missing word
    deleted, missing = t.batch_delete(to_delete, dedup=False, presorted=False)
    check("batch_delete deleted count", deleted == 2, f"Got {deleted}")
    check("batch_delete missing count", missing == 1, f"Got {missing}")
    check("deleted gone: apply", t.search("apply") is None)
    check("deleted gone: bath", t.search("bath") is None)
    check("sibling remains: apple", t.search("apple") is not None)
    check("sibling remains: batch", t.search("batch") is not None)


def test_unicode_casefold():
    section("TEST: unicode normalization (casefold)")
    t = CompressedTrie()
    t.single_insert("Straße")  # German sharp s -> 'ss' under casefold
    for probe in ["straße", "STRASSE", "Strasse"]:
        check(f"unicode casefold search: {probe}", t.search(probe) is not None)


def test_count_nodes_and_avg_branch_factor():
    section("TEST: count_nodes & avg_branch_factor")
    t = CompressedTrie()
    for w in ["a", "ab", "ac", "b"]:
        t.single_insert(w)
    total = t.count_nodes(get_avg_branch_factor=False)
    avg_bf = t.count_nodes(get_avg_branch_factor=True)
    check("count_nodes returns positive", total > 0, f"Got {total}")
    check("avg_branch_factor reasonable range", 0.0 <= avg_bf <= 26.0,
          f"Got {avg_bf}")


def test_large_random_roundtrip():
    section("TEST: large random roundtrip (insert -> enumerate -> delete)")
    random.seed(1337)
    t = CompressedTrie()
    words = gen_random_words(1500,
                             alphabet=string.ascii_lowercase,
                             min_len=4,
                             max_len=9)
    words_plus_dups = words + words[:200]
    t.batch_insert(words_plus_dups, dedup=True, presorted=False)

    sample = random.sample(words, 25)
    for w in sample:
        check(f"random search present: {w}", t.search(w) is not None)

    got = set(t.enumerate_prefix("", k=None))
    exp = set(w.casefold() for w in words)
    check("random export equals inserted set", got == exp,
          f"Exp {len(exp)} vs Got {len(got)}")

    to_delete = words[:len(words) // 2]
    deleted, missing = t.batch_delete(to_delete, dedup=True, presorted=False)
    check("random delete half -> deleted count",
          deleted == len(set(w.casefold() for w in to_delete)),
          f"Got deleted={deleted}, missing={missing}")

    remain_any = any(t.search(w) is not None for w in to_delete)
    check("deleted words actually gone", remain_any is False)

    survivors = words[len(words) // 2:]
    survivors_ok = all(
        t.search(w) is not None for w in random.sample(survivors, 25))
    check("survivors still present", survivors_ok)


# ------------------------------------------------------------------------------
# Property-ish tests & invariants (lightweight)
# ------------------------------------------------------------------------------
def test_fuzz_enumeration_prefix_property():
    section("TEST: fuzz enumeration prefix property")
    random.seed(7)
    t = CompressedTrie()
    words = set(gen_random_words(300, min_len=3, max_len=7))
    t.batch_insert(list(words))
    prefixes = random.sample(list(words), 30)
    prefixes += ["", "a", "b", "zz", "foo"]
    for p in prefixes:
        got = set(t.enumerate_prefix(p))
        exp = {w for w in words if w.startswith(p.casefold())}
        check(f"enum matches setcomp for '{p}'", got == exp,
              f"Got {len(got)} vs Exp {len(exp)}")


def test_structural_invariants():
    section("TEST: structural invariants (development)")
    t = CompressedTrie()
    corpus = gen_words_fixed() + gen_random_words(200, min_len=3, max_len=6)
    t.batch_insert(corpus)

    # Walk and assert invariants
    def walk(node):
        edges = list(node._iter_edges() or ())
        # 1) no empty edge labels
        check("no empty edge labels", all(lbl for lbl, _ in edges))
        # 2) distinct first chars
        firsts = [lbl[0] for lbl, _ in edges]
        check("distinct first chars per node", len(firsts) == len(set(firsts)))
        # 3) non-root leaf must be terminal
        if not edges and node is not t.root:
            check("leaf is terminal or merged", node.is_terminal is True)
        for _, child in edges:
            walk(child)

    walk(t.root)


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    random.seed(42)

    # Baseline / shared tests
    test_prepare_batch_basic()
    test_prepare_batch_presorted_stable_dedup()
    test_single_insert_and_search()
    test_single_delete()
    test_prefix_search()
    test_batch_insert_and_search()
    test_enumerate_prefix()
    test_batch_delete_and_prune()
    test_empty_string_behavior()
    test_unicode_casefold()
    test_count_nodes_and_avg_branch_factor()
    test_large_random_roundtrip()

    # Radix-specific additions
    test_mid_edge_enumeration_start()
    test_insert_order_symmetry()
    test_coalescing_single_level()
    test_coalescing_multi_level()
    test_fanout_promotion_demotion()
    test_prefix_is_word_with_children()

    # Property & invariants
    test_fuzz_enumeration_prefix_property()
    test_structural_invariants()

    print("\n" + "-" * 70)
    print(f"RESULTS: PASS={PASS}  FAIL={FAIL}  SKIP={SKIP}")
    print("-" * 70)
    if FAIL > 0:
        sys.exit(1)
