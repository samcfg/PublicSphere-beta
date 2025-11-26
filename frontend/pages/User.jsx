import { useState } from 'react';
import { useAuth } from '../utilities/AuthContext.jsx';
import { UserReputation } from '../components/user/UserReputation.jsx';
import { UserSettings } from '../components/user/UserSettings.jsx';
import { UserContributions } from '../components/user/UserContributions.jsx';
import { UserData } from '../components/user/UserData.jsx';

/**
 * User profile page with tabbed interface
 * Tabs: Reputation, Settings, Contributions, Data
 * (Home/Workspaces deferred until draft tables implemented)
 */
export function User() {
  const { user, isAuthenticated, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('reputation');

  if (!isAuthenticated) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <h1>Not logged in</h1>
        <p>Please log in to view your profile</p>
      </div>
    );
  }

  const tabs = [
    { id: 'reputation', label: 'Reputation' },
    { id: 'settings', label: 'Settings' },
    { id: 'contributions', label: 'Contributions' },
    { id: 'data', label: 'Data' },
  ];

  return (
    <div className="user-page">
      <header className="user-header">
        <div className="user-header-info">
          <h1>{user?.username}</h1>
          <p className="user-email">{user?.email || 'No email provided'}</p>
        </div>
        <button className="logout-button" onClick={logout}>
          Logout
        </button>
      </header>

      <nav className="user-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`user-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="user-content">
        {activeTab === 'reputation' && <UserReputation />}
        {activeTab === 'settings' && <UserSettings />}
        {activeTab === 'contributions' && <UserContributions />}
        {activeTab === 'data' && <UserData />}
      </div>
    </div>
  );
}
