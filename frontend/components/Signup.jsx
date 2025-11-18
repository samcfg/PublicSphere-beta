// From Uiverse.io by JkHuger
import { useState } from 'react';
import { useAuth } from '../utilities/AuthContext.jsx';
import { validateUsername, validateEmail, validatePassword, validatePasswordMatch } from '../utilities/validators.js';
import '../styles/components/modal1.css';

export function Signup({ onToggleMode, onSignupSuccess }) {
  const { register } = useAuth();
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
    const usernameValidation = validateUsername(username);
    if (!usernameValidation.valid) {
      setError(usernameValidation.error);
      return;
    }

    const emailValidation = validateEmail(email);
    if (!emailValidation.valid) {
      setError(emailValidation.error);
      return;
    }

    const passwordValidation = validatePassword(password);
    if (!passwordValidation.valid) {
      setError(passwordValidation.error);
      return;
    }

    const passwordMatchValidation = validatePasswordMatch(password, passwordConfirm);
    if (!passwordMatchValidation.valid) {
      setError(passwordMatchValidation.error);
      return;
    }

    setIsLoading(true);

    // Call register from AuthContext
    const response = await register({
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
      // Success - notify parent to close modal
      if (onSignupSuccess) {
        onSignupSuccess();
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
