#!/usr/bin/env python3
# dev_tests/url-ip_tests.py
"""
Tests for:
  - components.work_loads.url_generator.generate_urls
  - components.work_loads.ip_generator.IPGenerator / IPConfig

Focus:
  1) Validity (parseable URLs, hostname rules, IPv4 addresses)
  2) Realism heuristics (warnings only): HTTPS share, common TLD share, private mix vs weights, etc.

Notes:
  - By default we ACCEPT scheme-less URLs like "example.com/a/b" (set STRICT_SCHEME=True to force http/https).
  - We ENFORCE no URL fragments if STRICT_NO_FRAGMENTS=True.
  - IPs are validated as IPv4 only (per your generator).
"""

from __future__ import annotations

import sys
import os
import re
import time
import math
import json
import random
import statistics as stats
from typing import List, Dict, Tuple, Optional
from collections import Counter
from urllib.parse import urlparse, unquote
import ipaddress

# ================================
# CONFIG
# ================================
STRICT_SCHEME = False          # accept scheme-less URLs if False
STRICT_NO_FRAGMENTS = True     # fail if any URL has a fragment
URL_DEFAULT_SCHEME = "http"    # used only to parse scheme-less URLs for validation

# ================================
# IMPORTS (project wiring)
# ================================
FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(FILE_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from components.work_loads.url_generator import generate_urls  # type: ignore
except Exception:
    print("[FATAL] Could not import components.work_loads.url_generator.generate_urls")
    raise

try:
    from components.work_loads.ip_generator import IPGenerator, IPConfig  # type: ignore
except Exception:
    print("[FATAL] Could not import components.work_loads.ip_generator.{IPGenerator, IPConfig}")
    raise

# ================================
# Pretty printing
# ================================
USE_COLOR = sys.stdout.isatty()
def c(txt, code): return f"\033[{code}m{txt}\033[0m" if USE_COLOR else txt
def OK(txt="OK"): return c(txt, "92")
def BAD(txt="FAIL"): return c(txt, "91")
def WARN(txt="WARN"): return c(txt, "93")
def HDR(txt): return c(txt, "96")
def hr(char="─", width=80): print(char * width)
def fmt_pct(x, total): return "0.00%" if total == 0 else f"{(100.0 * x / total):.2f}%"

# ================================
# URL validation
# ================================
LABEL_RE = re.compile(r"^[a-z0-9-]{1,63}$", re.IGNORECASE)
TLD_RE = re.compile(r"^[a-z]{2,63}$", re.IGNORECASE)
PATH_SEG_RE = re.compile(r"^[A-Za-z0-9._~!$&'()*+,;=:@%-]*$")

COMMON_TLDS = {
    "com","org","net","io","edu","gov","co","us","uk","de","jp","fr","au","ca","nl","it","es"
}

def is_valid_hostname(host: str) -> bool:
    """DNS host only (not IP literal) — URL generator should primarily produce hostnames."""
    if not host or len(host) > 253:
        return False
    labels = host.split(".")
    for label in labels:
        if not label or label.startswith("-") or label.endswith("-"):
            return False
        if not LABEL_RE.match(label):
            return False
    tld = labels[-1]
    return bool(TLD_RE.match(tld))

def _parse_url_lenient(u: str):
    """If scheme-less, prefix '//' to allow urlparse to fill hostname."""
    pu = urlparse(u)
    if pu.scheme == "" and pu.netloc == "" and pu.path and not STRICT_SCHEME:
        pu = urlparse(f"//{u}", scheme=URL_DEFAULT_SCHEME)
    return pu

def analyze_urls(urls: List[str]) -> Dict[str, any]:
    res = {
        "total": len(urls),
        "valid": 0,
        "invalid": 0,
        "schemes": Counter(),
        "tlds": Counter(),
        "hosts_with_www": 0,
        "with_query": 0,
        "with_fragment": 0,
        "avg_path_depth": 0.0,
        "path_depths": [],
        "examples_invalid": [],
    }

    for u in urls:
        try:
            pu = _parse_url_lenient(u)
        except Exception:
            res["invalid"] += 1
            if len(res["examples_invalid"]) < 5:
                res["examples_invalid"].append(u)
            continue

        scheme = pu.scheme.lower()
        host = (pu.hostname or "").lower()
        path = pu.path or ""
        query = pu.query or ""
        fragment = pu.fragment or ""

        # Scheme rule
        if STRICT_SCHEME:
            scheme_ok = scheme in {"http", "https"}
        else:
            scheme_ok = (scheme in {"http", "https"}) or (scheme == "" and host)

        # Hostname rule (DNS only; not accepting IP literals for URL host realism)
        host_ok = is_valid_hostname(host) if host else False

        # Path charset
        path_ok = True
        if path:
            segs = [s for s in path.split("/") if s]
            for seg in segs:
                if not PATH_SEG_RE.match(unquote(seg)):
                    path_ok = False
                    break
            res["path_depths"].append(len(segs))
        else:
            res["path_depths"].append(0)

        if scheme_ok and host_ok and path_ok:
            res["valid"] += 1
        else:
            res["invalid"] += 1
            if len(res["examples_invalid"]) < 5:
                res["examples_invalid"].append(u)

        res["schemes"][scheme] += 1
        if host and "." in host and not host.replace(".", "").isdigit():
            tld = host.split(".")[-1]
            res["tlds"][tld] += 1
        if host.startswith("www."):
            res["hosts_with_www"] += 1
        if query:
            res["with_query"] += 1
        if fragment:
            res["with_fragment"] += 1

    if res["path_depths"]:
        res["avg_path_depth"] = stats.mean(res["path_depths"])
    return res

def print_url_report(analysis: Dict[str, any]):
    total, valid, invalid = analysis["total"], analysis["valid"], analysis["invalid"]
    hr()
    print(HDR("URL GENERATION — VALIDITY SUMMARY"))
    print(f"Total URLs: {total}")
    print(f"Valid: {OK(str(valid))}  ({fmt_pct(valid, total)})")
    print(f"Invalid: {(BAD if invalid else OK)(str(invalid))} ({fmt_pct(invalid, total)})")

    print()
    print(HDR("Scheme distribution"))
    for s, cnt in analysis["schemes"].most_common():
        print(f"  {s or '<none>' :<8}  {cnt:>7}  ({fmt_pct(cnt, total)})")

    print()
    print(HDR("TLD top 10"))
    for tld, cnt in analysis["tlds"].most_common(10):
        marker = "★" if tld in COMMON_TLDS else " "
        print(f"  {tld:<6} {cnt:>7}  ({fmt_pct(cnt, total)}) {marker}")

    print()
    print(HDR("Other URL structure stats"))
    print(f"  Hosts starting with 'www.': {analysis['hosts_with_www']:>6} ({fmt_pct(analysis['hosts_with_www'], total)})")
    print(f"  With query string       : {analysis['with_query']:>6} ({fmt_pct(analysis['with_query'], total)})")
    print(f"  With fragment (#)       : {analysis['with_fragment']:>6} ({fmt_pct(analysis['with_fragment'], total)})")
    print(f"  Avg. path depth         : {analysis['avg_path_depth']:.2f}")

    if analysis["examples_invalid"]:
        print()
        print(HDR("Examples of invalid URLs (first 5)"))
        for u in analysis["examples_invalid"]:
            print(f"  - {u}")

    print()
    print(HDR("Realism heuristics (warnings only)"))
    warnings = []
    https_share = analysis["schemes"].get("https", 0) / max(1, total)
    if https_share < 0.5:
        warnings.append(f"HTTPS share is {https_share:.1%}; consider >= 60% for modern web realism.")
    if STRICT_NO_FRAGMENTS and analysis["with_fragment"] > 0:
        warnings.append("Some URLs include fragments (#), but fragments were intended to be excluded.")
    common_tld_share = sum(cnt for tld, cnt in analysis["tlds"].items() if tld in COMMON_TLDS) / max(1, sum(analysis["tlds"].values()))
    if common_tld_share < 0.35 and len(analysis["tlds"]) > 0:
        warnings.append(f"Common TLD share is {common_tld_share:.1%}; consider boosting common TLDs for realism.")
    if warnings:
        for w in warnings:
            print("  " + WARN("! ") + w)
    else:
        print("  " + OK("All realism heuristics look good."))

# ================================
# IP validation (IPv4 only)
# ================================
RFC1918_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]
UNROUTABLE_RANGES = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
]

