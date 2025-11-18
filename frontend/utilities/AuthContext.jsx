import { createContext, useContext, useState, useEffect } from 'react';
import { getToken, getUser, storeAuth, clearAuth, isTokenExpired } from './auth.js';
import { fetchUserProfile, loginUser as apiLogin, logoutUser as apiLogout } from '../APInterface/api.js';

/**
 * AuthContext - Global authentication state for the app
 * Provides user object, token, and auth methods to all components
 */
const AuthContext = createContext(null);

/**
 * AuthProvider - Wraps app to provide auth state
 * Handles initial token validation and maintains reactive state
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(getUser());
  const [token, setToken] = useState(getToken());
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Validate token on mount
  useEffect(() => {
    const validateToken = async () => {
      const storedToken = getToken();

      if (!storedToken || isTokenExpired()) {
        // No token or expired - clear everything
        clearAuth();
        setUser(null);
        setToken(null);
        setIsAuthenticated(false);
        setIsLoading(false);
        return;
      }

      // Token exists and not expired - validate with backend
      const response = await fetchUserProfile(storedToken);

      if (response.error) {
        // Token invalid - clear everything
        clearAuth();
        setUser(null);
        setToken(null);
        setIsAuthenticated(false);
      } else {
        // Token valid
        setIsAuthenticated(true);
      }

      setIsLoading(false);
    };

    validateToken();

    // Listen for expiration events from auth.js
    const handleExpiration = () => {
      setUser(null);
      setToken(null);
      setIsAuthenticated(false);
    };

    window.addEventListener('auth:expired', handleExpiration);
    return () => window.removeEventListener('auth:expired', handleExpiration);
  }, []);

  /**
   * Login - authenticate user and store credentials
   * @param {string} username
   * @param {string} password
   * @returns {Object} Response with error or success
   */
  const login = async (username, password) => {
    const response = await apiLogin({ username, password });

    if (response.error) {
      return response;
    }

    // Success - store auth data
    const { token: newToken, expires_at, user: newUser } = response.data;
    storeAuth(newToken, expires_at, newUser);
    setToken(newToken);
    setUser(newUser);
    setIsAuthenticated(true);

    return response;
  };

  /**
   * Logout - clear credentials and notify backend
   */
  const logout = async () => {
    const currentToken = token;

    // Clear local state first
    clearAuth();
    setUser(null);
    setToken(null);
    setIsAuthenticated(false);

    // Then try backend logout
    if (currentToken) {
      try {
        await apiLogout(currentToken);
      } catch (err) {
        console.warn('Backend logout failed:', err);
      }
    }
  };

  /**
   * Register - create account and auto-login
   * @param {Object} data - {username, email, password, password_confirm}
   * @returns {Object} Response with error or success
   */
  const register = async (data) => {
    const { registerUser } = await import('../APInterface/api.js');
    const response = await registerUser(data);

    if (response.error) {
      return response;
    }

    // Success - store auth data and update state
    const { token: newToken, expires_at, user: newUser } = response.data;
    storeAuth(newToken, expires_at, newUser);
    setToken(newToken);
    setUser(newUser);
    setIsAuthenticated(true);

    return response;
  };

  const value = {
    user,
    token,
    isAuthenticated,
    isLoading,
    login,
    logout,
    register,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * useAuth - Hook to access auth context
 * @returns {Object} {user, token, isAuthenticated, isLoading, login, logout}
 *
 * @example
 * function MyComponent() {
 *   const { user, isAuthenticated, logout } = useAuth();
 *
 *   if (!isAuthenticated) return <Login />;
 *
 *   return <div>Welcome {user.username} <button onClick={logout}>Logout</button></div>
 * }
 */
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }

  return context;
}
