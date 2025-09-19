Claim1 -[group:123, logic:AND]→ Target
Claim2 -[group:123, logic:AND]→ Target

  # Both edges get identical metadata
  edge1_props = {
      'id': str(uuid.uuid4()),           # Individual edge ID
      'composite_id': composite_id,       # Shared group ID
      'logic_type': 'AND',
      'strength': 0.85,
      'notes': 'Both claims strongly support conclusion'
  }

  edge2_props = {
      'id': str(uuid.uuid4()),           # Different individual ID  
      'composite_id': composite_id,       # Same group ID
      'logic_type': 'AND',               # Same metadata
      'strength': 0.85,
      'notes': 'Both claims strongly support conclusion'
  }

so as a measure to make versioning easier, all of the language 
  (language.py) around the compound edges must treat them atomically, and in
   conjunction with the shared metadata, they will be effectively 
  syncronized in terms of versioning, as well as readably converging for the
   user. 
Visually the convergence of the edges will be dicteted by calculating coordinates by triangulating node positions = setting bezier control points for the two edges. This will be done in the same development step as when we make the arguments hierarchical, theoretically. 