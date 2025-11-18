import { useState } from 'react';
import { useAuth } from '../utilities/AuthContext.jsx';
import '../styles/components/modal1.css';

export function Login({ onToggleMode, onLoginSuccess }) {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    const response = await login(username, password);

    setIsLoading(false);

    if (response.error) {
      // Handle error
      if (typeof response.error === 'object') {
        const errorMessages = Object.entries(response.error)
          .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
          .join('; ');
        setError(errorMessages);
      } else {
        setError(response.error);
      }
    } else {
      // Success - notify parent to close modal
      if (onLoginSuccess) {
        onLoginSuccess();
      }
    }
  };

  return (
    <div className="auth-card">
      <a className="auth-title">Log in</a>

      {error && <div className="auth-error">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="auth-inputBox">
          <input
            type="text"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={isLoading}
          />
          <span className="user">Username</span>
        </div>

        <div className="auth-inputBox">
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoading}
          />
          <span>Password</span>
        </div>

        <button
          type="button"
          className="auth-button auth-toggle"
          onClick={onToggleMode}
          disabled={isLoading}
        >
          Sign Up
        </button>

        <button type="submit" className="auth-button" disabled={isLoading}>
          {isLoading ? 'Logging in...' : 'Enter'}
        </button>
      </form>
    </div>
  );
}
