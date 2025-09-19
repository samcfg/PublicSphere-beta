# PublicSphere SourceExchange: Setup Guide

This document provides instructions for setting up the PublicSphere SourceExchange development environment.

## Prerequisites

- Python 3.9+ 
- PostgreSQL 13+
- Node.js 16+ and npm
- Git

## Initial Setup

### 1. Clone the Repository

```bash
git clone [repository-url]
cd publicsphere-sourcexchange
```

### 2. Set Up the Backend

#### Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Environment Variables

Create a `.env` file in the backend directory:

```
# Django settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database settings
DB_NAME=publicsphere
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# JWT settings
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=86400
```

#### Set Up the Database

```bash
# Create the database
createdb publicsphere

# Run migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser
```

### 3. Set Up the Frontend

```bash
cd frontend
npm install
```

## Running the Development Environment

### Start the Backend

```bash
# From the project root
source venv/bin/activate  # On Windows: venv\Scripts\activate
python manage.py runserver
```

### Start the Frontend

```bash
# From the frontend directory
npm start
```

The application should now be running at:
- Backend API: http://localhost:8000/
- Admin Interface: http://localhost:8000/admin/
- API Documentation: http://localhost:8000/api/docs/
- Frontend: http://localhost:3000/

## Development Workflow

1. Create or update database models in the appropriate app directory
2. Generate migrations: `python manage.py makemigrations`
3. Apply migrations: `python manage.py migrate`
4. Create appropriate serializers, views, and URL configurations
5. Test endpoints using the API documentation interface

## Running Tests

```bash
# Run backend tests
python manage.py test

# Run frontend tests
cd frontend
npm test
```