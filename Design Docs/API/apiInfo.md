The claim/source detail endpoints (**fetchClaimConnections, fetchSourceConnections**) only return connections, not the node data itself (as seen in views.py line 60-61)


**fetchGraphData()** returns the complete graph including all node properties (content, label, etc.). Can filter the full graph response client-side to find the specific node by ID
