/**
 * React application entry point
 * Mounts the App component with routing
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { App } from './components/App.jsx';
import { Home } from './pages/Home.jsx';
import { GraphPage } from './pages/GraphPage.jsx';
import './styles/main.css';

const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<Home />} />
          <Route path="graph" element={<GraphPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
