# Notes For Creating Work Load Generators #

(NORMALIZATION OFF FOR URLS)
Schemes: ✅
  https:// 88%
  http:// 12%
Chooses host domain with a realistic zip-f like distribution
Path Segments: ✅
  Choose random depth (0-4)
  Fill segments with English words
  End in file path only 5% of the time and only when depth > 0 (.php, .jpg, .jpeg, .png, etc...)
Query Strings (60% probability):
  Chance of 33% for each additional query string (Cap at 8)
  Keys randomly from pool (q, id, utm_source, ref, page, etc)
  Values are slugs or ints
  Joined with &
Fragment Identifiers (7.5% probability):
  Append # followed by random word from pool (section1, section2, comments, etc...)

ORDER: scheme + host + path + query + fragment


Validate with urllib.parse to confirm the are valid URLs
Generate large sample and check probability of elements match the desired frequency


Sources:

Median requests by content type: https://almanac.httparchive.org/en/2022/page-weight"
Top 1m domains used for base URL generation: https://doi.org/10.14722/ndss.2019.23386
Image path sub-distribution for path generation: https://almanac.httparchive.org/en/2022/media
Font path sub-distribution for path generation: https://almanac.httparchive.org/en/2024/fonts



TO DO:
Test URL generator