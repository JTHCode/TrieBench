# test_cases.py
# Simple, self-contained test runner for your Trie implementation.
# - No external frameworks required
# - Clear PASS/FAIL/SKIP output
# - Covers every public method (and _prepare_batch) with deterministic + randomized cases

import random
import string
import sys
from typing import Iterable

# ------------------------------------------------------------------------------
# Import the implementation under test
# ------------------------------------------------------------------------------
try:
    from ..tries.standard_trie import Trie  # adjust if your file/module name differs
except Exception as e:
    print("[FAIL] Could not import Trie from standard_trie.py")
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
        "app", "apple", "apply",
        "bat", "batch", "bath",
        "bar", "bark",
        "cat", "cater",
        "do", "dog", "dove",
    ]

def gen_words_with_dups_unsorted() -> list[str]:
    base = ["apply", "apple", "app", "bath", "batch", "bat", "bark", "bar", "dog", "dove", "do"]
    # add some duplicates and shuffle
    words = base + ["app", "dog", "bath", "BATCH"]  # tests normalization too
    random.shuffle(words)
    return words

def gen_random_words(n: int, alphabet: str = string.ascii_lowercase, min_len=3, max_len=10) -> list[str]:
    out = []
    for _ in range(n):
        L = random.randint(min_len, max_len)
        out.append("".join(random.choice(alphabet) for _ in range(L)))
    return out

# ------------------------------------------------------------------------------
# Individual tests
# ------------------------------------------------------------------------------
def test_prepare_batch_basic():
    section("TEST: _prepare_batch (basic)")
    t = Trie()
    inp = ["B", "a", "A", "b", "a", "B"]
    out = t._prepare_batch(inp, normalize=str.casefold, dedup=True, presorted=False)
    check("_prepare_batch sorted+dedup", out == ["a", "b"], f"Got: {out}")

    out2 = t._prepare_batch(inp, normalize=str.casefold, dedup=False, presorted=False)
    check("_prepare_batch sorted no dedup", out2 == ["a", "a", "a", "b", "b", "b"], f"Got: {out2}")

def test_prepare_batch_presorted_stable_dedup():
    section("TEST: _prepare_batch (presorted + stable dedup)")
    t = Trie()
    # already normalized & sorted under casefold:
    inp = ["aa", "aa", "ab", "ab", "b", "b"]
    out = t._prepare_batch(inp, normalize=str.casefold, dedup=True, presorted=True)
    check("_prepare_batch presorted stable dedup", out == ["aa", "ab", "b"], f"Got: {out}")

def test_single_insert_and_search():
    section("TEST: single_insert & search")
    t = Trie()
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
    t = Trie()
    # some impls may have the method mis-indented; skip cleanly if not found
    if not hasattr(t, "single_delete"):
        mark("SKIP", "single_delete present", "Method not found on Trie (check indentation/definition)")
        return

    for w in ["a", "ab", "abc"]:
        t.single_insert(w)
    # delete deepest; parents should remain
    ok = t.single_delete("abc")
    check("single_delete existing word", ok is True)
    check("single_delete left parent word intact", t.search("ab") is not None)
    check("single_delete left root child intact", t.search("a") is not None)
    # delete missing
    ok2 = t.single_delete("abcd")
    check("single_delete missing word returns False", ok2 is False)

def test_prefix_search():
    section("TEST: prefix_search")
    t = Trie()
    for w in gen_words_fixed():
        t.single_insert(w)
    node = t.prefix_search("app")
    check("prefix_search existing path", node is not None)
    check("prefix_search missing path", t.prefix_search("apz") is None)

def test_batch_insert_and_search():
    section("TEST: batch_insert & search")
    t = Trie()
    words = gen_words_with_dups_unsorted()
    t.batch_insert(words, dedup=True, presorted=False)
    # All unique normalized words should be present
    expected = {w.casefold() for w in words}
    for w in expected:
        ok = t.search(w) is not None
        check(f"batch_insert -> search: {w}", ok, "Insertion likely failed (check child assignment for new edges)")

def test_enumerate_prefix():
    section("TEST: enumerate_prefix (DFS export)")
    t = Trie()
    words = gen_words_fixed()
    t.batch_insert(words)
    # all words via prefix=""
    got = set(t.enumerate_prefix("", k=None))
    exp = set(w.casefold() for w in words)
    check("enumerate_prefix all words", got == exp, f"Got: {sorted(got)} Expected: {sorted(exp)}")

    # subset prefix
    sub = set(t.enumerate_prefix("ba", k=None))
    exp_sub = {w for w in exp if w.startswith("ba")}
    check("enumerate_prefix 'ba'", sub == exp_sub, f"Got: {sorted(sub)} Expected: {sorted(exp_sub)}")

    # limit k
    k_out = list(t.enumerate_prefix("app", k=2))
    check("enumerate_prefix limit k=2", len(k_out) == 2, f"Got length {len(k_out)}: {k_out}")

