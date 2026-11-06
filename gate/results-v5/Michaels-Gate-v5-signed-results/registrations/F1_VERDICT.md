# F1 verdict: DESIGN WALL. Immutable; do not edit. Any revision is F2 and must be pre-registered first.
Run: q8F.py at commit 572a4fe (F1_IMPL.json). Results are in q8F1_results.json, log in q8F1.log. Runtime 159 s.
PASS: A1 ratchet harm, A2 outlier, A3 clean FRR 0.0005, A5 coverage min 0.940, A7 alarm_cover harm 0, A8 park_flood (queue ≤16, window ≤20, 0 park admits, beacons verify, feed origin unaffected), A9 adaptive harm 0.
FAIL A4: drift5 FRR 0.0686 [0.0672, 0.0699], holdout5 0.0427 (UCL 0.0438 passes; drift5 fails).
  Diagnosis: A (the geometry-only arm) has the same FRR (0.0672), and so does C (0.0687). The rejects come from the inherited anchor/residual hull on rare items (sigma 0.06, 8% of events), not from the imprint or the park.
  This is an outer-loop property: meeting the bound would require changing the residual cap or the corpus, and both are frozen. Per the spec, we stop with proof rather than retune.
  F still improves on D/E (0.090 FRR, 0.744 coverage) and removes their HOLDING collapse.
FAIL A6 bulk: pkg_bulk_diluted max non-imprint memory fraction 0.391 (E: 0.298, bound 0.30).
  Diagnosis: E's ≤0.30 depended on the rudder purge, which F removed. Alarm-and-park therefore gives up a real E protection.
  A remedy has to be lineage-scoped and must not charge the write budget. Example: a per-lineage memory share cap enforced at admission, i.e. a Crimson per-origin quota applied to memory and not only to parks. That is an F2 design change.
Exploratory label: none of the above came from tuning; the corpora were frozen at e125422.
