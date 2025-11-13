// From Uiverse.io by JkHuger
import '../styles/components/auth.css';

export function Login({ onToggleMode }) {
  return (
    <div className="auth-card">
      <a className="auth-title">Log in</a>

      <div className="auth-inputBox">
        <input type="text" required />
        <span className="user">Username</span>
      </div>

      <div className="auth-inputBox">
        <input type="password" required />
        <span>Password</span>
      </div>

      <button className="auth-button auth-toggle" onClick={onToggleMode}>
        Sign Up
      </button>

      <button className="auth-button">Enter</button>
    </div>
  );
}
