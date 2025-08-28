import random
import math
import os
import secrets
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


### ================= URL Generation Probability Config ================= ###

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


# --- Path segment probability config --- #
slug_separators = [
  "-",     # hyphen in slugs
  "_",     # underscore in slugs
  " ",   # encoded space
]

slug_separator_weights = [
  0.82,   # "-" most common in slugs
  0.12,   # "_" less common
  0.06,   # " " rare but realistic
]

sub_segments = [1, 2, 3, 4, 5, 6, 7, 8]
sub_segment_weights = [0.30, 0.23, 0.18, 0.12, 0.08, 0.05, 0.03, 0.01]



### ================= URL Generation Functions ================= ###

# Pulling list of top domains from Tranco
def load_domains(n=100_000, cache_path=domain_cache_path, s=1.1):
  """Load top n domains from Tranco list, with weights based on Zipf's law."""
  if n <= 0 or n > 1_000_000:
    raise ValueError("n must be between 1 and 1,000,000")
  t = Tranco(cache=True, cache_dir=cache_path)
  try:
    latest_list = t.list(subdomains=True)
  except TypeError:
    latest_list = t.list()
  domains = latest_list.top(n)
  weights_zipf = [1 / ((r+1) ** s) for r in range(n)]
  return domains, weights_zipf


def sample_host(domains, weights, rng, num_hosts=1):
  """Choose host domain(s) from a list of domains with given weights."""
  if num_hosts <= 0 or num_hosts > len(domains):
    raise ValueError(f"num_hosts must be greater than 0 and less than {len(domains)}")
  if num_hosts == 1:
    return rng.choices(domains, weights=weights, k=1)[0]
  return rng.choices(domains, weights=weights, k=num_hosts)


def pick_scheme(rng):
  """Pick a scheme (http or https) with a realistic probability."""
  return rng.choices(["http", "https"], weights=[0.12, 0.88], k=1)[0]


## ----- Path Generation Functions ----- ##

def slug(rng, min_len=2, max_len=12, digit_p=0.15, sep_p=0.15):
  pool = string.ascii_lowercase + (string.digits if rng.random() < digit_p else "")
  s = "".join(rng.choices(pool, k=rng.randint(min_len, max_len)))
  if rng.random() < sep_p:
    if len(s) > 3:
      indx = rng.randint(2, len(s) - 2)
      seperator = rng.choices(slug_separators, slug_separator_weights, k=1)[0]
      s = s[:indx] + seperator + s[indx:]
  return quote(s, safe='-_.~')
  

def segment(rng, slug_p):
  """Generate a single path segment."""
  num_segs = rng.choices(sub_segments, weights=sub_segment_weights, k=1)[0]
  for i in range(num_segs):
    if rng.random() < slug_p:
      yield slug(rng)
    else:
      yield quote(rng.choice(WORDS_BROAD).lower(), safe='-_.~')
    if i < num_segs - 1:
      yield rng.choices(slug_separators, weights=slug_separator_weights, k=1)[0]


def gen_paths(rng, slug_p=0.3):
  """Generate a random path with a depth up to 5.
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
    segs.append("".join(segment(rng, slug_p)))
    slug_p += ((1 - slug_p) * 0.15)

  path += "/".join(segs)
  if rng.random() < 0.3:
    path += '.' + rng.choices(file_paths, weights=file_path_weights, k=1)[0]
  else:
    path += '/'
  return path


## ----- Query String Generation Functions ----- ##

param_keys = ["q","id","page","ref","utm_source","utm_medium","utm_campaign",
  "utm_term","utm_content","lang","session","token","fbclid"]

param_weights = [0.15, 0.13, 0.13, 0.10, 0.06, 0.06, 0.05, 0.03, 
     0.03, 0.06, 0.10, 0.05, 0.05]



def param_pair(rng, seen):
  """Generate a single key-value pair for a query string."""
  kw = zip(param_keys, param_weights)
  new_keys, new_weights = zip(*[duo for duo in kw if duo[0] not in seen])
  key = rng.choices(new_keys, weights=new_weights, k=1)[0]
  seen.add(key)
  
  if key == 'q':  # slugified words joined with + or percent-encoded spaces, can be very long
    nw = [1,2,3,4,5,6,8,12]
    nw_weights = [0.25,0.25,0.2,0.12,0.08,0.05,0.03,0.02]
    num_words = rng.choices(nw, weights=nw_weights, k=1)[0]
    search_words = rng.choices(WORDS_COMMON, k=num_words)
    space_sym = '+'
    if rng.random() < 0.2:
      space_sym = "%20"
    val = space_sym.join(search_words)

  elif key == 'id': # Digits only
    val = str(rng.randint(1, 10**7))
  
  elif key in ['fbclid', 'ref', 'token', 'session']: # long random hex or base64-like tokens (
    if rng.random() < 0.6:
      bytes_len = rng.choice([8,12,16,24,32])
      val = secrets.token_hex(bytes_len)
    else:
      val = slug(rng, min_len=16, max_len=48, digit_p=0.33, sep_p=0.0)

  elif key == "page":
    val = str(rng.randint(1, 50))

  elif key == "lang": # language code
    val = rng.choice(["en","en-us","es","fr","de","pt-br","it","ja","zh-cn","ru","nl"])
    
  else: # 1-3 word strings seperated by + or %20
    num_words = rng.randint(1, 3)
    search_words = rng.choices(WORDS_COMMON, k=num_words)
    space_sym = '+'
    if rng.random() < 0.2:
      space_sym = "%20"
    val = space_sym.join(search_words)
  return key + '=' + val
  

def query_string(rng):
  """Generate a random query string (or none) with a random number of parameters."""
  np = [0, 1, 2, 3, 4, 5, 6, 7]
  np_weights = [0.40, 0.35, 0.11, 0.09, 0.03, 0.015, 0.005, 0.002]
  num_params = rng.choices(np, weights=np_weights, k=1)[0]
  if num_params == 0:
    return ''
  pairs = []
  seen = set()
  for _ in range(num_params):
    pairs.append(param_pair(rng, seen))
  pairs.sort()
  return '?' + '&'.join(pairs)



### ================= Final URL Generation Logic ================= ###

def generate_urls(num_urls, seed=None):
  """Generate a list of random URLs."""
  rng = random.Random(seed)
  domains, weights = load_domains()
  urls = []
  for _ in range(num_urls):
    scheme = pick_scheme(rng)
    host = sample_host(domains, weights, rng)
    path = gen_paths(rng)
    query = query_string(rng)
    url = f"{scheme}://{host}{path}{query}"
    urls.append(url)
  return urls



