# API Documentation

## Base URL
```
Development: http://localhost:3000/api
Production: https://your-domain.com/api
```

## Authentication

### JWT Token
Most endpoints require authentication using a JWT token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Getting a Token
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "1",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    }
  }
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Rate Limiting
- **Limit**: 100 requests per minute per IP
- **Headers**: 
  - `X-RateLimit-Limit`: Request limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset time (Unix timestamp)

## API Endpoints

### Users

#### Get All Users
```http
GET /api/users
Authorization: Bearer <token>
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 10)
- `search` (optional): Search term
- `sort` (optional): Sort field (default: createdAt)
- `order` (optional): Sort order (asc/desc, default: desc)

**Response:**
```json
{
  "data": [
    {
      "id": "1",
      "email": "user@example.com",
      "name": "John Doe",
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100,
    "totalPages": 10
  }
}
```

#### Get User by ID
```http
GET /api/users/{id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "1",
  "email": "user@example.com",
  "name": "John Doe",
  "profile": {
    "avatar": "https://example.com/avatar.jpg",
    "bio": "Software developer"
  },
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z"
}
```

#### Create User
```http
POST /api/users
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "newuser@example.com",
  "name": "Jane Doe",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "id": "2",
  "email": "newuser@example.com",
  "name": "Jane Doe",
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z"
}
```

#### Update User
```http
PUT /api/users/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Name",
  "profile": {
    "bio": "Updated bio"
  }
}
```

#### Delete User
```http
DELETE /api/users/{id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "User deleted successfully"
}
```

### Posts

#### Get All Posts
```http
GET /api/posts
```

**Query Parameters:**
- `page`, `limit`, `search`, `sort`, `order` (same as users)
- `author` (optional): Filter by author ID
- `category` (optional): Filter by category
- `published` (optional): Filter by published status (true/false)

**Response:**
```json
{
  "data": [
    {
      "id": "1",
      "title": "Sample Post",
      "content": "Post content...",
      "excerpt": "Post excerpt...",
      "author": {
        "id": "1",
        "name": "John Doe"
      },
      "category": "Technology",
      "published": true,
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 50,
    "totalPages": 5
  }
}
```

#### Create Post
```http
POST /api/posts
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "New Post",
  "content": "Post content...",
  "excerpt": "Post excerpt...",
  "category": "Technology",
  "published": false
}
```

### File Upload

#### Upload File
```http
POST /api/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <file>
```

**Response:**
```json
{
  "url": "https://example.com/uploads/file.jpg",
  "filename": "file.jpg",
  "size": 1024000,
  "mimeType": "image/jpeg"
}
```

## Webhooks

### Available Webhooks
- `user.created` - Triggered when a new user is created
- `user.updated` - Triggered when a user is updated
- `post.published` - Triggered when a post is published

### Webhook Payload
```json
{
  "event": "user.created",
  "data": {
    "id": "1",
    "email": "user@example.com",
    "name": "John Doe"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## SDK Examples

### JavaScript/TypeScript
```typescript
import { ApiClient } from './api-client';

const client = new ApiClient({
  baseUrl: 'https://api.example.com',
  token: 'your-jwt-token'
});

// Get users
const users = await client.users.getAll({
  page: 1,
  limit: 10
});

// Create user
const newUser = await client.users.create({
  email: 'user@example.com',
  name: 'John Doe',
  password: 'password123'
});
```

### cURL Examples
```bash
# Get all users
curl -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     "https://api.example.com/api/users"

# Create user
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","name":"John Doe","password":"password123"}' \
     "https://api.example.com/api/users"
```

## Testing

### Postman Collection
Import the Postman collection from `/docs/postman-collection.json` for easy API testing.

### Test Environment
- **Base URL**: `https://api-test.example.com`
- **Test User**: `test@example.com` / `testpassword`

## Changelog

### v1.2.0 (2024-01-15)
- Added pagination to all list endpoints
- Improved error handling
- Added webhook support

### v1.1.0 (2024-01-01)
- Added user profile endpoints
- Implemented file upload
- Added search functionality

### v1.0.0 (2023-12-01)
- Initial API release
- Basic CRUD operations for users and posts
- JWT authentication
