import random
import math
import os
import string
from tranco import Tranco
from urllib.parse import urlparse, quote

FILE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load word lists
with open(os.path.join(FILE_DIR, "words_common.txt"), "r", encoding="utf-8") as f:
    WORDS_COMMON = [w for w in f.read().splitlines() if w]

with open(os.path.join(FILE_DIR, "words_alpha.txt"), "r", encoding="utf-8") as f:
    WORDS_BROAD = [w for w in f.read().splitlines() if w]
  
domain_cache_path = os.path.join(FILE_DIR, "tranco_cache")


# --- List of file extensions and their weights for path generation --- #
file_paths = [
  # Code / markup
  "js","mjs","css","html","htm",
  # Images
  "jpg","jpeg","png","gif","webp","svg","ico",
  # Fonts
  "woff2","woff","ttf","otf","eot",
  # Docs / data
  "pdf","json","xml","txt","csv",
  # Media
  "mp4","webm","mov","mp3","ogg",
]

file_path_weights = [
  # Code / markup
  0.283058, 0.010266, 0.095455, 0.029750, 0.004057,
  # Images
  0.103223, 0.025806, 0.090288, 0.050907, 0.028495, 0.015048, 0.005123,
  # Fonts
  0.080540, 0.009943, 0.003977, 0.002983, 0.001989,
  # Docs / data
  0.029830, 0.029830, 0.009943, 0.011932, 0.007955,
  # Media
  0.034801, 0.014915, 0.004972, 0.009943, 0.004972,
]


# --- Path separators and their weights for path generation --- #
path_separators = [
  "/",     # path delimiter
  "-",     # hyphen in slugs
  "_",     # underscore in slugs
  "%20",   # encoded space
]

path_separator_weights = [
  0.65,   # "/" dominates (actual directory separator)
  0.23,   # "-" most common in slugs
  0.12,   # "_" less common
  0.06,   # "%20" rare but realistic
]


# Pulling list of top domains from Tranco
def load_domains(n=100_000, cache_path=domain_cache_path, s=1.1):
  """Load top n domains from Tranco list, with weights based on Zipf's law."""
  if n <= 0 or n > 1_000_000:
    raise ValueError("n must be between 1 and 1,000,000")
  t = Tranco(cache=True, cache_dir=cache_path)
  latest_list = t.list(subdomains=True)
  domains = latest_list.top(n)
  weights_zipf = [1 / ((r+1) ** s) for r in range(n)]
  return domains, weights_zipf


def sample_host(domains, weights, rng, num_hosts=1):
  """Choose host domain(s) from a list of domains with given weights."""
  if num_hosts <= 0 or num_hosts > len(domains):
    raise ValueError(f"num_hosts must be greater than 0 and less than {num_hosts+1}")
  if num_hosts == 1:
    return rng.choices(domains, weights=weights, k=1)[0]
  return rng.choices(domains, weights=weights, k=num_hosts)


def pick_scheme(rng):
  """Pick a scheme (http or https) with a realistic probability."""
  return rng.choices(["http", "https"], weights=[0.12, 0.88], k=1)[0]
  

def slug(rng, min_len=2, max_len=16, digit_p=0.15):
  pool = string.ascii_lowercase + (string.digits if rng.random() < digit_p else "")
  s = "".join(rng.choices(pool, k=rng.randint(min_len, max_len)))
  return quote(s)


def gen_paths(rng, slug_p=0.3):
  """Generate a random path with a given maximum depth.
    slug_p: probability of a segment being a slug (vs. a common word)."""
  if slug_p < 0 or slug_p > 1:
    raise ValueError("slug_p must be between 0 and 1")
    
  num_segs, seg_weights = zip(*[
    (0, 0.20), (1, 0.30), (2, 0.25), (3, 0.13), (4, 0.10), (5, 0.02)
  ])
  depth = rng.choices(num_segs, weights=seg_weights, k=1)[0]
  path = "/"
  segs = []
  if depth == 0:
    return path
    
  
  for _ in range(depth):
    if rng.random() < slug_p:
      path += slug(rng)
    else:
      path += quote(rng.choice(WORDS_COMMON).lower())
    slug_p += ((1 - slug_p) * 0.2)
    path += rng.choices(path_separators, weights=path_separator_weights, k=1)[0]

  
  if rng.random() < 0.3:
    path += '.' + rng.choices(file_paths, weights=file_path_weights, k=1)[0]
  else:
    path += '/'
  return path


def is_valid_url(u):
  p = urlparse(u)
  return bool(p.scheme and p.netloc)
