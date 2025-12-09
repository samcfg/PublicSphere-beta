import { Link } from 'react-router-dom';
import { NodeDisplay } from '../components/common/NodeDisplay.jsx';
import { ConnectionDisplay } from '../components/common/ConnectionDisplay.jsx';
import { SearchBar } from '../components/common/SearchBar.jsx';
import { AttributionProvider } from '../utilities/AttributionContext.jsx';
import '../styles/components/modal.css';

/**
 * Home/landing page with component showcases
 */
export function Home() {
  // Example data for NodeDisplay - using real nodes from the graph
  const exampleClaim = {
    id: 'ff68b489-3fa0-4d41-84a1-f085b92bf6f7',
    type: 'claim',
    content: 'Digital independent distribution is a viable route for musicians'
  };

  const exampleSource = {
    id: '97e2c5e4-4ac1-4805-abad-d7e7f8a51be5',
    type: 'claim',
    content: 'It maximizes their cut of profit'
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
          A public knowledge map
        </p>
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
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '2rem',
            marginBottom: '2rem'
          }}>
            <h2 style={{
              fontSize: '1.5rem',
              textTransform: 'uppercase',
              letterSpacing: '2px',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-family-ui)',
              margin: 0
            }}>
              Enter a Graph
            </h2>
            <SearchBar />
          </div>
          <div style={{
            display: 'flex',
            gap: '2rem',
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}>
            {/* Claim Card */}
            <Link
              to={`/context?id=${exampleClaim.id}`}
              style={{ textDecoration: 'none', color: 'inherit' }}
            >
              <div className="modal-card" style={{
                width: '450px',
                minHeight: 'auto',
                padding: '60px',
                cursor: 'pointer',
                transition: 'transform 0.2s ease, box-shadow 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.2)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '';
              }}>
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
            </Link>

            {/* Source Card */}
            <Link
              to={`/context?id=${exampleSource.id}`}
              style={{ textDecoration: 'none', color: 'inherit' }}
            >
              <div className="modal-card" style={{
                width: '450px',
                minHeight: 'auto',
                padding: '60px',
                cursor: 'pointer',
                transition: 'transform 0.2s ease, box-shadow 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.2)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '';
              }}>
                <NodeDisplay
                  nodeId={exampleSource.id}
                  nodeType={exampleSource.type}
                  content={exampleSource.content}
                  containerStyle={{
                    border: 'none',
                    padding: '0'
                  }}
                  contentStyle={{
                    paddingBottom: '60px'
                  }}
                />
              </div>
            </Link>
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
