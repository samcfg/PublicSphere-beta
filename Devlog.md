# 9/3 
## Transcript 1
The atomic units of structured reasoning: Sources
  (evidence/observations), Claims (assertions/conclusions), and Connections
  (logical relationships). This trinity mirrors the fundamental epistemological
  process—we observe reality, form beliefs about it, and establish logical
  relationships between observations and beliefs. To achieve your vision of collaborative thought, the 
  interface should expose these three primitives directly: users should create,
  manipulate, and connect discrete source and claim objects.

● Composite connections solve the multi-premise logical
  arguments naturally—one Connection can aggregate multiple Sources into a single
  Claim with the logical operator built into the Connection object. The
  strength/confidence as a continuous variable (0-1 or 0-100) on each primitive allows
   network-level confidence propagation through graph traversal algorithms. Comments
  sections provide the human interpretive layer without cluttering the formal
  structure. Terminal Claims without incoming Connections become axioms/assumptions by
   definition, making the epistemological foundation explicit rather than hidden. Falsifiability emerges from graph topology.
   have potential Sources that could connect with negative/contradictory
  relationships. This creates a clean separation between the formal reasoning layer
  (the graph) and the contextual/interpretive layer (comments), where users can argue
  about what the formal relationships mean without breaking the underlying logical
  structure. The system becomes both computationally tractable and philosophically
  rigorous.

## Sam's Notes
It seems that the entirely graph database is insufficient for the purposes of rigorous storage, the hybrid aproach is indeed the best. In fact, the majority of storage should be relational, with perhaps only the functional argument mapping being graph, and the nodes and edges are then copied and elaborated in relational analogus. 
## Transcript 2
### Summary
  Argument Mapping Structure:
  - Three primitives: SourceArea (evidence), ClaimArea (assertions), Connection (logical
  relationships)
  - Compound logic handled via connection branching: AND/OR connections split into
  multiple graph branches (BRANCH_A, BRANCH_B) converging on single conclusion
  - UI handles nesting visualization; database stores flat branching structure

  Collaborative Features:
  - Public, collaborative argument graphs where multiple users contribute
  - User ratings on sources/claims/connections aggregate into global_strength values (0-1
   scale)
  - Users explicitly create connections; system does not infer relationships from natural
   language

  Scale & Complexity:
  - Initial expectation: dozens of interconnected claims per SourceExchange article
  - Must be architecturally scalable to arbitrary complexity
  - Falsification emerges from graph topology - connections must be user-created, not
  precomputed

  Development Strategy:
  - Single-user test implementation recommended to validate core argument mapping without
   user management complexity
  - Graph database stores lightweight references; relational handles data integrity,
  versioning, metadata
  - Historical relationship changes reconstructed from relational side, though graph can
  store some metadata

  Key Insight: The argument mapping graph is the innovation; user systems and forum
  functionality are well-understood domains to be added later.

## Tech Stack Decisions: 
+ Initial Prototype design: 
    Python App → PostgreSQL+AGE → Response
+  Eventual Production architecture:
        91    User Request → Python App → PostgreSQL+AGE → JSON Response → Frontend Visualization
        92 +  
        93 +  ## Hybrid Architecture Plan (Full Release)
        94 +  
        95 +  ### Data Storage Strategy:
        96 +  **PostgreSQL+AGE (Graph)**: Current argument structure, reasoning operations
        97 +  - Node types: Source, Claim, User
        98 +  - Relationships: SUPPORTS, CONTRADICTS, IMPLIES, QUALIFIES, PRECEDES
        99 +  - Optimized for: Traversal, pathfinding, reasoning chain analysis
       100 +  
       101 +  **PostgreSQL (Relational)**: Analytics, versioning, user management  
       102 +  - Tables: user_ratings, relationship_history, node_versions, user_profiles
       103 +  - Optimized for: Aggregations, temporal queries, user-centric operations
       104 +  
       105 +  ### Query Distribution:
       106 +  **Graph Database Handles:**
       107 +  - Argument traversal: "Find all evidence supporting claim X"
       108 +  - Reasoning chains: "Path from source A to conclusion B" 
       109 +  - Network analysis: "What are the most central claims?"
       110 +  - Real-time argument structure queries
       111 +  
       112 +  **Relational Database Handles:**
       113 +  - User ratings aggregation: "Average strength rating for relationship X"
       114 +  - Temporal reconstruction: "What did argument map look like 5 days ago?"
       115 +  - User analytics: "All ratings by user Y"
       116 +  - Version history and audit trails
       117 +  
       118 +  ### Architecture Benefits:
       119 +  - **Separation of concerns**: Argument logic (graph) vs data management (relational)
       120 +  - **Performance optimization**: Each system handles queries it excels at
       121 +  - **Structural clarity**: Graph topology mirrors argument structure naturally
       122 +  - **Scalability**: Independent optimization of reasoning vs analytics workloads