def is_private_ipv4(ip: ipaddress.IPv4Address) -> bool:
    return any(ip in n for n in RFC1918_RANGES)

def is_unroutable_or_reserved(ip: ipaddress.IPv4Address) -> bool:
    return any(ip in n for n in UNROUTABLE_RANGES)

def analyze_ips(ips: List[str]) -> Dict[str, any]:
    res = {
        "total": len(ips),
        "valid": 0,
        "invalid": 0,
        "private": 0,
        "public": 0,
        "classA_private": 0,
        "classB_private": 0,
        "classC_private": 0,
        "unroutable_reserved": 0,
        "examples_invalid": [],
    }
    for s in ips:
        try:
            ip = ipaddress.IPv4Address(s)  # IPv4 only, per your generator
        except Exception:
            res["invalid"] += 1
            if len(res["examples_invalid"]) < 5:
                res["examples_invalid"].append(s)
            continue

        res["valid"] += 1
        if is_private_ipv4(ip):
            res["private"] += 1
            if ip in RFC1918_RANGES[0]:
                res["classA_private"] += 1
            elif ip in RFC1918_RANGES[1]:
                res["classB_private"] += 1
            elif ip in RFC1918_RANGES[2]:
                res["classC_private"] += 1
        else:
            res["public"] += 1
            if is_unroutable_or_reserved(ip):
                res["unroutable_reserved"] += 1
    return res

