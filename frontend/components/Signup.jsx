// From Uiverse.io by JkHuger
import { useState } from 'react';
import { registerUser } from '../APInterface/api.js';
import '../styles/components/auth.css';

export function Signup({ onToggleMode, onSignupSuccess }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Frontend validation
    if (!username || !password) {
      setError('Username and password are required');
      return;
    }

    if (password !== passwordConfirm) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);

    // Call API
    const response = await registerUser({
      username,
      email: email || '',
      password,
      password_confirm: passwordConfirm
    });

    setIsLoading(false);

    if (response.error) {
      // Handle error
      if (typeof response.error === 'object') {
        // Format validation errors
        const errorMessages = Object.entries(response.error)
          .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
          .join('; ');
        setError(errorMessages);
      } else {
        setError(response.error);
      }
    } else {
      // Success - save token and notify parent
      localStorage.setItem('authToken', response.data.token);
      if (onSignupSuccess) {
        onSignupSuccess(response.data);
      }
    }
  };

  return (
    <div className="auth-card">
      <a className="auth-title">Sign Up</a>

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
          <span>Username</span>
        </div>

        <div className="auth-inputBox email">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isLoading}
          />
          <span className="user">Email (optional)</span>
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

        <div className="auth-inputBox">
          <input
            type="password"
            required
            value={passwordConfirm}
            onChange={(e) => setPasswordConfirm(e.target.value)}
            disabled={isLoading}
          />
          <span>Password Again</span>
        </div>

        <div className="auth-legal">
          By signing up, you agree to our{' '}
          <a href="/tos" target="_blank">Terms of Service</a>
          {' '}and{' '}
          <a href="/privacy" target="_blank">Privacy Policy</a>
        </div>

        <button
          type="button"
          className="auth-button auth-toggle"
          onClick={onToggleMode}
          disabled={isLoading}
        >
          Log In
        </button>

        <button type="submit" className="auth-button" disabled={isLoading}>
          {isLoading ? 'Creating...' : 'Enter'}
        </button>
      </form>
    </div>
  );
}
