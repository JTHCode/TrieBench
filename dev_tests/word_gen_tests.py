import os
import sys
import unittest
from collections import Counter
import importlib.util

# ---------------- Import shim (works from dev_tests/) ----------------
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(THIS_DIR, os.pardir))
COMPONENTS_DIR = os.path.join(ROOT_DIR, "components")

# Ensure repo root is on sys.path so "components" is importable
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Optional: set cwd to repo root so any relative file opens in components/work_loads.py work.
# Comment this out if you've already made paths robust inside work_loads.py.
os.chdir(ROOT_DIR)

try:
    from components.work_loads import gen_words_with_prefix_freq, generate_random_words
except Exception:
    # Fallback: load by absolute path
    mod_path = os.path.join(COMPONENTS_DIR, "work_loads.py")
    spec = importlib.util.spec_from_file_location("work_loads", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    gen_words_with_prefix_freq = mod.gen_words_with_prefix_freq
    generate_random_words = mod.generate_random_words


# ---------- Helpers for prefix clustering metrics ----------
def two_prefix(w: str) -> str:
    return w[:2] if len(w) >= 2 else w

def avg_run_length(words):
    """Average run-length of consecutive identical 2-char prefixes."""
    if not words:
        return 0.0
    prev = two_prefix(words[0])
    run = 1
    runs = []
    for w in words[1:]:
        p = two_prefix(w)
        if p == prev:
            run += 1
        else:
            runs.append(run)
            run = 1
            prev = p
    runs.append(run)
    return sum(runs) / len(runs)

def neighbor_same_prefix_ratio(words):
    """Fraction of positions i>0 where prefix[i] == prefix[i-1]."""
    if len(words) < 2:
        return 0.0
    num_same = 0
    prev = two_prefix(words[0])
    for w in words[1:]:
        p = two_prefix(w)
        if p == prev:
            num_same += 1
        prev = p
    return num_same / (len(words) - 1)

def prefix_hhi(words):
    """Herfindahl-Hirschman index over 2-char prefixes; higher => more concentrated."""
    n = len(words)
    if n == 0:
        return 0.0
    counts = Counter(two_prefix(w) for w in words)
    return sum((c / n) ** 2 for c in counts.values())


# ---------------------------------- Tests ----------------------------------
class TestGenerateRandomWords(unittest.TestCase):
    def test_length_and_types_nonunique(self):
        n = 10_000  # < 100k
        words = generate_random_words(n, seed=123, unique=False)
        self.assertEqual(len(words), n)
        self.assertTrue(all(isinstance(w, str) and len(w) > 0 for w in words))

    def test_reproducibility(self):
        n = 5_000
        a = generate_random_words(n, seed=999, unique=False)
        b = generate_random_words(n, seed=999, unique=False)
        c = generate_random_words(n, seed=1000, unique=False)
        self.assertEqual(a, b)          # same seed => identical
        self.assertNotEqual(a, c)       # different seed => very likely different

    def test_uniqueness(self):
        # Request fewer than common list size; ensure uniqueness holds.
        n = 5_000
        words = generate_random_words(n, seed=42, unique=True)
        self.assertEqual(len(words), n)
        self.assertEqual(len(set(words)), n)

    def test_unique_overflow_raises(self):
        with self.assertRaises(ValueError):
            generate_random_words(1_000_000_000, seed=1, unique=True)


class TestPrefixFrequencyGenerator(unittest.TestCase):
    def test_basic_length_and_types(self):
        n = 10_000
        words = gen_words_with_prefix_freq(n, prefix_freq=0.0, seed=7, unique=False)
        self.assertEqual(len(words), n)
        self.assertTrue(all(isinstance(w, str) and len(w) > 0 for w in words))

    def test_prefix_clustering_effectiveness(self):
        """
        Higher prefix_freq should increase clustering.
        We check three signals:
          - average run length
          - neighbor same-prefix ratio
          - prefix concentration (HHI)
        """
        n = 20_000  # < 100k
        low = gen_words_with_prefix_freq(n, prefix_freq=0.0, seed=123, unique=False)
        high = gen_words_with_prefix_freq(n, prefix_freq=0.8, seed=123, unique=False)

        arl_low = avg_run_length(low)
        arl_high = avg_run_length(high)
        self.assertGreater(arl_high, max(arl_low * 3.0, 3.0))  # robust gap

        r_low = neighbor_same_prefix_ratio(low)
        r_high = neighbor_same_prefix_ratio(high)
        self.assertGreater(r_high, r_low + 0.15)               # clear increase

        hhi_low = prefix_hhi(low)
        hhi_high = prefix_hhi(high)
        self.assertGreater(hhi_high, hhi_low)                  # more concentration

    def test_unique_mode_no_duplicates(self):
        n = 20_000  # safely below any 1/1.1 unique cap and <100k
        words = gen_words_with_prefix_freq(n, prefix_freq=0.2, seed=9, unique=True)
        self.assertEqual(len(words), n)
        self.assertEqual(len(set(words)), n)

    def test_same_seed_reproducibility(self):
        n = 10_000
        a = gen_words_with_prefix_freq(n, prefix_freq=0.5, seed=2024, unique=False)
        b = gen_words_with_prefix_freq(n, prefix_freq=0.5, seed=2024, unique=False)
        c = gen_words_with_prefix_freq(n, prefix_freq=0.5, seed=2025, unique=False)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_invalid_num_words_raises(self):
        with self.assertRaises(ValueError):
            gen_words_with_prefix_freq(0, prefix_freq=0.3, seed=1, unique=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
