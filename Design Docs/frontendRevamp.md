# Frontend Structure Revamp

## File System Architecture

```
frontend/
├── pages/
│   └── index.html                    # Minimal React mount point (<div id="root">)
│
├── components/
│   ├── Graph.jsx                     # Cytoscape rendering component (useRef + useEffect)
│   ├── UI.jsx                        # UI controls and interactions
│   ├── Forms.jsx                     # Form components for creating/editing entities
│   └── App.jsx                       # Root component (replaces main.js)
│
├── hooks/
│   └── useGraphData.js               # Custom hook for fetching graph data from DRF
│
├── api/
│   └── api.js                        # DRF endpoint client (pure functions)
│
├── utilities/
│   ├── formatters.js                 # Data transformation (AGE → Cytoscape, pure functions)
│   └── data.js                       # Data processing utilities
│
├── styles/
│   ├── variables.css                 # CSS custom properties (design tokens)
│   └── components/                   # Component-specific styles
│
├── dist/                              # Vite build output (served by Django in production)
│   └── [Generated bundles]
│
├── tailwind.config.js                # Tailwind CSS configuration
├── postcss.config.js                 # PostCSS configuration (Tailwind processor)
│
├── assets/
│   └── [Placeholder for images, fonts, icons]
│
├── package.json                      # Package manager config (includes Vite + React)
├── pnpm-lock.yaml                    # Dependency lock file
├── vite.config.js                    # Vite bundler configuration (with React plugin)
│
└── [DEPRECATED - DELETE]
    ├── modules/                      # Vanilla JS files (replaced by React components)
    │   ├── graph.js
    │   ├── ui.js
    │   └── main.js
    ├── database.js                   # Node.js AGE wrapper (replaced by DRF)
    ├── server.js                     # Express server (replaced by Django)
    ├── node_modules/                 # Generated dependencies (recreate via pnpm install)
    ├── start.sh                      # Node.js startup script (obsolete)
    └── monitor-age.js                # AGE monitoring script (obsolete)
```

## Architecture Principles