def test_batch_delete_and_prune():
    section("TEST: batch_delete & pruning")
    t = Trie()
    words = gen_words_fixed()
    t.batch_insert(words)

    to_delete = ["apply", "bath", "zzz"]  # include a missing word
    deleted, missing = t.batch_delete(to_delete, dedup=False, presorted=False)
    check("batch_delete deleted count", deleted == 2, f"Got {deleted}")
    check("batch_delete missing count", missing == 1, f"Got {missing}")

    # Deleted words gone
    check("deleted word gone: apply", t.search("apply") is None)
    check("deleted word gone: bath", t.search("bath") is None)

    # Siblings remain
    check("sibling remains: apple", t.search("apple") is not None)
    check("sibling remains: batch", t.search("batch") is not None)

def test_empty_string_handling():
    section("TEST: empty string '' handling")
    t = Trie()
    t.single_insert("")  # if supported, root.is_terminal should be set
    check("search empty string present", t.search("") is not None)
    all_words = list(t.enumerate_prefix("", k=None))
    check("enumerate includes empty string", "" in all_words, f"Got: {all_words}")

def test_unicode_normalization():
    section("TEST: unicode normalization (casefold)")
    t = Trie()
    t.single_insert("Straße")  # German sharp s -> 'ss' under casefold
    # lookup with different casings/forms
    for probe in ["straße", "STRASSE", "Strasse"]:
        check(f"unicode casefold search: {probe}", t.search(probe) is not None)

def test_count_nodes_and_avg_branch_factor():
    section("TEST: count_nodes & avg_branch_factor")
    t = Trie()
    # Construct small controlled trie
    for w in ["a", "ab", "ac", "b"]:
        t.single_insert(w)
    total = t.count_nodes(get_avg_branch_factor=False)
    avg_bf = t.count_nodes(get_avg_branch_factor=True)
    check("count_nodes returns positive", total > 0, f"Got {total}")
    check("avg_branch_factor reasonable range", 0.0 <= avg_bf <= 26.0, f"Got {avg_bf}")

def test_large_random_roundtrip():
    section("TEST: large random roundtrip (insert -> enumerate -> delete)")
    random.seed(1337)
    t = Trie()
    words = gen_random_words(2000, alphabet=string.ascii_lowercase, min_len=4, max_len=9)
    # Insert (unsorted with dups)
    words_plus_dups = words + words[:200]
    t.batch_insert(words_plus_dups, dedup=True, presorted=False)

    # Check membership for a sample
    sample = random.sample(words, 25)
    for w in sample:
        check(f"random search present: {w}", t.search(w) is not None)

    # Enumerate all and compare set equality
    got = set(t.enumerate_prefix("", k=None))
    exp = set(w.casefold() for w in words)
    check("random export equals inserted set", got == exp, f"Exp {len(exp)} vs Got {len(got)}")

    # Delete half and re-check
    to_delete = words[: len(words)//2]
    deleted, missing = t.batch_delete(to_delete, dedup=True, presorted=False)
    check("random delete half -> deleted count", deleted == len(set(w.casefold() for w in to_delete)),
          f"Got deleted={deleted}, missing={missing}")

    remain_any = any(t.search(w) is not None for w in to_delete)
    check("deleted words actually gone", remain_any is False)

    # Remaining words still present
    survivors = words[len(words)//2 :]
    survivors_ok = all(t.search(w) is not None for w in random.sample(survivors, 25))
    check("survivors still present", survivors_ok)

# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    random.seed(42)

    test_prepare_batch_basic()
    test_prepare_batch_presorted_stable_dedup()
    test_single_insert_and_search()
    test_single_delete()
    test_prefix_search()
    test_batch_insert_and_search()
    test_enumerate_prefix()
    test_batch_delete_and_prune()
    test_empty_string_handling()
    test_unicode_normalization()
    test_count_nodes_and_avg_branch_factor()
    test_large_random_roundtrip()

    print("\n" + "-" * 70)
    print(f"RESULTS: PASS={PASS}  FAIL={FAIL}  SKIP={SKIP}")
    print("-" * 70)
    if FAIL > 0:
        sys.exit(1)