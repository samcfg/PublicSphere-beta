● Claim Rating Algorithm v2

  Core principles:
  1. Within argument paths: Multiply source strength × connection validity (a chain's strength requires both strong evidence AND
  strong logic)
  2. Compound connections: Product of all parent inputs (conjunction is only as strong as combined reliability)
  3. Multiple independent paths: Probabilistic reinforcement (two 70% arguments → 91% combined, not 140%)
  4. Contradictions: Subtract aggregated contradiction strength from support strength

  Algorithm:
```
  def calculate_claim_rating(claim):
      supporting_paths = []
      contradicting_paths = []

      for connection in claim.incoming_connections:
          # Get parent node ratings (recursive for claims, direct for sources)
          parent_ratings = [get_node_rating(p) for p in connection.parents]

          if connection.type in ["and", "nand"]:
              # Compound: multiply all parent strengths
              # (all must be strong for conjunction to hold)
              combined = product(parent_ratings) / (100 ** (len(parent_ratings)-1))
          else:
              # Single parent
              combined = parent_ratings[0]

          # Path strength = parent(s) strength × connection logic
          path = (combined/100) × (connection.rating/100) × 100

          if connection.type in ["supports", "and"]:
              supporting_paths.append(path)
          else:
              contradicting_paths.append(path)

      # Aggregate using probabilistic reinforcement
      # P(A or B) = 1 - (1-A)(1-B)
      support = 100 × (1 - ∏[1 - p/100 for p in supporting_paths])
      contradict = 100 × (1 - ∏[1 - c/100 for c in contradicting_paths])

      return clamp(support - contradict, 0, 100)
```
  Example:
  - Source A: 80 factuality
  - Connection: 90 logic
  - Path strength: (80/100) × (90/100) × 100 = 72

