import { Link } from 'react-router-dom';
import { NodeDisplay } from '../components/common/NodeDisplay.jsx';
import { ConnectionDisplay } from '../components/common/ConnectionDisplay.jsx';
import { AttributionProvider } from '../utilities/AttributionContext.jsx';
import '../styles/components/modal.css';

/**
 * Home/landing page with component showcases
 */
export function Home() {
  // Example data for NodeDisplay
  const exampleClaim = {
    id: 'example-claim-uuid',
    type: 'claim',
    content: 'Climate change is primarily driven by human activities'
  };

  const exampleSource = {
    id: 'example-source-uuid',
    type: 'source',
    content: 'IPCC Sixth Assessment Report finds that human influence has warmed the atmosphere, ocean and land',
    url: 'https://www.ipcc.ch/report/ar6/wg1/'
  };

  // Example data for ConnectionDisplay
  const exampleConnection = {
    connectionId: 'example-connection-uuid',
    fromNodes: [{
      id: 'source-1-uuid',
      type: 'source',
      content: 'Global surface temperature has increased by approximately 1.1°C since pre-industrial times',
      url: 'https://www.noaa.gov/news'
    }],
    toNode: {
      id: 'claim-1-uuid',
      type: 'claim',
      content: 'Earth is experiencing significant warming'
    },
    logicType: 'AND'
  };

  return (
    <AttributionProvider attributions={{}}>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '4rem 2rem',
        minHeight: '100vh',
        backgroundColor: 'var(--bg-primary)',
        color: 'var(--text-primary)'
      }}>
        {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h1 style={{
          fontSize: '3rem',
          marginBottom: '1rem',
          color: 'var(--text-primary)',
          fontFamily: 'var(--font-family-heading)'
        }}>
          PublicSphere
        </h1>
        <p style={{
          fontSize: '1.2rem',
          marginBottom: '2rem',
          color: 'var(--text-secondary)',
          fontFamily: 'var(--font-family-base)'
        }}>
          Structured collaborative reasoning
        </p>
        <Link
          to="/graph"
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: 'var(--accent-blue)',
            color: 'var(--bg-secondary)',
            textDecoration: 'none',
            borderRadius: '8px',
            fontSize: '1rem',
            fontWeight: 'bold',
            transition: 'all 0.3s ease'
          }}
        >
          Enter Graph
        </Link>
      </div>

      {/* Example Cards */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '3rem',
        maxWidth: '1400px',
        width: '100%'
      }}>
        {/* Node Examples */}
        <section>
          <h2 style={{
            textAlign: 'center',
            marginBottom: '2rem',
            fontSize: '1.5rem',
            textTransform: 'uppercase',
            letterSpacing: '2px',
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-family-ui)'
          }}>
            Nodes
          </h2>
          <div style={{
            display: 'flex',
            gap: '2rem',
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}>
            {/* Claim Card */}
            <div className="modal-card" style={{ width: '450px', minHeight: 'auto', padding: '60px' }}>
              <NodeDisplay
                nodeId={exampleClaim.id}
                nodeType={exampleClaim.type}
                content={exampleClaim.content}
                containerStyle={{
                  border: 'none',
                  padding: '0'
                }}
                contentStyle={{
                  paddingBottom: '60px'
                }}
              />
            </div>

            {/* Source Card */}
            <div className="modal-card" style={{ width: '450px', minHeight: 'auto', padding: '60px' }}>
              <NodeDisplay
                nodeId={exampleSource.id}
                nodeType={exampleSource.type}
                content={exampleSource.content}
                url={exampleSource.url}
                containerStyle={{
                  border: 'none',
                  padding: '0'
                }}
                contentStyle={{
                  paddingBottom: '60px'
                }}
              />
            </div>
          </div>
        </section>

        {/* Connection Example */}
        <section>
          <h2 style={{
            textAlign: 'center',
            marginBottom: '2rem',
            fontSize: '1.5rem',
            textTransform: 'uppercase',
            letterSpacing: '2px',
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-family-ui)'
          }}>
            Connection
          </h2>
          <div style={{
            display: 'flex',
            justifyContent: 'center'
          }}>
            <div className="modal-card" style={{
              width: 'auto',
              minHeight: 'auto',
              padding: '2rem'
            }}>
              <ConnectionDisplay
                connectionId={exampleConnection.connectionId}
                fromNodes={exampleConnection.fromNodes}
                toNode={exampleConnection.toNode}
                logicType={exampleConnection.logicType}
              />
            </div>
          </div>
        </section>
      </div>
    </div>
    </AttributionProvider>
  );
}
