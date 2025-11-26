/**
 * Cytoscape style configurations
 * Each variant is a function that takes (colors, fontFamily) and returns a Cytoscape style array
 *
 * colors object contains:
 *   - bgPrimary, textPrimary, textSecondary
 *   - accentGreen, accentBlue, accentBlueDark
 *   - nodeDefault, nodeSource, nodeText
 */

export const styleVariants = {
  /**
   * Classic style - current default appearance
   * Rectangle nodes, clean borders, bezier edges
   */
  classic: (colors, fontFamily) => [
    {
      selector: 'node',
      style: {
        'background-color': colors.nodeDefault,
        'label': 'data(content)',
        'color': colors.nodeText,
        'text-valign': 'center',
        'text-halign': 'center',
        'font-family': fontFamily,
        'font-size': '12px',
        'font-weight': 'normal',
        'text-wrap': 'wrap',
        'text-max-width': '200px',
        'width': 'label',
        'height': 'label',
        'min-width': '80px',
        'min-height': '40px',
        'padding': '10px',
        'shape': 'rectangle',
        'border-width': 1,
        'border-color': colors.accentBlue
      }
    },
    {
      selector: 'node[label = "Source"]',
      style: {
        'border-color': colors.accentBlueDark
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 3,
        'line-color': colors.accentGreen,
        'target-arrow-color': colors.accentGreen,
        'target-arrow-shape': 'triangle',
        'arrow-scale': 1.2,
        'curve-style': 'bezier'
      }
    },
    {
      selector: 'edge[logic_type = "NOT"], edge[logic_type = "NAND"]',
      style: {
        'line-color': '#e74c3c',
        'target-arrow-color': '#e74c3c'
      }
    },
    {
      selector: 'edge.highlighted',
      style: {
        'width': 5,
        'line-color': '#ffffff',
        'target-arrow-color': '#ffffff'
      }
    },
    {
      selector: 'node.hovered',
      style: {
        'overlay-color': colors.accentBlue,
        'overlay-opacity': 0.3,
        'overlay-padding': 8,
        'transition-property': 'overlay-opacity, overlay-padding',
        'transition-duration': '0.2s',
        'transition-timing-function': 'ease-out'
      }
    },
    {
      selector: 'node[label = "Source"].hovered',
      style: {
        'overlay-color': colors.accentGreen
      }
    }
  ]
};
