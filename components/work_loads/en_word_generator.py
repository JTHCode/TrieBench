import random
import math
import os
from collections import defaultdict

# Load word lists
FILE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(FILE_DIR, "words_common.txt"), "r", encoding="utf-8") as f:
    WORDS_COMMON = [w for w in f.read().splitlines() if w]

with open(os.path.join(FILE_DIR, "words_alpha.txt"), "r", encoding="utf-8") as f:
    WORDS_BROAD = [w for w in f.read().splitlines() if w]


## Created dictionary for words with identical first two letters
## This is to generate words with common prefixes
prefix_bucket = defaultdict(list)
for word in WORDS_BROAD:
  prefix_bucket[word[:2]].append(word)
prefixes = list(prefix_bucket.keys())
prefix_weights = [len(prefix_bucket[p]) for p in prefixes]


def generate_random_words(num_words, seed=None, unique=False):
  """
  Return n random words from WORD_LIST.
  - unique=False: sample with replacement (fast, allows duplicates)
  - unique=True: sample without replacement (requires n <= len(WORD_LIST))
  """
  word_list = WORDS_COMMON
  if num_words < 1 or (unique is True and num_words > len(word_list)):
    raise ValueError(f"num_words must be between 1 and {len(word_list)}")
  rng = random.Random(seed)
  if unique:
    return rng.sample(word_list, num_words)
  return rng.choices(word_list, k=num_words)



def gen_words_with_prefix_freq(num_words, prefix_freq=0.0, seed=None, unique=False):
  """Generates a list of words with a given prefix frequency.
  A higher prefix_freq means more words will share common prefixes.
  Prefix frequency is applied logarithmically
  prefix_freq: 0 -> 0.999...
  """
  def _p_eff_log(x, max_mean=100) -> float:
    # Logarithmic mapping of prefix frequency to effective prefix frequency
    if x < 0 or x > 1:
      raise ValueError("Prefix frequency must be between 0 and 1")
    x = max(0.0, min(0.999999, x))
    k = math.log(max_mean)
    p = 1.0 - math.exp(-k * x)
    return min(p, 0.999999)
  prefix_freq = _p_eff_log(prefix_freq)
    
  word_list = WORDS_BROAD
  max_unique = len(word_list) // 1.1
  if num_words < 1 or (unique is True and num_words > max_unique):
    raise ValueError(f"num_words must be between 1 and {max_unique}")
  if prefix_freq < 0 or prefix_freq >= 1:
    raise ValueError("prefix_freq must be between 0 and 1")
  rng = random.Random(seed)
    
  rand_words_list = []
  if unique: 
    seen = set()
    exhausted = set()
    
  while len(rand_words_list) < num_words:
    prefix = rng.choices(prefixes, weights=prefix_weights)[0]
    options = prefix_bucket[prefix]
    sample_word = rng.choice(options)
    if unique:
      if prefix in exhausted or sample_word in seen:
        continue
    rand_words_list.append(sample_word)
    if unique: seen.add(sample_word)
    
    trigger = rng.random()
    while trigger < prefix_freq:
      new_word = rng.choice(options)
      if unique:
        remaining = [w for w in options if (w not in seen)]
        if not remaining:
            exhausted.add(prefix)
            break 
        if new_word in seen:
          new_word = rng.choice(remaining)
      rand_words_list.append(new_word)
      if unique: seen.add(new_word)
      trigger = rng.random()
      if len(rand_words_list) >= num_words:
        break
  return rand_words_list