### Separation of Concerns
- **pages/**: HTML entry points for different views (minimal React mount point)
- **components/**: React components for UI rendering (Graph, UI controls, Forms, App root)
- **hooks/**: Custom React hooks for data fetching and state management
- **api/**: Backend communication layer (DRF endpoints, pure functions)
- **utilities/**: Pure functions for data transformation (framework-agnostic)
- **styles/**: Visual presentation layer (CSS variables + component styles)
- **dist/**: Vite build output (bundled, tree-shaken, minified assets)
- **assets/**: Static media files

### Build System (Vite + React)
- **Package management**: pnpm downloads dependencies to `node_modules/`
- **Bundling**: Vite resolves `import` statements, JSX transpilation via @vitejs/plugin-react, tree-shakes unused code, minifies output
- **Development**: `pnpm dev` runs Vite dev server with hot module replacement (HMR) and React Fast Refresh
- **Production**: `pnpm build` generates optimized bundles in `dist/` for Django to serve
- **Security**: Self-hosted dependencies (no CDN), lockfile ensures reproducible builds
- **Performance**: Dead code elimination, scope hoisting, content-based hashing for cache invalidation

### Import Flow (React)
```
pages/index.html (<div id="root">)
  ↓ (loads)
components/App.jsx (ReactDOM.createRoot)
  ↓ (renders)
hooks/useGraphData.js (custom hook)
  ↓ (calls)
api/api.js → DRF Backend (/api/graph/*)
  ↓ (fetches data)
utilities/formatters.js (transforms data)
  ↓ (returns to)
components/Graph.jsx (Cytoscape rendering via useRef + useEffect)
```

### Django Integration
- **Development**: Vite dev server proxies API requests to Django backend (hot reload)
- **Production**: `pnpm build` → `dist/`, Django `collectstatic` gathers to `STATIC_ROOT`, Nginx serves
- **Entry point**: `pages/index.html` served at `/` via Django TemplateView

### Migration from Node.js + Vanilla JS to Django + React
1. Restructure filesystem to new architecture (create `components/`, `hooks/` directories)
2. Install Vite bundler with React plugin and configure build pipeline
3. Install React dependencies (`react`, `react-dom`, `@vitejs/plugin-react`)
4. Port `database.js:formatForCytoscape()` to `utilities/formatters.js` (pure function)
5. Rewrite `api/api.js` to target Django REST endpoints (keep as pure functions)
6. Create `hooks/useGraphData.js` custom hook for data fetching
7. Convert `modules/graph.js` → `components/Graph.jsx` (useRef + useEffect for Cytoscape)
8. Convert `modules/ui.js` → `components/UI.jsx` (React components)
9. Convert `modules/main.js` → `components/App.jsx` (root component with ReactDOM.createRoot)
10. Update `pages/index.html` to minimal React mount point (`<div id="root">`)
11. Configure Django `settings.py` to serve `dist/` output
12. Delete obsolete files: `modules/`, `server.js`, `database.js`, `start.sh`, `monitor-age.js`
13. Update `package.json` dependencies (remove Express/pg, add Vite + React + Cytoscape)


## Development Plan

### Step 1: Filesystem Restructure
**Goal:** Reorganize existing files into new React-based folder structure.

1. **Rename root directory:**
   ```bash
   mv age-cytoscape-api/ frontend/
   ```

2. **Create new directory structure:**
   ```bash
   cd frontend/
   mkdir -p pages components hooks api utilities styles/components assets
   ```

3. **Move existing files to temporary locations (will be converted to React):**
   ```bash
   mv index.html pages/
   mv src/api.js api/
   mv src/data.js utilities/
   # Keep src/graph.js, src/ui.js, src/main.js for reference during React conversion
   ```

4. **Keep vendor/ and package files in place** (will be migrated to pnpm dependencies)

5. **Delete obsolete Node.js backend files:**
   ```bash
   rm database.js server.js start.sh monitor-age.js
   rm -rf node_modules/  # Will regenerate with pnpm
   ```

### Step 2: Install Vite, React, and Tailwind CSS
**Goal:** Set up build tooling with React support and Tailwind CSS.

1. **Install Vite, React, and Cytoscape dependencies:**
   ```bash
   cd frontend/
   pnpm add react react-dom
   pnpm add -D vite @vitejs/plugin-react
   pnpm add cytoscape cytoscape-dagre dagre
   ```

2. **Install Tailwind CSS and dependencies:**
   ```bash
   pnpm add -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   ```

3. **Configure `tailwind.config.js`:**
   ```javascript
   export default {
     content: [
       "./pages/**/*.html",
       "./components/**/*.{js,jsx}",
     ],
     theme: {
       extend: {},
     },
     plugins: [],
   }
   ```

4. **Create `styles/main.css` with Tailwind directives:**
   ```css
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```

5. **Create `vite.config.js` with React plugin:**
   ```javascript
   import { defineConfig } from 'vite';
   import react from '@vitejs/plugin-react';

   export defineConfig({
     plugins: [react()],
     root: './',
     build: {
       outDir: 'dist',
       rollupOptions: {
         input: 'pages/index.html'
       }
     },
     server: {
       proxy: {
         '/api': 'http://localhost:8000'  // Proxy DRF requests during dev
       }
     }
   });
   ```

6. **Update `package.json`:**
   ```json
   {
     "name": "publicsphere-frontend",
     "version": "1.0.0",
     "private": true,
     "scripts": {
       "dev": "vite",
       "build": "vite build",
       "preview": "vite preview"
     },
     "dependencies": {
       "react": "^18.2.0",
       "react-dom": "^18.2.0",
       "cytoscape": "^3.28.1",
       "cytoscape-dagre": "^2.5.0",
       "dagre": "^0.8.5"
     },
     "devDependencies": {
       "vite": "^5.0.0",
       "@vitejs/plugin-react": "^4.2.0",
       "tailwindcss": "^3.4.0",
       "postcss": "^8.4.32",
       "autoprefixer": "^10.4.16"
     }
   }
   ```

### Step 3: Create utilities/formatters.js
**Goal:** Port AGE→Cytoscape transformation logic from `database.js`.

1. **Extract `formatForCytoscape()` function** from `database.js:60-110`
2. **Create `utilities/formatters.js`:**
   ```javascript
   export function formatForCytoscape(nodes, edges) {
     // Port logic: strip AGE type suffixes, build Cytoscape JSON
     // Input: raw AGE query results
     // Output: {elements: [{data: {...}}, ...]}
   }
   ```

3. **No external dependencies** - pure data transformation function

### Step 3: Rewrite api/api.js for DRF (Pure Functions)
**Goal:** Replace Express endpoint calls with Django REST API using pure functions.

**Current structure (api.js:1-22):**
```javascript
class GraphAPI {
  constructor(baseURL = 'http://localhost:3001') {
    this.baseURL = baseURL;
  }
  async fetchGraphData() {
    return fetch(`${this.baseURL}/graph`);
  }
}
```

**New structure (pure functions for React compatibility):**
```javascript
const BASE_URL = '/api/graph';

