# NodeCreationModal Refactor - Session Summary

## Problem Solved
Fixed vertical spacing in compound connection mode to prevent NodeBox overlap when boxes expand (e.g., selecting "source" type reveals title/URL fields). Implemented dynamic height measurement using React refs and `getBoundingClientRect()`.

## Work Completed

### Phase 1: Box Separation (Completed)
Refactored monolithic NodeCreationModal into separate boxes with spatial flow:
- **ConnectionBox** - Positioned right of clicked node, shows relationship/logic type selector
- **NodeBox** - Positioned right of ConnectionBox, shows node type and content fields
- Dynamic highlight colors based on selections (green=support/AND/source, red=contradict/NAND, blue=claim)

### Phase 2: Compound Connections (Completed)
Added support for creating multiple nodes with shared compound connection:
- Compound mode toggle in ConnectionBox
- Logic type selector: AND (supports, green) or NAND (contradicts, red)
- Node count controls (+/- buttons, minimum 2)
- Multiple NodeBoxes stack vertically
- Only first NodeBox shows controls (close/submit buttons, error display)
- Backend creates N edges with shared `composite_id`

### Phase 2.5: Dynamic Spacing Fix (Completed)
Implemented height-aware vertical positioning:
- NodeBox converted to `forwardRef` component
- Refs attached to measure actual rendered heights
- `useEffect` hooks trigger recalculation on node type/count changes
- `getNodeBoxOffset()` uses measured heights instead of hardcoded 250px defaults

## Spatial Positioning Architecture

### Key Constants (NodeCreationModal.jsx:81-85)
```javascript
const nodeWidth = node.outerWidth(); // Width of clicked Cytoscape node
const CONNECTION_BOX_OFFSET_X = nodeWidth / 2 + 40; // Right edge + 40px gap
const CONNECTION_BOX_WIDTH = 220; // Fixed width of connection box
const BOX_GAP = 60; // Horizontal gap between connection and node boxes
const NODE_BOX_OFFSET_X = CONNECTION_BOX_OFFSET_X + CONNECTION_BOX_WIDTH + BOX_GAP;
```

### Positioning Functions

#### `getConnectionBoxY()` (NodeCreationModal.jsx:568-572)
```javascript
const getConnectionBoxY = () => {
  if (!isCompound) return -100; // Simple mode: offset above center
  return 0; // Compound mode: center vertically
};
```

#### `getNodeBoxOffset(index, totalNodes)` (NodeCreationModal.jsx:541-565)
Calculates X/Y offset for each NodeBox in compound mode:
```javascript
const getNodeBoxOffset = (index, totalNodes) => {
  if (!isCompound || totalNodes === 1) {
    return { x: NODE_BOX_OFFSET_X, y: -100 }; // Simple mode positioning
  }

  // Use measured heights if available, otherwise defaults
  const heights = boxHeights.length === totalNodes
    ? boxHeights
    : Array(totalNodes).fill(250);

  const GAP = 20; // Vertical gap between stacked boxes

  // Calculate total height including gaps
  const totalHeight = heights.reduce((sum, h) => sum + h, 0) + (GAP * (totalNodes - 1));

  // Calculate Y offset for this box (center distribution)
  let yOffset = -totalHeight / 2; // Start from top
  for (let i = 0; i < index; i++) {
    yOffset += heights[i] + GAP; // Add previous box heights + gaps
  }
  yOffset += heights[index] / 2; // Center current box at its position

  return { x: NODE_BOX_OFFSET_X, y: yOffset };
};
```

### Height Measurement System (NodeCreationModal.jsx:49-71)
```javascript
// Refs to store DOM elements
const nodeBoxRefs = useRef([]);
const [boxHeights, setBoxHeights] = useState([]);
const [needsRecalc, setNeedsRecalc] = useState(0);

// Trigger recalc when nodes change
useEffect(() => {
  setNeedsRecalc(prev => prev + 1);
}, [nodes.length, nodes.map(n => n.type).join(',')]);

// Measure actual DOM heights
useEffect(() => {
  if (!isCompound) return;

  const heights = nodeBoxRefs.current.map(ref => {
    if (!ref) return 250; // Fallback
    const height = ref.getBoundingClientRect().height;
    return height || 250;
  });

  if (heights.length > 0 && JSON.stringify(heights) !== JSON.stringify(boxHeights)) {
    setBoxHeights(heights);
  }
}, [isCompound, needsRecalc]);
```

### Ref Attachment (NodeCreationModal.jsx:631)
```javascript
<NodeBox
  ref={(el) => nodeBoxRefs.current[index] = el}
  // ... other props
/>
```

## Component Files

