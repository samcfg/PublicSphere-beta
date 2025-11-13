import { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { fetchUserProfile } from '../APInterface/api.js';
import { Navbar } from './Navbar.jsx';
import { Login } from './Login.jsx';
import { Signup } from './Signup.jsx';

/**
 * Root layout component
 * Manages auth state and provides navbar + login modal for all pages
 */
export function App() {
  const location = useLocation();
  const [showLogin, setShowLogin] = useState(false);
  const [isLoginVisible, setIsLoginVisible] = useState(false);
  const [isSignup, setIsSignup] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [authToken, setAuthToken] = useState(null);

  // Determine if we're on the graph page
  const isGraphPage = location.pathname === '/graph';

  // Check authentication on mount
  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (token) {
      fetchUserProfile(token).then(response => {
        if (response.data && !response.error) {
          setAuthToken(token);
          setIsLoggedIn(true);
        } else {
          localStorage.removeItem('authToken');
        }
      });
    }
  }, []);

  const handleUserClick = () => {
    if (!showLogin) {
      setShowLogin(true);
      setTimeout(() => setIsLoginVisible(true), 10);
    } else {
      setIsLoginVisible(false);
      setTimeout(() => setShowLogin(false), 100);
    }
  };

  const handleAuthSuccess = (data) => {
    setAuthToken(data.token);
    setIsLoggedIn(true);
    setIsLoginVisible(false);
    setTimeout(() => {
      setShowLogin(false);
      setIsSignup(false);
    }, 100);
  };

  return (
    <div className={isGraphPage ? 'graph-page' : ''}>
      <Navbar
        onUserClick={handleUserClick}
        isLoggedIn={isLoggedIn}
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

      <Outlet />
    </div>
  );
}
