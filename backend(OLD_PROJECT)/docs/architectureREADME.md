# PublicSphere SourceExchange: Architecture Overview

This document provides an architectural overview of the PublicSphere SourceExchange platform.

## System Architecture

PublicSphere SourceExchange is built using a modern web application architecture:

- **Backend**: Django REST Framework for API development
- **Frontend**: React with Tailwind CSS
- **Database**: PostgreSQL

## Component Overview

### Backend Components

The backend follows Django's app-based architecture to maintain modularity and separation of concerns:

1. **Users App**: User authentication, registration, and profile management
   - Models: User, UserConsent
   - Features: JWT authentication, optional 2FA, profile management

2. **Articles App**: Manages article references
   - Models: Article
   - Features: Article CRUD, referrer validation

3. **Sources App**: Manages source areas and versioning
   - Models: SourceArea, SourceAreaVersion
   - Features: Source creation, duplication prevention, metadata parsing

4. **Connections App**: Manages connections between sources and articles
   - Models: Connection
   - Features: Connection CRUD, rating management

5. **Forums App**: Manages forum threads and categories
   - Models: Thread, ForumCategory, ThreadSettings
   - Features: Thread CRUD, category management

6. **Comments App**: Manages user comments and votes
   - Models: Comment, CommentVote
   - Features: Comment CRUD, voting system

7. **Ratings App**: Handles user ratings for sources and connections
   - Models: Rating
   - Features: Rating submission and aggregation

8. **Moderation App**: Handles moderation actions and permissions
   - Models: Moderator, ModerationAction
   - Features: Moderation controls, action logging

9. **Access App**: Manages article access permissions
   - Models: UserArticleAccess
   - Features: Referrer-based access validation

### Utility Components

1. **OpenGraph Metadata Parser**: Extracts bibliographic data from web pages
2. **Source Duplication Prevention**: Detects potential duplicate sources
3. **Referrer Validation**: Verifies access from authorized sources
4. **Rate Limiting**: Prevents abuse of the platform

### Frontend Components

The frontend is organized into feature-based components:

1. **Authentication**: Login, registration, and profile components
2. **Article View**: Article display with source connections
3. **Source Display**: Source information with metadata
4. **Discussion Forums**: Threaded discussion interface
5. **Moderation Tools**: Interface for moderators

## Data Flow

### Source Creation Flow

1. User submits a new source
2. System checks for duplicates using fuzzy matching
3. User confirms if similar sources exist
4. Metadata is parsed from the URL if available
5. Source is stored and forum thread is created automatically

### Article Access Flow

1. User clicks a link from an article to the SourceExchange platform
2. System validates the HTTP referrer header
3. Access is granted for the specific article forum
4. Access is stored in the user's account if logged in

### Forum Discussion Flow

1. User navigates to a specific tab (Sources, General, etc.)
2. System loads threads for the selected category
3. User can view, create, or respond to threads
4. Moderators can perform moderation actions

## Security Architecture

1. **Authentication**: JWT-based authentication with secure token handling
2. **Authorization**: Role-based access control
3. **Data Protection**: 
   - HTTPS for all communications
   - Secure password hashing
   - Content validation and sanitization
   - Protection against common web vulnerabilities

4. **Privacy Protection**:
   - Minimal data collection
   - No tracking cookies or analytics
   - Transparent data usage

## Database Schema

The database schema follows the models defined in the respective apps, with proper relationships between entities:

- One-to-many relationships between users and their content
- Many-to-many relationships between sources and articles via connections
- One-to-many relationships between threads and comments
- Generic foreign keys for ratings and moderation actions

## API Structure

The API follows RESTful principles with resource-based endpoints:

- `/api/users/`: User management endpoints
- `/api/articles/`: Article management endpoints
- `/api/sources/`: Source management endpoints
- `/api/connections/`: Connection management endpoints
- `/api/forums/`: Forum management endpoints
- `/api/comments/`: Comment management endpoints
- `/api/ratings/`: Rating management endpoints
- `/api/moderation/`: Moderation action endpoints
- `/api/access/`: Access management endpoints

API documentation is available at `/api/docs/` using the drf-spectacular library.