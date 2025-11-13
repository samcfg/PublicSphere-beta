import { useState, useEffect } from 'react';
import '../styles/components/darkmode.css';

/**
 * Dark/Light mode toggle component
 * Shadow position indicates current mode:
 * - Light mode: shadow at translate3d(8px, -8px, 0) - minimal coverage
 * - Dark mode: shadow at translate3d(36px, -36px, 0) - full coverage
 */
export function DarkModeToggle() {
  const [isDark, setIsDark] = useState(false);

  // Load theme preference on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialDark = savedTheme === 'dark' || (!savedTheme && prefersDark);

    setIsDark(initialDark);
    document.documentElement.setAttribute('data-theme', initialDark ? 'dark' : 'light');
  }, []);

  const toggleTheme = () => {
    const newTheme = !isDark;
    setIsDark(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme ? 'dark' : 'light');
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
  };

  return (
    <div
      className="moon-toggle"
      onClick={toggleTheme}
      role="button"
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && toggleTheme()}
    >
      <div className="moon">
        <div
          className="shadow"
          data-mode={isDark ? 'dark' : 'light'}
        ></div>
      </div>
    </div>
  );
}