def print_ip_report(analysis: Dict[str, any], cfg: Optional[IPConfig]):
    total = analysis["total"]
    valid = analysis["valid"]
    invalid = analysis["invalid"]
    private_ = analysis["private"]
    public_ = analysis["public"]

    hr()
    print(HDR("IP GENERATION — VALIDITY SUMMARY"))
    print(f"Total IPs: {total}")
    print(f"Valid IPv4: {OK(str(valid))}  ({fmt_pct(valid, total)})")
    print(f"Invalid: {(BAD if invalid else OK)(str(invalid))} ({fmt_pct(invalid, total)})")

    print()
    print(HDR("Private vs Public split"))
    print(f"  Private: {private_:>7} ({fmt_pct(private_, total)})")
    print(f"  Public : {public_:>7} ({fmt_pct(public_, total)})")

    print()
    print(HDR("Private sub-range split"))
    pa, pb, pc = analysis["classA_private"], analysis["classB_private"], analysis["classC_private"]
    pvt_total = max(1, private_)
    print(f"  10.0.0.0/8     : {pa:>7} ({fmt_pct(pa, pvt_total)})")
    print(f"  172.16.0.0/12  : {pb:>7} ({fmt_pct(pb, pvt_total)})")
    print(f"  192.168.0.0/16 : {pc:>7} ({fmt_pct(pc, pvt_total)})")

    if analysis["unroutable_reserved"]:
        print()
        print(HDR("Reserved/unroutable seen among public (informational)"))
        print(f"  Count: {analysis['unroutable_reserved']} ({fmt_pct(analysis['unroutable_reserved'], max(1, public_))})")

    print()
    print(HDR("Realism heuristics (warnings only)"))
    warnings = []
    if cfg is not None and total > 0:
        observed_public = public_ / total
        if abs(observed_public - cfg.public_share) > 0.10:
            warnings.append(
                f"Observed public share {observed_public:.1%} differs from target {cfg.public_share:.1%} by >10pp."
            )
        # private weights check
        if private_ > 0 and cfg.private_weights:
            w = cfg.private_weights
            exp = [float(w.get("a", 0)), float(w.get("b", 0)), float(w.get("c", 0))]
            tw = sum(exp) or 1.0
            exp = [x / tw for x in exp]
            obs = [
                analysis["classA_private"]/max(1, private_),
                analysis["classB_private"]/max(1, private_),
                analysis["classC_private"]/max(1, private_),
            ]
            labels = ["10/8", "172.16/12", "192.168/16"]
            for i in range(3):
                if abs(obs[i] - exp[i]) > 0.10:
                    warnings.append(f"Private mix off for {labels[i]}: observed {obs[i]:.1%} vs expected {exp[i]:.1%}.")
    if warnings:
        for w in warnings:
            print("  " + WARN("! ") + w)
    else:
        print("  " + OK("All realism heuristics look good."))

