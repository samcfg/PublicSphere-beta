/**
 * React application entry point
 * Mounts the App component to the DOM
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './components/App.jsx';
import './styles/main.css';

// Wait for DOM to be ready
const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
