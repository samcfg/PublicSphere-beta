Graph Navigation Design

  Context-Based Navigation
    Contexts are selected by selecting a conclusion node, and displaying all the premise nodes and connections leading to it. 
  Users start sessions by defining their analytical context:

  with conclusion("climate change is anthropogenic") as ctx:
      ctx.tree()      # Show full reasoning tree
      ctx.tree(2)     # Show only 2 levels back

  This generates a temporary coordinate system for the session,
   eliminating UUID typing.

  Coordinate System

  Single Conclusion:
  - Nodes: 0 (conclusion), a1, a2 (height a), b1, b2, b3
  (height b)
  - Connections: a1c0 (from a1 to conclusion), b2ca1 (from b2
  to a1)

  Multiple Conclusions:
  - Add prefix: A0, Aa1, Aa2 (first conclusion), B0, Ba1, Ba2
  (second conclusion)
  - Handles shared premises across different reasoning trees

  Usage

  Compact codes for typing:
  ctx[a1]           # Quick node reference
  ctx[b2ca1]        # Connection reference

  Coordinate display for readability:
  a1 [1.0] temperature records show warming trend
  b2 [2.1] NOAA measurements
  b2ca1: [2.1]→[1.0] (connection with arrow)

  Design Principles

  - Universal addressing: Same scheme for all node types
  (Claims, Sources) and edge types
  - Typing efficiency: 2-3 characters instead of UUIDs
  - Visual clarity: Coordinates show logical structure
  - Depth control: Users choose scope of analysis

  The system translates compact codes to readable coordinates,
  giving users both efficiency and comprehension.