import { Link } from 'react-router-dom';

/**
 * Home/landing page placeholder
 */
export function Home() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      backgroundColor: 'var(--bg-primary)',
      color: 'var(--text-primary)'
    }}>
      <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>PublicSphere</h1>
      <p style={{ fontSize: '1.2rem', marginBottom: '2rem', color: 'var(--text-secondary)' }}>
        Structured collaborative reasoning
      </p>
      <Link
        to="/graph"
        style={{
          padding: '0.75rem 1.5rem',
          backgroundColor: 'var(--accent-primary)',
          color: 'var(--text-primary)',
          textDecoration: 'none',
          borderRadius: '4px',
          fontSize: '1rem'
        }}
      >
        Enter Graph
      </Link>
    </div>
  );
}
