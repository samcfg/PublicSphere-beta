/**
 * React application entry point
 * Mounts the App component with routing
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './utilities/AuthContext.jsx';
import { App } from './components/App.jsx';
import { Home } from './pages/Home.jsx';
import { GraphPage } from './pages/GraphPage.jsx';
import { ContextPage } from './pages/ContextPage.jsx';
import { User } from './pages/User.jsx';
import './styles/main.css';

const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<App />}>
            <Route index element={<Home />} />
            <Route path="graph" element={<GraphPage />} />
            <Route path="context" element={<ContextPage />} />
            <Route path="user" element={<User />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </React.StrictMode>
);
