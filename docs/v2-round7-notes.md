# V2 Round 7 Notes

This round focuses on ranking quality and API normalization foundations.

## Improvements

- search now considers `aliases` and `tags` in record matching
- search hits now carry a `score`
- ranking now includes basic retention-aware weighting using importance and status
- graph-expanded hits are scored slightly below direct hits and merged into sorted final results

## Why this matters

These changes move V2 closer to practical use:
- important active memories surface earlier
- archived / superseded records can be deprioritized
- alias/tag matching improves robustness on long-tail queries
- future HTTP/API layers can expose scores and ranking explanations
