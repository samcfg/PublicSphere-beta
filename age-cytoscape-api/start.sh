#!/bin/bash

# AGE-Cytoscape API Startup Script

echo "=== AGE-Cytoscape API Startup ==="

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "Error: PostgreSQL is not running on localhost:5432"
    echo "Start PostgreSQL first:"
    echo "  sudo systemctl start postgresql"
    exit 1
fi

# Navigate to script directory
cd "$(dirname "$0")"

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    if command -v pnpm &> /dev/null; then
        pnpm install
    else
        npm install
    fi
fi

echo "Starting AGE-Cytoscape API server..."
echo ""
echo "Server will be available at:"
echo "  API: http://localhost:3001/graph"
echo "  Visualization: http://localhost:3001/index.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
node server.js