### Modified Files
- **frontend/components/graph/NodeBox.jsx** - Converted to forwardRef, ref attached to outer div
- **frontend/components/graph/ConnectionBox.jsx** - Simplified relationship choices to supports/contradicts
- **frontend/components/graph/NodeCreationModal.jsx** - Orchestrates both boxes, handles positioning, compound mode logic

### Key State (NodeCreationModal.jsx:26-51)
```javascript
// Mode control
const [isCompound, setIsCompound] = useState(false);
const [nodeCount, setNodeCount] = useState(2);
const [logicType, setLogicType] = useState(null); // 'AND' or 'NAND'

// Simple mode
const [nodeType, setNodeType] = useState(null); // 'claim' or 'source'
const [relationship, setRelationship] = useState(null); // 'supports' or 'contradicts'
const [content, setContent] = useState('');
const [title, setTitle] = useState(''); // Sources only, required
const [url, setUrl] = useState(''); // Sources only, optional

// Compound mode: array of node data
const [nodes, setNodes] = useState([
  { type: null, content: '', title: '', url: '' },
  { type: null, content: '', title: '', url: '' }
]);

const [connectionNotes, setConnectionNotes] = useState('');
const [isSubmitting, setIsSubmitting] = useState(false);
const [error, setError] = useState(null);

// Dynamic spacing
const nodeBoxRefs = useRef([]);
const [boxHeights, setBoxHeights] = useState([]);
const [needsRecalc, setNeedsRecalc] = useState(0);
```

## Rendering Pattern (NodeCreationModal.jsx:574-650)
```javascript
return (
  <>
    {/* Connection Box - right of clicked node */}
    <PositionedOverlay offset={{ x: CONNECTION_BOX_OFFSET_X, y: getConnectionBoxY() }}>
      <ConnectionBox {...} />
    </PositionedOverlay>

    {/* Node Boxes - right of connection box */}
    {!isCompound ? (
      /* Simple: single box */
      <PositionedOverlay offset={{ x: NODE_BOX_OFFSET_X, y: -100 }}>
        <NodeBox {...} />
      </PositionedOverlay>
    ) : (
      /* Compound: multiple boxes stacked vertically */
      nodes.map((nodeData, index) => (
        <PositionedOverlay offset={getNodeBoxOffset(index, nodes.length)}>
          <NodeBox ref={(el) => nodeBoxRefs.current[index] = el} {...} />
        </PositionedOverlay>
      ))
    )}
  </>
);
```

## Phase 3: Triangle Layout & Dynamic Positioning (Completed)

Refactored positioning system from Cytoscape-relative to DOM-relative with triangle layout.

### Architecture Changes

#### Enhanced PositionedOverlay Component
Added **DOM tracking mode** alongside existing Cytoscape mode:

**New Props:**
- `domElement` - React ref to DOM element to track (alternative to `cytoElement`)
- `getOffset` - Dynamic offset calculator function: `(rect) => {x, y}`

**Key Implementation (PositionedOverlay.jsx:81-109):**
```javascript
// DOM MODE: Track DOM element position
if (domElement?.current) {
  const updatePosition = () => {
    const rect = domElement.current.getBoundingClientRect();
    const currentZoom = cy.zoom();

    // Convert rect from screen (zoomed) coordinates to logical coordinates
    const logicalRect = {
      left: rect.left,
      top: rect.top,
      width: rect.width / currentZoom,   // Unscale visual dimensions
      height: rect.height / currentZoom,
      right: rect.right,
      bottom: rect.bottom
    };

    // Calculate offset in logical coordinate space
    const calculatedOffset = getOffset ? getOffset(logicalRect) : offset;

    // Apply offset in logical space, then scale will convert to screen space
    const x = rect.left + calculatedOffset.x * currentZoom;
    const y = rect.top + calculatedOffset.y * currentZoom;

    overlayRef.current.style.left = `${x}px`;
    overlayRef.current.style.top = `${y}px`;
    overlayRef.current.style.transform = `scale(${currentZoom})`;
  };

  // Track: ResizeObserver, cy zoom/pan, window resize/scroll
}
```

**Critical Coordinate Space Handling:**

The system handles two coordinate spaces:

1. **Screen/Visual Coordinates**: What `getBoundingClientRect()` returns
   - Already scaled by Cytoscape zoom
   - Example: At 2x zoom, a 200px logical element has `rect.height = 400px`

2. **Logical Coordinates**: Design/layout space
   - Unscaled dimensions
   - Used for offset calculations to maintain proportional spacing

**Why the conversion is necessary:**
- `rect` dimensions are already zoom-scaled (visual pixels)
- `STANDARD_GAP` is a logical constant (design pixels)
- Without conversion: mixing scaled and unscaled values causes zoom-dependent spacing bugs
- **Solution**: Divide `rect.width/height` by `currentZoom` before passing to `getOffset()`
- Then multiply calculated offset by `currentZoom` when applying position

