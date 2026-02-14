  ranker options:
  - 'network-simplex' (default): Optimal rank assignment,
  minimizes edge length
  - 'tight-tree': Produces more compact trees
  - 'longest-path': Emphasizes the deepest reasoning chains
  (good for highlighting argument depth)
#### Hypothetical structural rating system
CONNECTION: "Pfizer trial data" --[supports]--> "Vaccines are safe"

  CHALLENGES (visible on edge):
  ├─ "Trial period too short for long-term effects" (24 users agree)
  ├─ "Sample size adequate for statistical power" (31 users agree)
  └─ "Placebo group data confirms causation" (18 users agree)

  LOGICAL CRITIQUE OPTIONS:
  [Sample size insufficient]
  [Confounding variables present]
  [Correlation not causation]
  [Source credibility questioned]
  [Data interpretation disputed]

  Instead of "I rate this 60%", users click:
  - "I challenge this on methodological grounds" → selects challenge type → explains

We have "dimensions" in the comments field to build out, for people to chose whether they 
are ranking accuracy, usefulness, etc. 