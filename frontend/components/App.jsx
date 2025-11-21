import { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../utilities/AuthContext.jsx';
import { Navbar } from './Navbar.jsx';
import { Login } from './Login.jsx';
import { Signup } from './Signup.jsx';
import { RateLimitModal } from './common/RateLimitModal.jsx';

/**
 * Root layout component
 * Provides navbar + login modal for all pages
 */
export function App() {
  const location = useLocation();
  const { isAuthenticated } = useAuth();
  const [showLogin, setShowLogin] = useState(false);
  const [isLoginVisible, setIsLoginVisible] = useState(false);
  const [isSignup, setIsSignup] = useState(false);
  const [showRateLimitModal, setShowRateLimitModal] = useState(false);

  // Determine if we're on a graph page (full graph or context view)
  const isGraphPage = location.pathname === '/graph' || location.pathname === '/context';

  const handleUserClick = () => {
    if (!showLogin) {
      setShowLogin(true);
      setTimeout(() => setIsLoginVisible(true), 10);
    } else {
      setIsLoginVisible(false);
      setTimeout(() => setShowLogin(false), 100);
    }
  };

  const handleAuthSuccess = () => {
    setIsLoginVisible(false);
    setTimeout(() => {
      setShowLogin(false);
      setIsSignup(false);
    }, 100);
  };

  // Listen for rate limit events from API
  useEffect(() => {
    const handleRateLimit = () => {
      setShowRateLimitModal(true);
    };

    window.addEventListener('api:ratelimit', handleRateLimit);
    return () => window.removeEventListener('api:ratelimit', handleRateLimit);
  }, []);

  return (
    <div className={isGraphPage ? 'graph-page' : ''}>
      <Navbar
        onUserClick={handleUserClick}
        isLoggedIn={isAuthenticated}
      />

      {showLogin && (
        <div style={{
          position: 'fixed',
          top: '50%',
          left: '20px',
          transform: 'translateY(-50%)',
          zIndex: 1001,
          opacity: isLoginVisible ? 1 : 0,
          transition: 'opacity 0.1s ease-in-out'
        }}>
          {isSignup ? (
            <Signup
              onToggleMode={() => setIsSignup(false)}
              onSignupSuccess={handleAuthSuccess}
            />
          ) : (
            <Login
              onToggleMode={() => setIsSignup(true)}
              onLoginSuccess={handleAuthSuccess}
            />
          )}
        </div>
      )}

      {showRateLimitModal && (
        <RateLimitModal onClose={() => setShowRateLimitModal(false)} />
      )}

      <Outlet />
    </div>
  );
}