This ensures spacing scales uniformly with zoom while maintaining design proportions.

### OnClickNode Integration

**Added frameRef to track container (OnClickNode.jsx:33, 211):**
```javascript
const frameRef = useRef(null);

// Attached to frame container
<div ref={frameRef} className="graph-tooltip-container">
```

**Passed to NodeCreationModal (OnClickNode.jsx:408):**
```javascript
<NodeCreationModal frameRef={frameRef} ... />
```

### Triangle Layout Implementation

**Positioning Constants (NodeCreationModal.jsx:82):**
```javascript
const STANDARD_GAP = 24; // Spacing between boxes (reduced 60% from original 60px)
```

**Dynamic Offset Calculations (NodeCreationModal.jsx:537-581):**

```javascript
// ConnectionBox: below-left of OnClickNode frame
const getConnectionBoxOffset = (frameRect) => {
  return {
    x: -STANDARD_GAP,                    // Left of frame
    y: frameRect.height + STANDARD_GAP   // Below frame
  };
};

// NodeBox: below-right of OnClickNode frame
const getNodeBoxOffset = (frameRect, index, totalNodes) => {
  const baseX = frameRect.width + STANDARD_GAP;      // Right of frame
  const baseY = frameRect.height + STANDARD_GAP * 1.5; // Below frame (extra spacing)

  if (!isCompound || totalNodes === 1) {
    return { x: baseX, y: baseY };
  }

  // Compound mode: stack vertically, centered around baseY
  const heights = boxHeights.length === totalNodes
    ? boxHeights
    : Array(totalNodes).fill(250);

  const STACK_GAP = 20; // Vertical gap between stacked boxes

  const totalHeight = heights.reduce((sum, h) => sum + h, 0) + (STACK_GAP * (totalNodes - 1));

  let yOffset = baseY - totalHeight / 2;
  for (let i = 0; i < index; i++) {
    yOffset += heights[i] + STACK_GAP;
  }
  yOffset += heights[index] / 2;

  return { x: baseX, y: yOffset };
};
```

**Triangle Geometry:**
```
       [OnClickNode Frame]
              ↙         ↘
   [ConnectionBox]    [NodeBox]
   x: -24            x: width + 24
   y: height + 24    y: height + 36
```

**Positioning Pattern (NodeCreationModal.jsx:586-660):**
```javascript
// ConnectionBox
<PositionedOverlay
  domElement={frameRef}
  cy={cy}
  getOffset={getConnectionBoxOffset}
>
  <ConnectionBox ... />
</PositionedOverlay>

// NodeBox(es)
<PositionedOverlay
  domElement={frameRef}
  cy={cy}
  getOffset={(frameRect) => getNodeBoxOffset(frameRect, index, nodes.length)}
>
  <NodeBox ... />
</PositionedOverlay>
```

### Key Parameters Summary

**Spacing Constants:**
- `STANDARD_GAP = 24px` - Primary spacing unit (horizontal/vertical gaps)
- `STANDARD_GAP * 1.5 = 36px` - NodeBox vertical offset (slight extra spacing for visual balance)
- `STACK_GAP = 20px` - Vertical spacing between multiple NodeBoxes in compound mode

**Coordinate Space Conversions:**
- Visual to Logical: `rect.dimension / currentZoom`
- Logical to Visual: `logicalOffset * currentZoom`

**All spacing now:**
- Scales proportionally with zoom
- Based on actual OnClickNode frame dimensions (no hardcoded values)
- Maintains triangle geometry at all zoom levels

## Phase 4: SVG Connection Lines (Planning)

### Requirements
Create visual connectors showing the flow:
- OnClickNode → ConnectionBox
- ConnectionBox → NodeBox
- In compound mode: ConnectionBox → multiple NodeBoxes

### Design 

**1. SVG Container Strategy**

Where should the SVG element live in the DOM?

**Option A: Separate PositionedOverlay per line**
```javascript
<PositionedOverlay domElement={frameRef} cy={cy} getOffset={...}>
  <svg>
    <line x1={startX} y1={startY} x2={endX} y2={endY} />
  </svg>
</PositionedOverlay>
```
- Pro: Reuses positioning system
- Con: Need to calculate both endpoints in offset space

**Option B: Single full-viewport SVG**
```javascript
<svg style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', pointerEvents: 'none', zIndex: 999 }}>
  <line x1={absoluteX1} y1={absoluteY1} x2={absoluteX2} y2={absoluteY2} />
</svg>
```
- Pro: Simple absolute coordinates
- Con: Need to track all box positions globally
- Con: Doesn't scale with Cytoscape zoom (or needs manual zoom handling)