## Overall Design: 
  1. Core Concept:
  Atomic units: Source (evidence), Claim (assertions), Connection (relationships).

  1. Node Types:
  Node = Entity that exists independently
  - Source: Evidence, observations, data
  - Claim: Assertions, conclusions, hypotheses
  - User: (for single-user version, just one node)

  1. Node Properties Decision:
  What data belongs ON each node vs in separate tables?
  (:Source {
    id: string,           // Required: unique identifier
    content: text,        // The actual evidence/observation
    created_at: datetime, // When was this created?
    confidence: float,    // How reliable is this source?
    source_type: string   // "primary", "secondary", "derived"?
  })

  1. Relationship Type Decisions:
  Relationship = How two nodes connect logically
  From your design: "evidential support, logical implication, contradiction, qualification, temporal precedence"

  1. Relationship Properties:
  -[:SUPPORTS {
    strength: float,      // 0.0-1.0 confidence in this connection
    logic_type: string,   // "AND", "OR", "IMPLIES" 
    created_at: datetime,
    notes: text          // Human interpretation
  }]->

## 9/17
Got the initial skeleton working, where the PS/Graph_DB/src/schema.py file defines the graph db, and using test_data generated, can visualize the db in cytoscape. 
## 9/18
  The plan: 
   1. Put content into nodes and edges
   2. Update the language
   3. get the temporality running
   4. make compound connections
   5. Fill out functionality

  + Notes on Language creation:
   the lowest level means of database manipulation are the following NOTATIONS (Ted Nelson's term instead of language for collections of purpose-built commands):
    - Raw manipulation: SQL + AGE functions (graph management)
    - Data manipulation: Cypher (wrapped in SQL)
    - AGE does the translation: Cypher → internal graph operations
+ get_db singleton: 
    - __init__() (line 12): Constructor, creates PostgreSQL connection pool
  - get_connection() (line 38): Context manager for raw connections
  - get_cursor() (line 64): Context manager for database cursors
  - close() (line 205): Cleanup connection pool

  Graph Management:

  - graph_exists() (line 137): Check if graph exists in ag_graph table
  - create_graph() (line 143): Create new graph via AGE's create_graph()
  function
  - drop_graph() (line 154): Delete graph via AGE's drop_graph() function

  Query Operations:

  - execute_cypher() (line 98): Core function - wraps Cypher in SQL,
  parses AGE JSON results
  - get_graph_stats() (line 166): Node/edge counts using Cypher queries
  - get_node_labels() (line 181): Extract all node types via Cypher
  - get_edge_types() (line 197): Extract all relationship types via Cypher

- Made [[languagecontexts]] design. 
Started editing languages, first made a [[cli]] file so I can use terminal like api. Added delete for node/edge. Next we add edit_content

With the basics of the language, now we'll configure the cytoscape visual for ease of testing. 
- split the js visualization code into 5 files within /src. 
Made the plan for node forking and merging. 

We integrated Django into the project to manage temporal version logging, creating backend/PS_Django_DB/ with a bookkeeper app containing NodeVersion and EdgeVersion models. Django is configured to use the same ostgreSQL publicsphere database as AGE, with UUIDs serving as the consistent identifier format. 
Making logging.py wrapper. 
Made compound connections in the backend. 
Got the hierarchy working with a cytoscape extension called Dagre. 
Next is to plan the major steps before release, designing. 

Made basic source nodes and negative connections together. 
Thinking about security.
added 30 second query timeout within database.py 
Makng users. Admins can't see anon attributions. 
Users made (phase 1 in plan.md)
Superuser, Admin, Moderator hierarchy defined. 
Executing the frontentRevemp plan with some modifications: 
  Formatted all the views, in a standard way, and Using api formatting in Django_DB/common/api_standards for formatting errors and things. 
  Adding tailwind 4
Project now works Identically as a single-page whole graph app running react. 
Decided to use cytoscape for production, adding custom react elements as graph overlays that appear on click and track the graph position. 
11/14
Make DOM node popup
Make node creation
- wired to user
- Questions as prompts? 
  - i.e. Is this a statement or evidence? 
  - Do you have a link for the evidence/ what is your empyrical statement? 
  - Notes? 
Make node page