export async function fetchClaims() {
  const response = await fetch(`${BASE_URL}/claims/`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function fetchSources() {
  const response = await fetch(`${BASE_URL}/sources/`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function fetchConnections() {
  const response = await fetch(`${BASE_URL}/connections/`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

// Composite function for loading full graph
export async function fetchGraphData() {
  const [claims, sources, connections] = await Promise.all([
    fetchClaims(),
    fetchSources(),
    fetchConnections()
  ]);
  return { claims, sources, connections };
}
```

### Step 4: Create hooks/useGraphData.js
**Goal:** Custom React hook for fetching graph data from DRF API.

```javascript
import { useState, useEffect } from 'react';
import { fetchGraphData } from '../api/api.js';

export function useGraphData() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchGraphData()
      .then(graphData => {
        setData(graphData);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  }, []);

  return { data, loading, error };
}
```

### Step 5: Convert modules/graph.js → components/Graph.jsx
**Goal:** React component for Cytoscape rendering using useRef + useEffect.

**Key changes:**
- Replace global Cytoscape instance with `useRef` to hold DOM container
- Initialize Cytoscape in `useEffect` hook (runs after component mounts)
- Accept graph data as props, re-render on data changes
- Clean up Cytoscape instance on unmount (return cleanup function from useEffect)

```jsx
import { useRef, useEffect } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';

cytoscape.use(dagre);

export function Graph({ data }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    if (!data || !containerRef.current) return;

    // Initialize Cytoscape instance
    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: data.elements,
      layout: { name: 'dagre' },
      // ... style configuration
    });

    // Cleanup on unmount
    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [data]);

  return <div ref={containerRef} style={{ width: '100%', height: '100vh' }} />;
}
```

### Step 6: Convert modules/ui.js → components/UI.jsx Make this part of a pages file?? 
**Goal:** Convert UI controls to React components.

**Key changes:**
- Replace DOM manipulation with React state management
- Convert event listeners to React event handlers
- Use controlled components for forms

```jsx
export function UI({ onLoadGraph, onResetView }) {
  return (
    <div className="controls">
      <button onClick={onLoadGraph}>Load Graph</button>
      <button onClick={onResetView}>Reset View</button>
    </div>
  );
}
```

### Step 7: Convert modules/main.js → components/App.jsx + main.jsx
**Goal:** Create React root component and entry point.

**components/App.jsx:**
```jsx
import { useGraphData } from '../hooks/useGraphData.js';
import { formatForCytoscape } from '../utilities/formatters.js';
import { Graph } from './Graph.jsx';
import { UI } from './UI.jsx';

export function App() {
  const { data, loading, error } = useGraphData();

  if (loading) return <div>Loading graph...</div>;
  if (error) return <div>Error loading graph: {error.message}</div>;

  const cytoscapeData = formatForCytoscape(data);

  return (
    <div className="app">
      <UI />
      <Graph data={cytoscapeData} />
    </div>
  );
}
```

**components/main.jsx (entry point):**
```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App.jsx';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

### Step 8: Update pages/index.html
**Goal:** Convert to minimal React mount point.

**Current structure:**
```html
<!DOCTYPE html>
<html>
<head>...</head>
<body>
  <!-- Complex HTML structure -->
  <script src="/static/vendor/cytoscape.min.js"></script>
  <script src="src/graph.js"></script>
  <!-- ... multiple script tags -->
</body>
</html>
```

**New structure:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PublicSphere</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/components/main.jsx"></script>
</body>
</html>
```

**Note:** Vite handles all imports, CSS, and bundling from the single entry point.

### Step 9: Configure Django to Serve Frontend (How does Index work?)
**Goal:** Point Django at `frontend/` directory, serve index.html at `/`.

**In `backend/PS_Django_DB/config/settings.py`:**
```python
STATICFILES_DIRS = [
    BASE_DIR.parent.parent / 'frontend',  # Points to /frontend/ root
]
STATIC_URL = '/static/'
```

**In `backend/PS_Django_DB/config/urls.py`:**
```python
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/graph/', include('graph.urls')),
    path('api/users/', include('users.urls')),
    path('api/social/', include('social.urls')),
    path('', TemplateView.as_view(template_name='pages/index.html'), name='home'),
]
```

**Template discovery:**
Django will look for `pages/index.html` in `STATICFILES_DIRS` locations.

### Step 10: Test Integration
**Validation steps:**

1. **Start Vite dev server:**
   ```bash
   cd frontend/
   pnpm dev
   ```
   - Vite serves at `http://localhost:5173`
   - Hot module replacement (HMR) enabled
   - Proxies `/api` requests to Django backend

2. **Start Django dev server (separate terminal):**
   ```bash
   cd backend/PS_Django_DB
   python manage.py runserver
   ```
   - Django serves at `http://localhost:8000`
   - Provides DRF API endpoints

3. **Test API endpoints:**
   ```bash
   curl http://localhost:8000/api/graph/claims/
   curl http://localhost:8000/api/graph/sources/
   curl http://localhost:8000/api/graph/connections/
   ```

4. **Load React app:**
   - Navigate to `http://localhost:5173/`
   - Should render React app, fetch data from DRF via proxy
   - Cytoscape graph renders with existing test data

5. **Browser console checks:**
   - No CORS errors (Vite proxy handles API requests)
   - React DevTools shows component tree
   - Graph renders with existing test data
   - No JSX transpilation errors

6. **Production build test:**
   ```bash
   cd frontend/
   pnpm build
   ```
   - Generates optimized bundles in `dist/`
   - Django `STATICFILES_DIRS` points to `dist/` for production serving

## Success Criteria

- [ ] Frontend directory renamed and restructured with React architecture (`components/`, `hooks/`)
- [ ] Vite bundler with React plugin installed and configured (`vite.config.js`, `@vitejs/plugin-react`)
- [ ] Tailwind CSS installed and configured (`tailwind.config.js`, `postcss.config.js`, `styles/main.css`)
- [ ] React dependencies installed (`react`, `react-dom`)
- [ ] `utilities/formatters.js` ports `database.js` transformation logic (pure function)
- [ ] `api/api.js` successfully calls DRF endpoints as pure functions (no classes)
- [ ] `hooks/useGraphData.js` custom hook fetches data from DRF API
- [ ] `components/Graph.jsx` renders Cytoscape using useRef + useEffect
- [ ] `components/UI.jsx` implements UI controls as React components
- [ ] `components/App.jsx` serves as root component with data flow orchestration
- [ ] `components/main.jsx` entry point uses ReactDOM.createRoot
- [ ] `pages/index.html` is minimal React mount point (`<div id="root">`) with Tailwind CSS imported
- [ ] `pnpm dev` launches Vite dev server with HMR at `http://localhost:5173/`
- [ ] Cytoscape graph renders with existing test data from PostgreSQL+AGE
- [ ] `pnpm build` generates optimized bundles in `dist/` directory
- [ ] Django serves production bundles from `dist/` via `collectstatic`
- [ ] No manual file copying from `node_modules/` (Vite handles all bundling)
- [ ] Browser console shows no errors on page load (dev or production)
- [ ] React DevTools shows component tree correctly
- [ ] Obsolete vanilla JS files deleted (`modules/graph.js`, `modules/ui.js`, `modules/main.js`)
