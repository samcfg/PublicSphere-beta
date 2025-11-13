// From Uiverse.io by SelfMadeSystem
import '../styles/components/navbar.css';
import { DarkModeToggle } from './darkmode.jsx';

export function Navbar({ onUserClick, isLoggedIn }) {
  return (
    <div className="nav">
      <div className="container">
        <div className="btn">Home</div>
        <div className="btn">Contact</div>
        <div className="btn">About</div>
        <div className="btn" onClick={onUserClick}>
          {isLoggedIn ? 'User' : 'Login'}
        </div>
        <svg
          className="outline"
          overflow="visible"
          width="520"
          height="60"
          viewBox="0 0 520 60"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect
            className="rect"
            pathLength="100"
            x="0"
            y="0"
            width="520"
            height="60"
            fill="transparent"
            strokeWidth="5"
          />
        </svg>
      </div>
      <div className="theme-toggle-container">
        <DarkModeToggle />
      </div>
    </div>
  );
}