**Option C: SVG within NodeCreationModal, positioned via PositionedOverlay**
```javascript
// In NodeCreationModal
<PositionedOverlay domElement={frameRef} cy={cy} getOffset={() => ({x: 0, y: 0})}>
  <svg width={calculatedWidth} height={calculatedHeight}>
    {/* Lines relative to OnClickNode origin */}
  </svg>
</PositionedOverlay>
```
- Pro: Groups all creation UI together
- Pro: Inherits zoom scaling automatically
- Con: Need to calculate bounding box for entire triangle

**2. Line Style**

- Start testing with straight lines
- Stroke width proportional to ctoscape?
- Color matching (inherit from ConnectionBox/NodeBox accent colors), have a "glint" effect
- Arrow markers at endpoint at nodebox, not connectionbox. 

**3. Dynamic Updates**

Lines need to update when:
- OnClickNode frame resizes (content height changes)
- Compound mode toggled (number of NodeBoxes changes)
- NodeBox type changes (height changes)
- Cytoscape zoom/pan
- React components that re-render on state changes

**4. Coordinate Calculations**

Given the triangle layout, line endpoints need to connect:
- **OnClickNode → ConnectionBox**: From frame bottom-left edge to ConnectionBox top-center
- **ConnectionBox → NodeBox**: From ConnectionBox right edge to NodeBox left edge
- **Compound mode**: Single ConnectionBox to N NodeBoxes (fan-out pattern)

Need to determine:
- Anchor points on each box (center? edge? corner?)
- How to calculate these in logical coordinate space
- Whether PositionedOverlay can expose element positions to siblings

**5. Reusability**

A generic `ConnectorLine` component that can be reused in @ConnectionDisplay

### Proposed Architecture (Initial Recommendation)

**Option C with coordinate helper:**

1. **Create `useElementPosition` hook** to expose PositionedOverlay-tracked positions
2. **Render SVG in NodeCreationModal** using PositionedOverlay
3. **Calculate line endpoints** from known offsets and box dimensions
4. **Use logical coordinate space** for calculations, let zoom scaling happen automatically

```javascript
// Pseudocode
const svgOffset = (frameRect) => ({ x: -STANDARD_GAP, y: 0 });
const svgWidth = frameRect.width + STANDARD_GAP * 3 + 220; // Span entire triangle
const svgHeight = frameRect.height + STANDARD_GAP * 2 + 400; // Max vertical extent

<PositionedOverlay domElement={frameRef} cy={cy} getOffset={svgOffset}>
  <svg width={svgWidth} height={svgHeight} style={{ pointerEvents: 'none', zIndex: 998 }}>
    <line
      x1={frameBottomLeftX}
      y1={frameBottomLeftY}
      x2={connectionBoxTopCenterX}
      y2={connectionBoxTopCenterY}
      stroke="var(--accent-blue)"
      strokeWidth={2}
    />
    {/* More lines... */}
  </svg>
</PositionedOverlay>
```

## Notes for Next Agent

### Spatial Positioning Summary
All positioning is **relative to the clicked Cytoscape node**:
- ConnectionBox: `nodeWidth/2 + 40px` to the right, centered (compound) or -100px offset (simple)
- NodeBox: `ConnectionBox.right + 60px gap` to the right, centered (compound) or -100px offset (simple)
- Compound vertical spacing: Boxes distributed around center point (y=0), using measured heights + 20px gaps

### Important Constants to Preserve
- `CONNECTION_BOX_WIDTH = 220` - Affects NodeBox X position
- `BOX_GAP = 60` - Horizontal spacing between boxes
- `GAP = 20` (in getNodeBoxOffset) - Vertical spacing between stacked boxes
- Default fallback height: `250px` when measurement unavailable

### Dynamic Height Flow
1. User action (type change, node count) → `needsRecalc` increment
2. useEffect measures DOM heights → updates `boxHeights` state
3. Re-render with new `getNodeBoxOffset()` calculations → accurate positioning

### Color Semantics
- Green (`var(--accent-green)`): supports, AND logic, source nodes
- Red (`var(--accent-red)`): contradicts, NAND logic
- Blue (`var(--accent-blue)`): claim nodes, neutral default

### Backend Integration
- Simple mode: `createConnection({ from_node_id, to_node_id, logic_type?, notes })`
  - `logic_type: 'NOT'` for contradicts, omit/null for supports
- Compound mode: `createConnection({ source_node_ids: [...], target_node_id, logic_type, notes })`
  - Returns `composite_id` shared by all edges
  - Only claims allowed in compound (validated)