# ================================
# Test runners
# ================================
def run_url_tests(sample_size: int = 3000, seed: Optional[int] = 1337):
    if seed is not None:
        random.seed(seed)

    t0 = time.perf_counter()
    try:
        urls = generate_urls(sample_size)  # preferred signature
    except TypeError:
        # fallback: call with no args and replicate to requested size
        urls = generate_urls()
        if not isinstance(urls, list) or len(urls) < sample_size:
            urls = (urls * math.ceil(sample_size / max(1, len(urls))))[:sample_size]
    t1 = time.perf_counter()

    analysis = analyze_urls(urls)
    print(HDR("URL generation timing"))
    print(f"  Generated {len(urls)} URLs in {(t1 - t0):.3f}s "
          f"({len(urls)/max(1,(t1 - t0)):.0f} urls/sec)")
    print_url_report(analysis)

    hard_fail = []
    if analysis["invalid"] > 0:
        hard_fail.append(f"Found {analysis['invalid']} invalid URLs.")
    if STRICT_NO_FRAGMENTS and analysis["with_fragment"] > 0:
        hard_fail.append("URLs include fragments (#) but fragments were to be excluded.")

    passed = len(hard_fail) == 0
    if not passed:
        print()
        print(BAD("HARD FAILS"))
        for msg in hard_fail:
            print("  - " + msg)
    return passed, analysis

def run_ip_tests(sample_size: int = 20000, seed: Optional[int] = 4242):
    cfg = IPConfig(seed=seed)  # use your defaults (public_share, private_weights)
    gen = IPGenerator(cfg)

    t0 = time.perf_counter()
    # Prefer batch (present in your class); fallback to single loop if needed.
    if hasattr(gen, "batch") and callable(getattr(gen, "batch")):
        ips = gen.batch(sample_size)
    else:
        ips = [gen.single() for _ in range(sample_size)]
    t1 = time.perf_counter()

    analysis = analyze_ips(ips)
    print(HDR("IP generation timing"))
    print(f"  Generated {len(ips)} IPs in {(t1 - t0):.3f}s "
          f"({len(ips)/max(1,(t1 - t0)):.0f} ips/sec)")
    print_ip_report(analysis, cfg)

    hard_fail = []
    if analysis["invalid"] > 0:
        hard_fail.append(f"Found {analysis['invalid']} invalid IPs.")
    public_total = max(1, analysis["public"])
    if analysis["unroutable_reserved"] / public_total > 0.01:
        hard_fail.append(
            f"Unroutable/reserved among public is {analysis['unroutable_reserved']} "
            f"({fmt_pct(analysis['unroutable_reserved'], public_total)} of public)."
        )

    passed = len(hard_fail) == 0
    if not passed:
        print()
        print(BAD("HARD FAILS"))
        for msg in hard_fail:
            print("  - " + msg)
    return passed, analysis

# ================================
# MAIN
# ================================
def main():
    print(HDR("Running URL & IP generation tests (IP=v2 tailored)"))
    hr()

    URL_N = int(os.environ.get("URL_TEST_N", "3000"))
    IP_N = int(os.environ.get("IP_TEST_N", "20000"))

    URL_SEED = os.environ.get("URL_TEST_SEED")
    IP_SEED = os.environ.get("IP_TEST_SEED")
    url_seed = int(URL_SEED) if URL_SEED is not None else 1337
    ip_seed = int(IP_SEED) if IP_SEED is not None else 4242

    url_passed, url_stats = run_url_tests(URL_N, url_seed)
    ip_passed, ip_stats = run_ip_tests(IP_N, ip_seed)

    hr()
    overall = url_passed and ip_passed
    print(HDR("OVERALL RESULT"))
    print(OK("All hard checks passed.") if overall else BAD("One or more hard checks failed (see above)."))

    print()
    print(HDR("Quick JSON summary (copyable)"))
    summary = {
        "urls": {
            "total": url_stats.get("total"),
            "valid": url_stats.get("valid"),
            "invalid": url_stats.get("invalid"),
            "https_share": (url_stats["schemes"].get("https", 0) / max(1, url_stats["total"])) if url_stats else None,
            "avg_path_depth": url_stats.get("avg_path_depth"),
            "with_query": url_stats.get("with_query"),
            "with_fragment": url_stats.get("with_fragment"),
            "top_tlds": url_stats.get("tlds").most_common(5) if url_stats else [],
        },
        "ips": {
            "total": ip_stats.get("total"),
            "valid": ip_stats.get("valid"),
            "invalid": ip_stats.get("invalid"),
            "private": ip_stats.get("private"),
            "public": ip_stats.get("public"),
            "classA_private": ip_stats.get("classA_private"),
            "classB_private": ip_stats.get("classB_private"),
            "classC_private": ip_stats.get("classC_private"),
            "unroutable_reserved_public": ip_stats.get("unroutable_reserved"),
        },
        "overall_passed": overall,
        "config": {
            "STRICT_SCHEME": STRICT_SCHEME,
            "STRICT_NO_FRAGMENTS": STRICT_NO_FRAGMENTS
        }
    }
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
